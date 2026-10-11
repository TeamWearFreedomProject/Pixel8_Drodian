#!/usr/bin/env python3
"""U30: isolated proof that Google's Pixel kernel alias can select source GKI.

Never modify upstream or physical Pixel 8. The CI-only alias experiment
changes a single Google Bazel alias selection for 4KiB-page kernels and
records the configured dependency path. It does NOT establish full KMI/ABI.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

COMMON_PIN="397babd94c06783d8430c838475955f0b6ff63c2"
GKI_PIN="bd23337e42e794964a89f47596daf1209a25ee1a"
SOURCE="//aosp:kernel_aarch64"
OLD=":kernel_aarch64_download_or_build"

def fail(reason):
    raise SystemExit("U30 SOURCE ALIAS FAIL CLOSED: "+reason)

def git_head(root):
    return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()

def hash_bytes(t):
    return hashlib.sha256(t.encode()).hexdigest()

def patch(src,out):
    common=src/"private/devices/google/common"
    if git_head(common)!=COMMON_PIN or git_head(src/"aosp")!=GKI_PIN:
        fail("wrong official Google project revision")
    file=common/"kleaf/common.BUILD.bazel"
    text=file.read_text()
    matches=list(re.finditer(
        r'(?ms)\balias\s*\(\s*name\s*=\s*"kernel_aarch64"\s*,.*?^\)',
        text
    ))
    if len(matches)!=1:fail("expected a unique Google common kernel_aarch64 alias")
    m=matches[0]
    oldblock=m.group(0)
    if oldblock.count(OLD)!=1 or oldblock.count(":kernel_aarch64_16k_download_or_build")!=1:
        fail("Google alias no longer has exactly the two expected page-size branches")
    if "kernel_aarch64_download_or_build" not in text:
        fail("legacy downloaded GKI alias unexpectedly absent")
    replacement=oldblock.replace(OLD,'"'+SOURCE+'"',1) if False else oldblock.replace(
       '"'+OLD+'"','"'+SOURCE+'"',1
    )
    if replacement==oldblock:fail("4KiB-page alias replacement had no effect")
    new_text=text[:m.start()]+replacement+text[m.end():]
    if text.count(SOURCE)>0:fail("source alias already present; investigate before rewrite")
    file.write_text(new_text)
    diff=subprocess.run(
       ["git","-C",str(common),"diff","--","kleaf/common.BUILD.bazel"],
       capture_output=True,text=True,check=True
    ).stdout
    if "-"+'    "//conditions:default": "'+OLD+'"' not in diff and (
         not re.search(r'(?m)^-.*"//conditions:default": "'+re.escape(OLD)+r'"',diff)
    ):
        fail("old alias not visible in source diff")
    if not re.search(r'(?m)^\+.*"//conditions:default": "'+re.escape(SOURCE)+r'"',diff):
        fail("source GKI alias not visible in source diff")
    out.mkdir(parents=True,exist_ok=True)
    (out/"U30_RESEARCH_ONLY_COMMON_GKI_ALIAS_DIFF.txt").write_text(diff)
    result={
        "status":"U30_EXPERIMENTAL_4K_SOURCE_ALIAS_PATCHED_IN_CI_ONLY",
        "official_google_common_commit":COMMON_PIN,
        "official_r9_gki_source_commit":GKI_PIN,
        "original_google_alias_SHA256":hash_bytes(text),
        "modified_google_alias_SHA256":hash_bytes(new_text),
        "old_4k_alias":OLD,
        "new_4k_alias":SOURCE,
        "16k_page_kernel_alias_NOT_CHANGED":True,
        "other_images_headers_gki_artifacts_aliases_NOT_CHANGED":True,
        "target_build_dist_NOT_RUN":True,
        "KMI_safety_verified":False,
        "Pixel8_real_device_ever_written":False,
        "real_device_flash_gate":"DENY"
    }
    (out/"U30_SOURCE_ALIAS_PATCH.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

def verify(out):
    report=json.loads((out/"U30_SOURCE_ALIAS_PATCH.json").read_text())
    if report.get("real_device_flash_gate")!="DENY" or report.get("new_4k_alias")!=SOURCE:
        fail("unsafe alias metadata")
    p=out/"U30_SOURCE_ALIAS_PATH_QUERY.txt"
    if not p.is_file():fail("Bazel source dependency probe did not produce a log")
    trace=p.read_text(errors="replace")
    success=(out/"U30_SOURCE_ALIAS_PATH_EXIT.txt").read_text().strip()=="0"
    if not success:fail("Bazel source dependency cquery failed")
    required=(
       "_kernel_build rule //private/devices/google/shusky:kernel",
       "_kernel_build rule //aosp:kernel_aarch64",
    )
    for s in required:
        if s not in trace:fail("configured Bazel source path does not contain "+s)
    if "kernel_filegroup rule //aosp:kernel_aarch64_download_or_build" in trace:
        fail("still using downloaded GKI filegroup in selected kernel source path")
    output={
        "status":"U30_GOOGLE_SOURCE_GKI_ALIAS_PATH_CONFIRMED_RESEARCH_ONLY",
        "verified_current_config_source_dependency_path":True,
        "selected_base_kernel":SOURCE,
        "actual_shusky_6_1_157_full_build_performed":False,
        "other_image_and_headers_references_aligned":False,
        "shiba_stock_CP2A_vendor_KMI_CRC_verified":False,
        "boot_and_rollback_safety_verified":False,
        "phone_flashing_approved":False,
        "real_device_flash_gate":"DENY"
    }
    (out/"U30_SOURCE_ALIAS_PATH_RESULT.json").write_text(json.dumps(output,indent=2)+"\n")
    md=[
        "# U30—CI-only direct source GKI dependency experiment",
        "",
        "**PASS: Shusky kernel now points to r9 GKI 6.1.157 SOURCE TARGET**",
        "",
        "- Previously: shusky -> //common:kernel_aarch64 ->",
        "  //aosp:kernel_aarch64_download_or_build (kernel_filegroup, prebuilt).",
        "- Experimental 4KiB alias: shusky -> //common:kernel_aarch64 ->",
        "  //aosp:kernel_aarch64 (_kernel_build, source).",
        "- Change restricted to disposable CI checkout of Google's common Bazel alias.",
        "- 16KiB case and separate image/artifact/header aliases remain UNCHANGED.",
        "- No actual new shusky kernel was built by this source-path experiment.",
        "- Real 6.1.157 kernel+module KMI/CRC, complete image consistency, shiba board",
        "  compatibility, and AVB/rollback recovery remain UNVERIFIED.",
        "",
        "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (out/"U30_SOURCE_ALIAS_PATH_RESULT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="task",required=True)
    a=sub.add_parser("patch");a.add_argument("--src",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    b=sub.add_parser("verify");b.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.task=="patch":patch(args.src,args.out)
    else:verify(args.out)
if __name__=="__main__":
    main()
