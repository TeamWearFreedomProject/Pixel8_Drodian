#!/usr/bin/env python3
"""U30 staged source-only build gates for Google Pixel 8 shiba research.

The FIRST gate checks a kernel produced directly by the r9 GKI source target.
The SECOND gate checks the shusky dist graph for stale downloaded-GKI paths.
The FINAL audit rejects stale or missing Image even if Bazel exits zero.
No firmware delivery, boot operation, bypassed CRC or on-device action.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CP2A="6.1.157-android14-11-gbd23337e42e7-ab14791245"
OLD="6.1.124-android14-11-g8d713f9e8e7b-ab13202960"
GKI="bd23337e42e794964a89f47596daf1209a25ee1a"

def abort(reason):
    raise SystemExit("U30 STAGED BUILD FAIL-CLOSED: "+reason)

def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()

def banner(path):
    tail=b""
    rx=re.compile(rb"Linux version (6\.1\.[^\x00\s]+)")
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            m=rx.search(tail+chunk)
            if m:
                return m.group(1).decode("ascii","replace")
            tail=chunk[-2048:]
    return None

def locate(src,root):
    if not root.exists():
        abort("expected Bazel output directory missing: "+str(root))
    found=subprocess.run(
        ["find","-L",str(root),"-maxdepth","9","-type","f","-name","Image"],
        text=True,capture_output=True)
    if found.returncode:
        abort("Bazel Image file inventory could not be inspected: "+found.stderr[:500])
    return [Path(item) for item in found.stdout.splitlines() if item.strip()]

def save(out,name,info):
    out.mkdir(parents=True,exist_ok=True)
    (out/name).write_text(json.dumps(info,indent=2,sort_keys=True)+"\n")

def source_audit(src,out,exit_file):
    rc=int(exit_file.read_text().strip())
    root=src/"aosp"
    git=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],
                                text=True).strip()
    if git!=GKI:abort("GKI source Git SHA differs from CP2A r9")
    files=locate(src,src/"bazel-bin/aosp")
    (out/"U30_SOURCE_IMAGE_CANDIDATES.txt").write_text(
        "\n".join(str(x.relative_to(src)) for x in files)+"\n")
    valid=[]
    for f in files:
        rel=banner(f)
        if rel:
            valid.append({"path":str(f.relative_to(src)),"banner":rel,
                          "sha256":sha(f),"bytes":f.stat().st_size})
    matching=[x for x in valid
        if x["banner"].startswith("6.1.157-android14-11")]
    old=[x for x in valid if x["banner"].startswith("6.1.124-android14-11")]
    outcome={
        "stage":"U30_SOURCE_GKI_IMAGE",
        "actual_bazel_exit":rc,
        "gki_git":git,
        "kernel_images_found":valid,
        "CP2A_stock_kernel_release":CP2A,
        "actual_source_6_1_157":bool(matching),
        "old_6_1_124_present":bool(old),
        "device_ever_accessed":False,
        "safe_to_flash":False,
        "real_device_flash_gate":"DENY"
    }
    save(out,"U30_SOURCE_KERNEL_AUDIT.json",outcome)
    if rc!=0:abort("direct source GKI build exit was nonzero: "+str(rc))
    if len(matching)!=1 or old:
        abort("expected exactly one GKI 6.1.157 Image and NO old 6.1.124 Image")
    (out/"U30_SOURCE_KERNEL_PASS.txt").write_text(
        "SOURCE_6_1_157_KERNEL_IMAGE_COMPILED_AND_IDENTIFIED; REAL DEVICE FLASH GATE DENY\n"
    )
    print("U30 stage 1: actual source-built 6.1.157 GKI Image confirmed;",
          matching[0]["path"])

def provider_gate(out):
    files={
      name:out/("U30_"+name+"_PATH_CQUERY.txt")
      for name in ("DIST_TO_SOURCE","DIST_TO_OLD")
    }
    payload={}
    for name,path in files.items():
        if not path.is_file():abort("missing Bazel dist dependency query "+name)
        rc=int((out/("U30_"+name+"_PATH_EXIT.txt")).read_text().strip())
        s=path.read_text(errors="replace")
        payload[name]={"rc":rc,
                       "sha256":hashlib.sha256(s.encode()).hexdigest(),
                       "rules":[v.strip() for v in s.splitlines()
                                if re.search(r"(?m)^(?:\S+\s+)?(?:rule|alias)\s+//",v)]}
    old_res=payload["DIST_TO_OLD"]["rules"]
    source_res=payload["DIST_TO_SOURCE"]["rules"]
    good=(payload["DIST_TO_SOURCE"]["rc"]==0 and
          payload["DIST_TO_OLD"]["rc"]==0 and
          any("_kernel_build rule //aosp:kernel_aarch64" in x for x in source_res) and
          not any("kernel_aarch64_download_or_build" in x for x in old_res))
    report={
      "stage":"U30_SHUSKY_DIST_CONFIGURED_GRAPH_COMPATIBILITY_GATE",
      "query_results":payload,
      "no_old_GKI_downloaded_provider_in_dist_dependency_path":not old_res,
      "source_GKI_reachable_from_dist":any(
          "_kernel_build rule //aosp:kernel_aarch64" in x for x in source_res),
      "allowed_full_compilation":good,
      "not_a_CP2A_vendor_KMI_CRC_proof":True,
      "real_device_flash_gate":"DENY"
    }
    save(out,"U30_DIST_PROVIDER_GATE.json",report)
    if not good:
        abort("source or stale downloaded GKI provider still unresolved in dist graph")
    (out/"U30_PROVIDER_PASS.txt").write_text(
        "DIST_GRAPH_SOURCE_GKI_ONLY_CHECK_PASS_NOT_KMI_PROOF; REAL DEVICE FLASH GATE DENY\n"
    )
    print("U30 stage 2: source GKI path exists; no old provider in dist Bazel cquery")

def full_audit(src,out,exit_file):
    rc=int(exit_file.read_text().strip())
    dist=src/"out/shusky/dist"
    image=dist/"Image"
    rel=banner(image) if image.is_file() else None
    report={
      "stage":"U30_SHUSKY_VENDOR_FULL_DIST",
      "real_bazel_exit":rc,
      "Image_present":image.is_file(),
      "Image_release_actual":rel,
      "Image_sha256":sha(image) if image.is_file() else None,
      "Image_bytes":image.stat().st_size if image.is_file() else None,
      "stock_CP2A":CP2A,
      "source_kernel_6_1_157_confirmed":bool(
          rel and rel.startswith("6.1.157-android14-11")),
      "stock_CP2A_exact_binary_proven":False,
      "vendor_module_symbol_CRCs_verified":False,
      "board_DTBO_GPU_touch_avb_verified":False,
      "real_device_ever_written":False,
      "safe_to_flash":False,
      "real_device_flash_gate":"DENY"
    }
    save(out,"U30_FULL_DIST_AUDIT.json",report)
    if rc!=0:abort("actual shusky full Bazel dist exit was nonzero")
    if not rel or not rel.startswith("6.1.157-android14-11"):
        abort("full shusky dist Image was missing or not source 6.1.157")
    print("U30 stage 3: source 6.1.157 full-shusky dist Image banner passed",
          rel,"/ NEVER FLASH THIS IMAGE")

def main():
    ap=argparse.ArgumentParser()
    subs=ap.add_subparsers(dest="mode",required=True)
    for mode in ("source","graph","full"):
        p=subs.add_parser(mode)
        p.add_argument("--out",type=Path,required=True)
        if mode!="graph":
            p.add_argument("--src",type=Path,required=True)
            p.add_argument("--rc-file",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.mode=="source":source_audit(args.src,args.out,args.rc_file)
    elif args.mode=="graph":provider_gate(args.out)
    else:full_audit(args.src,args.out,args.rc_file)
if __name__=="__main__":main()
