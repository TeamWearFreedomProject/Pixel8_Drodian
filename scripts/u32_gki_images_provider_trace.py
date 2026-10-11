#!/usr/bin/env python3
"""U32: isolated CI-only proof of the legacy 6.1.124 GKI image provider.

U30 redirected only //common:kernel_aarch64 to pinned 6.1.157 source.
Google's pinned common BUILD obtains kernel_gki_modules from
//common:kernel_aarch64_images, a DIFFERENT Bazel alias. Trace both paths
and test whether redirecting only that 4KiB images alias to source
//aosp:kernel_aarch64_images yields a real source GKI dependency graph.

NO kernel build, NO firmware, NO module removal, NO disabling warnings,
NO real device or user computer access. A graph success is NOT a compatible
system_dlkm payload until a later full build checks the actual .ko files.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

GOOGLE_COMMON_SHA = "397babd94c06783d8430c838475955f0b6ff63c2"
GKI_SHA = "bd23337e42e794964a89f47596daf1209a25ee1a"
MODULE_PROVIDER="//private/devices/google/common:kernel_gki_modules"
OLD="//aosp:kernel_aarch64_images_download_or_build"
SOURCE_IMAGES="//aosp:kernel_aarch64_images"
SOURCE_KERNEL="//aosp:kernel_aarch64"

def fail(reason):
    raise SystemExit("U32 SOURCE IMAGES GRAPH FAIL CLOSED: "+reason)

def git_head(path):
    return subprocess.check_output(
        ["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def dump(out,name,data):
    (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")

def patch(src,out):
    if git_head(src/"private/devices/google/common")!=GOOGLE_COMMON_SHA:
        fail("Google common revision changed")
    if git_head(src/"aosp")!=GKI_SHA:
        fail("GKI source revision changed")
    rule=src/"private/devices/google/common/kleaf/common.BUILD.bazel"
    file=src/"private/devices/google/common/BUILD.bazel"
    body=rule.read_text()
    modules=file.read_text()
    if ('name = "kernel_gki_modules"' not in modules or
        'images = "//common:kernel_aarch64_images"' not in modules):
        fail("Google common module extraction source anchor changed")
    matches=list(re.finditer(
        r'(?ms)\balias\s*\(\s*name\s*=\s*"kernel_aarch64_images"\s*,.*?^\)',
        body
    ))
    if len(matches)!=1:
        fail("kernel_aarch64_images alias not uniquely found")
    m=matches[0]
    block=m.group(0)
    old='":kernel_aarch64_images_download_or_build"'
    image16='":kernel_aarch64_16k_images_download_or_build"'
    if block.count(old)!=1 or block.count(image16)!=1:
        fail("old Google image alias page-size branches unexpected")
    rewritten=block.replace(old,'"'+SOURCE_IMAGES+'"',1)
    result=body[:m.start()]+rewritten+body[m.end():]
    if result==body:
        fail("experimental images alias edit did not change source")
    rule.write_text(result)
    diff=subprocess.run(
       ["git","-C",str(src/"private/devices/google/common"),
        "diff","--","kleaf/common.BUILD.bazel"],
       capture_output=True,text=True,check=True
    ).stdout
    # Existing U30 changed the other kernel_aarch64 alias in the SAME file.
    # Verify the specific images change rather than assuming diff only one line.
    if not re.search(
       r'(?m)^-[ \t]*"//conditions:default":[ \t]*'
       r'":kernel_aarch64_images_download_or_build"',diff
    ) or not re.search(
       r'(?m)^\+[ \t]*"//conditions:default":[ \t]*'
       r'"//aosp:kernel_aarch64_images"',diff
    ):
        fail("actual images source alias change absent from Git diff")
    if not ('":kernel_aarch64_16k_images_download_or_build"' in result
            and '"//aosp:kernel_aarch64"' in result):
        fail("16KiB alias or earlier U30 GKI kernel fix unexpectedly modified")
    out.mkdir(parents=True,exist_ok=True)
    (out/"U32_CI_ONLY_GKI_IMAGES_SOURCE_ALIAS_DIFF.txt").write_text(diff)
    evidence={
      "status":"U32_RESEARCH_SOURCE_IMAGES_ALIAS_APPLIED_IN_EPHEMERAL_CI_ONLY",
      "Google_common_git_SHA":GOOGLE_COMMON_SHA,
      "GKI_git_SHA":GKI_SHA,
      "original_common_BUILD_sha256":sha(body),
      "experimental_common_BUILD_sha256":sha(result),
      "old_4k_images_provider":":kernel_aarch64_images_download_or_build",
      "new_4k_images_provider":SOURCE_IMAGES,
      "16KiB_page_alias_unchanged":True,
      "old_GKI_6_1_124_still_present_in_previous_U32_full_dist":True,
      "actual_fixed_6_1_157_GKI_modules_built":False,
      "real_CP2A_stock_ABI_compatible":False,
      "real_device_flash_gate":"DENY"
    }
    dump(out,"U32_IMAGES_ALIAS_EXPERIMENT.json",evidence)
    print(json.dumps(evidence,indent=2))

def verify(out):
    expected=[
       ("PRE_OLD_IMAGES","_kernel_build"), # pre-graph may not contain source
       ("POST_OLD_IMAGES",""),
       ("POST_SOURCE_IMAGES",""),
       ("POST_SOURCE_KERNEL","")
    ]
    queries={}
    for name,_ in expected:
        log=out/("U32_"+name+"_CQUERY.txt")
        status=out/("U32_"+name+"_EXIT.txt")
        if not log.is_file() or not status.is_file():
            fail("missing exact Bazel query evidence for "+name)
        txt=log.read_text(errors="replace")
        rc=int(status.read_text().strip())
        queries[name]={
          "exit":rc,
          "sha256":sha(txt),
          "path":[line.strip() for line in txt.splitlines() if (
              " rule //" in line or "INFO: Empty query results" in line
          )][:90],
        }
    a=queries["PRE_OLD_IMAGES"]
    b=queries["POST_OLD_IMAGES"]
    c=queries["POST_SOURCE_IMAGES"]
    d=queries["POST_SOURCE_KERNEL"]
    pre_old=OLD in "\n".join(a["path"])
    post_old=OLD in "\n".join(b["path"])
    post_source=SOURCE_IMAGES in "\n".join(c["path"])
    post_kernel=("_kernel_build rule "+SOURCE_KERNEL) in "\n".join(d["path"])
    all_rc_zero=all(t["exit"]==0 for t in queries.values())
    good=all_rc_zero and pre_old and not post_old and post_source and post_kernel
    report={
      "phase":"U32_IMAGES_PROVIDER_FORENSICS",
      "status":"SOURCE_IMAGES_GRAPH_CONFIRMED_RESEARCH_ONLY" if good
             else "SOURCE_IMAGES_GRAPH_UNRESOLVED_OR_FAILED",
      "pre_patch_old_downloaded_images_provider_reachable":pre_old,
      "post_patch_old_downloaded_images_provider_reachable":post_old,
      "post_patch_source_images_provider_reachable":post_source,
      "post_patch_kernel_6_1_157_source_build_reachable":post_kernel,
      "all_Bazel_queries_succeeded":all_rc_zero,
      "configured_Bazel_query_evidence":queries,
      "actual_new_GKI_system_dlkm_built":False,
      "actual_new_module_vermagic_audited":False,
      "U32_prior_58_old_modules_resolution_verified":False,
      "phone_safe_to_flash":False,
      "real_device_flash_gate":"DENY"
    }
    dump(out,"U32_IMAGES_PROVIDER_TRACE.json",report)
    summary=[
      "# U32 — old 6.1.124 GKI system_dlkm image alias investigation",
      "",
      "- Pre-patch old image provider reachable: "+str(pre_old),
      "- After 4KiB images alias patch old image provider reachable: "+str(post_old),
      "- New source images provider reachable: "+str(post_source),
      "- New source kernel provider reachable: "+str(post_kernel),
      "- Queries all exit 0: "+str(all_rc_zero),
      "- Research-only dependency graph hypothesis confirmed: "+str(good),
      "",
      "A Bazel dependency graph is NOT a real new system_dlkm module build.",
      "Old 58 actual U32 modules remain unresolved until a FULL rebuild",
      "and complete SHA256 / .ko vermagic audit under these new aliases.",
      "Stock CP2A module CRC, DTBO, AVB/rollback and recovery unverified.",
      "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (out/"U32_IMAGES_PROVIDER_TRACE.md").write_text("\n".join(summary)+"\n")
    print("\n".join(summary))
    if not good:
        fail("downloaded images still selected or source-images dependency missing")

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("patch")
    a.add_argument("--src",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    b=sub.add_parser("verify")
    b.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="patch":
        patch(args.src,args.out)
    else:
        verify(args.out)

if __name__=="__main__":
    main()
