#!/usr/bin/env python3
"""U25 isolated research-only shusky GKI 6.1.157 source compatibility attempt.

Only patches disposable GitHub Actions working-tree source, not repository
upstream or real Pixel hardware. Never bypass KMI/modpost/ABI errors.
"""
import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

GKI_SHA="bd23337e42e794964a89f47596daf1209a25ee1a"
STOCK_RELEASE="6.1.157-android14-11-gbd23337e42e7-ab14791245"
SOC_SHA="057ab18a9cc0e318538b419eafc565a7fbe1d320"

def digest(f):
    h=hashlib.sha256()
    with f.open("rb") as stream:
        for block in iter(lambda:stream.read(2**20),b""):h.update(block)
    return h.hexdigest()

def fail(message):
    raise SystemExit("U25 FAIL CLOSED: "+message)

def pin_sources(source):
    aosp=subprocess.check_output(["git","-C",str(source/"aosp"),"rev-parse","HEAD"],text=True).strip()
    soc=subprocess.check_output(["git","-C",str(source/"private/google-modules/soc/gs"),"rev-parse","HEAD"],text=True).strip()
    if aosp!=GKI_SHA or soc!=SOC_SHA:
        fail("unexpected GKI/SoC Git pin; refusing any research patch")
    make=(source/"aosp/Makefile").read_text()
    v=[]
    for key in ("VERSION","PATCHLEVEL","SUBLEVEL"):
        m=re.search(r"^"+key+r"\s*=\s*(\d+)",make,re.M)
        if not m:fail("missing GKI Makefile version "+key)
        v.append(int(m.group(1)))
    if v!=[6,1,157]:fail("source was not 6.1.157")
    return {"kernel/common":aosp, "google-modules/soc/gs":soc}

def patch(source,out):
    pins=pin_sources(source)
    # This optional USB dongle driver was explicitly excluded by project owner.
    kconfig=source/"aosp/drivers/net/usb/Kconfig"
    orig=kconfig.read_text()
    needle="config USB_RTL8150\n"
    if orig.count(needle)!=1:fail("RTL8150 Kconfig changed, no unsafe global rewrite")
    kconfig.write_text(orig.replace(needle,needle+"\tdepends on BROKEN\n",1))

    # Preserve the SoC USB controller and its register semantics. Rename only
    # the 0xd024 lane-0 constant from vendor's header; newer GKI defines a
    # distinct lane-indexed macro of the same name, DWC3_LLUCTL(n).
    socroot=source/"private/google-modules/soc/gs"
    header=socroot/"include/linux/usb/dwc3-exynos.h"
    header_data=header.read_text()
    define=r"(?m)^[ \t]*#define[ \t]+DWC3_LLUCTL[ \t]+0xd024[ \t]*$"
    if len(re.findall(define,header_data))!=1:
        fail("vendor USB register constant no longer exactly 0xd024")
    gki_core=(source/"aosp/drivers/usb/dwc3/core.h").read_text()
    if not re.search(r"(?m)^[ \t]*#define[ \t]+DWC3_LLUCTL\(n\)[ \t]+\(0xd024 \+ \(\(n\) \* 0x80\)\)",gki_core):
        fail("upstream DWC3_LLUCTL(n) semantics changed; review required")

    old_symbol=re.compile(r"\bDWC3_LLUCTL\b(?![ \t]*\()")
    new_symbol="GS_DWC3_LLUCTL_LANE0_0XD024"
    changed=[]
    count=0
    # Restrict edits to GS SoC project source, NOT generic GKI USB internals.
    for path in sorted(socroot.rglob("*")):
        if path.suffix not in (".h",".c") or not path.is_file():
            continue
        raw=path.read_text(errors="replace")
        new,count_this=old_symbol.subn(new_symbol,raw)
        if count_this:
            path.write_text(new)
            changed.append(str(path.relative_to(source)))
            count+=count_this
    if str(header.relative_to(source)) not in changed or count<1:
        fail("vendor USB driver patch affected unexpected source files")
    for path in changed:
        if not path.startswith("private/google-modules/soc/gs/"):
            fail("unexpected edited project outside GS SoC")

    data={"phase":"source_patch_only","official_source_pins":pins,
          "old_USB_RTL8150_disabled_optional_nic":True,
          "internal_DWC3_exynos_controller_kept_enabled":True,
          "DWC3_old_base_0xd024_semantics_preserved_by_vendor_local_constant":True,
          "DWC3_new_GKI_lane_macro_left_unchanged":True,
          "SoC_source_files_patched":changed,"legacy_macro_occurrences_renamed":count,
          "prebuilt_gki_should_be_disabled_by_Bazel_CLI":True,
          "original_vendor_source_still_modified":True,
          "kernel_stock_CP2A_byte_identity":False,
          "pixel_hardware_tested":False,"real_device_flash_gate":"DENY"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"U25_RESEARCH_SOURCE_PATCH.json").write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data,indent=2))

def build_report(src,out,exit_code):
    pin_sources(src)
    dist=src/"out/shusky/dist"
    files={}
    for name in ("Image","Image.gz","Image.lz4","boot.img","dtbo.img",
                 "vendor_dlkm.img","system_dlkm.img","vendor_kernel_boot.img"):
        p=dist/name
        if p.is_file():files[name]={"bytes":p.stat().st_size,"sha256":digest(p)}
    kernel_version=None
    image=dist/"Image"
    if image.is_file():
        previous=b""
        with image.open("rb") as f:
            while True:
                chunk=f.read(2**20)
                if not chunk:break
                m=re.search(rb"Linux version (6\.1\.[0-9]+-[^\x00\s]+)",previous+chunk)
                if m:
                    kernel_version=m.group(1).decode("ascii",errors="replace")
                    break
                previous=chunk[-512:]
    log=(out/"U25_FULL_BUILD.log")
    if not log.is_file():fail("compilation output log missing")
    logs=log.read_text(errors="replace")
    result={
       "status":"U25_PROTOTYPE_BUILT_VENDOR_ABI_UNVERIFIED" if exit_code==0 and image.is_file()
                else "U25_COMPILE_FAILED_WITH_EVIDENCE_PRESERVED",
       "real_build_exit":exit_code,
       "source_gki_git_sha":GKI_SHA,
       "use_prebuilt_gki":False,
       "use_signed_prebuilts":False,
       "source_modified_as_documented":True,
       "optional_rtl8150_excluded":True,
       "soc_internal_usb_kept":True,
       "previous_provider_KMI_mismatch_reobserved":"KMI or sublevel mismatch before running make modules_install" in logs,
       "previous_DWC3_LLUCTL_redefinition_reobserved":"'DWC3_LLUCTL' macro redefined" in logs,
       "real_generated_kernel_release":kernel_version,
       "kernel_version_exactly_stock":kernel_version==STOCK_RELEASE,
       "kernel_is_6_1_157":bool(kernel_version and kernel_version.startswith("6.1.157-android14-11-")),
       "generated_dist_files_HASH_ONLY_NOT_DEPLOYABLE":files,
       "real_CP2A_vendor_module_KMI_symbol_CRC_verified":False,
       "shiba_hardware_display_touch_USB_boot_verified":False,
       "physical_pixel8_tested":False,
       "avb_or_bootloader_rollback_verified":False,
       "ubuntu_bootable_on_pixel8":False,
       "real_device_flash_gate":"DENY"
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"U25_GKI_SOURCE_REBUILD.json").write_text(json.dumps(result,indent=2)+"\n")
    report=[
      "# U25 — 6.1.157 shusky source-only build attempt",
      "**EXPERIMENTAL SOURCE PATCH + NO PREBUILT GKI. DO NOT FLASH.**","",
      f"- GKI source SHA: \`{GKI_SHA}\` (working tree patched for diagnostics).",
      "- Explicit Bazel flags disable 6.1.124 prebuilt and signed prebuilts.",
      "- Optional RTL8150 external USB LAN excluded; internal Exynos DWC3 controller retained.",
      "- Vendor's lane-zero 0xd024 constant renamed, NOT replaced with a different offset.",
      f"- Actual compiler exit code: **{exit_code}**.",
      f"- Kernel release if generated: \`{kernel_version or 'NOT PRODUCED'}\`.",
      f"- KMI/sublevel mismatch from earlier run reobserved: **{result['previous_provider_KMI_mismatch_reobserved']}**.",
      f"- DWC3 name collision reobserved: **{result['previous_DWC3_LLUCTL_redefinition_reobserved']}**.",
      "- A build success does NOT verify original CP2A vendor module CRCs, kernel signatures, display, USB operation or Ubuntu init.",
      "- Never install this diagnostic kernel on Pixel 8; no phone or partitions accessed.",
      "**REAL DEVICE FLASH GATE: DENY.**","",
      "## Built outputs (if any; hash-only audit, not packaged for device)",
    ]
    report += [f"- {n} ({v['bytes']} bytes): SHA256 {v['sha256']}" for n,v in files.items()]
    (out/"U25_GKI_SOURCE_REBUILD.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    for mode in ("patch","audit"):
        p=sub.add_parser(mode);p.add_argument("--source-dir",type=Path,required=True)
        p.add_argument("--out",type=Path,required=True)
        if mode=="audit":p.add_argument("--exit-code",type=int,required=True)
    args=ap.parse_args()
    if args.cmd=="patch":patch(args.source_dir,args.out)
    else:build_report(args.source_dir,args.out,args.exit_code)

if __name__=="__main__": main()
