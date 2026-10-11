#!/usr/bin/env python3
"""U30: prove which kernel the Bazel provider REALLY selected.

Source-only CI tracing. No hardware actions, boot images, deployment artifacts
or fallback to an older prebuilt. A successful previous build is not a proof
of production CP2A 6.1.157 compatibility.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CP2A_GKI = "bd23337e42e794964a89f47596daf1209a25ee1a"
STOCK_RELEASE = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
OLD_RELEASE = "6.1.124-android14-11-g8d713f9e8e7b-ab13202960"
PROVIDER_TARGET = "//aosp:kernel_aarch64_download_or_build"

def check(cond, reason):
    if not cond:
        raise SystemExit("U30 PROVIDER TRACE FAIL CLOSED: "+reason)

def git_head(p):
    return subprocess.check_output(
        ["git","-C",str(p),"rev-parse","HEAD"],text=True).strip()

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_rc(p):
    try:
        return int(p.read_text().strip())
    except Exception as e:
        raise SystemExit("U30 missing/invalid Bazel query exit: "+str(p)+": "+str(e))

def main():
    p=argparse.ArgumentParser()
    for field in ("source","u28","logs","out"):
        p.add_argument("--"+field,type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    gki=a.source/"aosp"
    check(git_head(gki)==CP2A_GKI,"r9 GKI source SHA has changed")
    make=(gki/"Makefile").read_text()
    ver=[]
    for name in ("VERSION","PATCHLEVEL","SUBLEVEL"):
        m=re.search(r"(?m)^"+name+r"\s*=\s*(\d+)\s*$",make)
        check(m is not None,"Makefile "+name+" missing")
        ver.append(int(m.group(1)))
    check(ver==[6,1,157],"GKI worktree is not Linux 6.1.157")
    u28=json.loads(a.u28.read_text())
    check(u28["status"]=="U28_RESEARCH_COMPILE_PASS_NOT_CP2A_FIRMWARE",
          "U28 was not a true compiler PASS")
    check(u28["real_bazel_exit_code"]==0,"U28 Bazel exit was nonzero")
    check(u28["actual_built_kernel_release"]==OLD_RELEASE,
          "U28 actual Image banner is not the reported OLD 6.1.124")
    check(u28["compiler_diagnostics"]["KMI_6_1_124_provider_mismatch"] is True,
          "U28 mismatch was not independently recorded")
    check(u28["real_device_flash_gate"]=="DENY","U28 flash gate changed")
    device=a.source/"private/devices/google/common/device.bazelrc"
    d=device.read_text()
    check("gki_prebuilts=13202960" in d,"expected legacy prebuilt build ID missing")
    for flag in ("build --use_prebuilt_gki=true",
                 "build:use_source_tree_aosp --use_prebuilt_gki=false",
                 "build:use_source_tree_aosp --kernel_package=@//aosp"):
        check(flag in d,"official Bazelrc changed: "+flag)
    build_file=a.source/"private/devices/google/shusky/BUILD.bazel"
    check(build_file.is_file(),"shusky kernel Bazel rules missing")
    bazel_starlark=build_file.read_text()
    selection= {
        "source_gki_git_HEAD":git_head(gki),
        "source_makefile_kernel": ".".join(map(str,ver)),
        "legacy_prebuilt_GKI_build_number": "13202960",
        "shusky_Build_bazel_sha256":digest(build_file),
        "google_device_bazelrc_sha256":digest(device),
        "shusky_rule_mentions_kernel_aarch64": "kernel_aarch64" in bazel_starlark,
        "shusky_rule_mentions_base_kernel": "base_kernel" in bazel_starlark,
    }
    for name in ("provider","source","source-rule","shusky-kernel","link-path"):
        path=a.logs/("U30_"+name+"_CQUERY.txt")
        check(path.is_file() and path.stat().st_size>0,
              "missing actual Bazel cquery trace: "+name)
        selection[name+"_cquery_exit"]=read_rc(a.logs/("U30_"+name+"_EXIT.txt"))
        selection[name+"_trace_sha256"]=digest(path)
        t=path.read_text(errors="replace")
        selection[name+"_mentions_old_build_id"]="13202960" in t
        selection[name+"_mentions_old_release"]="6.1.124-android14-11" in t
        selection[name+"_mentions_current_source"]="kernel_aarch64" in t
        selection[name+"_trace_error_lines"]=[
           x[-400:] for x in t.splitlines()
           if re.search(r"(?i)(?:error:|failed to|invalid setting|not found)",x)
        ][:15]
    check(selection["provider_cquery_exit"]==0,
          "provider target did not successfully resolve")
    check(selection["source_cquery_exit"]==0,
          "source GKI target did not successfully resolve")
    check(selection["shusky-kernel_cquery_exit"]==0,
          "shusky device kernel target did not successfully resolve")
    prebuilt_in_device=bool(re.search(
        r"(?m)^\s*build\s+--use_prebuilt_gki=true\s*$",d
    ))
    report={
        "phase":"U30",
        "status":"U30_BAZEL_PROVIDER_TRACE_COMPLETE_KMI_MISMATCH_STILL_BLOCKS_HARDWARE",
        "existing_pixel8_stock_kernel":STOCK_RELEASE,
        "verified_source_git_commit":CP2A_GKI,
        "source_worktree_kernel":"6.1.157",
        "U28_REAL_BAZEL_BUILD_EXIT":0,
        "U28_GENERATED_IMAGE_RELEASE_ACTUAL":OLD_RELEASE,
        "U28_REAL_IMAGE_IS_STOCK_CP2A":False,
        "official_Bazelrc_defaults_old_prebuilt":prebuilt_in_device,
        "reported_6_1_124_vs_6_1_157_KMI_incompatibility":True,
        "bazel_configured_provider_resolution_trace":selection,
        "GKI_target_KMI_CRC_verified":False,
        "CP2A_vendor_driver_binary_equivalence_verified":False,
        "real_shiba_Pixel8_booted":False,
        "real_device_flash_gate":"DENY",
    }
    (a.out/"U30_BAZEL_PROVIDER_TRACE.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    )
    md=[
        "# U30 — why U28 green BUILD still selects old GKI",
        "",
        "**U30 READ-ONLY BAZEL PROVIDER TRACE COMPLETE; DEVICE FLASH GATE DENY.**",
        "",
        "- Current working Pixel 8 shiba CP2A GKI: "+STOCK_RELEASE,
        "- Actual U28 generated Image: "+OLD_RELEASE,
        "- Official r9 GKI source Git SHA: "+CP2A_GKI,
        "- The previous shusky Bazel build passed 439/439 but its emitted Image",
        "  belongs to OLD 6.1.124. Never equate this with CP2A 6.1.157.",
        "- Google device Bazelrc still defaults to pinned build 13202960;",
        "  source-tree flags alone were NOT adequate to prove provider equivalence.",
        "",
        "## Raw Bazel provider probes",
    ]
    for name in ("provider","source","source-rule","shusky-kernel","link-path"):
        md.append("- "+name+": cquery exit="+str(selection[name+"_cquery_exit"]) +
                  " / SHA256="+selection[name+"_trace_sha256"])
    md.extend([
        "",
        "Only original Bazel query outputs can establish the next specific",
        "source/provider fix; do NOT ignore kernel ABI/KMI warnings, use stale",
        "module CRCs, downgrade bootloader/rollback data or experiment on device.",
        "",
        "**KMI/AVB/DTBO/PANEL/TENSOR G3/PHYSICAL ROOTFS: UNVERIFIED.**",
        "**REAL DEVICE FLASH GATE: DENY.**"
    ])
    (a.out/"U30_BAZEL_PROVIDER_TRACE.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

if __name__=="__main__":
    main()
