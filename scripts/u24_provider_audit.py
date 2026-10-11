#!/usr/bin/env python3
"""U24: source-authenticated audit of U22's 6.1.124 GKI provider and DWC3 ABI.

Fail closed on missing official files. The audit does not modify kernel source,
does not compile anything or turn artifacts into flashable images.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SHIBA_STOCK = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
GKI = "bd23337e42e794964a89f47596daf1209a25ee1a"
COMMON_DEV = "397babd94c06783d8430c838475955f0b6ff63c2"
SOC = "057ab18a9cc0e318538b419eafc565a7fbe1d320"
PREBUILT = "13202960"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check(x, label):
    if not x: raise SystemExit("U24 FAIL CLOSED: "+label)

def main():
    a=argparse.ArgumentParser()
    for name in ("manifest","u22log","devicebazelrc","soch","gkih","out"):
        a.add_argument("--"+name,required=True,type=Path)
    z=a.parse_args()
    z.out.mkdir(parents=True,exist_ok=True)
    projects={p.get("name"):p.attrib for p in ET.parse(z.manifest).getroot().findall("project")}
    expected={
        "kernel/common":GKI,
        "kernel/devices/google/common":COMMON_DEV,
        "kernel/google-modules/soc/gs":SOC
    }
    for name,expected_sha in expected.items():
        check(projects.get(name,{}).get("revision")==expected_sha,
              "manifest Git commit drift for "+name)
    device=z.devicebazelrc.read_text()
    soc=z.soch.read_text()
    common=z.gkih.read_text()
    compiler=z.u22log.read_text(errors="replace")
    clean_device_lines=[line.strip() for line in device.splitlines()
                        if line.strip() and not line.lstrip().startswith("#")]
    check("build --use_prebuilt_gki=true" in clean_device_lines,
          "official device.bazelrc did not set prebuilt GKI")
    check(any(PREBUILT in line and "KLEAF_DOWNLOAD_BUILD_NUMBER_MAP" in line
              for line in clean_device_lines),
          "expected old GKI prebuilt build ID not configured")
    check("build --use_signed_prebuilts=true" in clean_device_lines,
          "signed prebuilt default no longer configured")
    check("build:use_source_tree_aosp --use_prebuilt_gki=false" in clean_device_lines,
          "official source-tree override no longer available")
    check('DWC3_LLUCTL' in soc and 'DWC3_LLUCTL' in common,
          "USB DWC3 LLUCTL macro overlap not present in pinned files")
    dev_defs=re.findall(r"^[ \t]*#[ \t]*define[ \t]+DWC3_LLUCTL(?=[ \t(])([^\r\n]*)",soc,re.M)
    gki_defs=re.findall(r"^[ \t]*#[ \t]*define[ \t]+DWC3_LLUCTL(?=[ \t(])([^\r\n]*)",common,re.M)
    print("Exact DWC3 definitions: vendor=", repr(dev_defs), "GKI=", repr(gki_defs))
    check(len(dev_defs)==1 and len(gki_defs)==1,
          "unexpected DWC3 macro definitions; needs human review")
    check("0xd024" in dev_defs[0].lower() and "0xd024" in gki_defs[0].lower(),
          "DWC3 register offsets unexpectedly changed")
    check("(n)" in gki_defs[0] and "(n)" not in dev_defs[0],
          "different DWC3 macro API conflict not confirmed")
    check("KMI or sublevel mismatch before running make modules_install" in compiler,
          "U22 historic GKI prebuilt mismatch log not found")
    check("DWC3_LLUCTL" in compiler and "macro redefined" in compiler,
          "U22 historic DWC3 compilation failure log not found")
    refs=re.findall(r"DWC3_LLUCTL",soc)
    report={
        "status":"U24_OFFICIAL_PINNED_SOURCE_PROVIDER_AND_DWC3_COLLISION_CONFIRMED",
        "source_pin_commits":expected,
        "file_sha256":{
            "device_bazelrc":sha(z.devicebazelrc.read_bytes()),
            "soc_dwc3_exynos_header":sha(z.soch.read_bytes()),
            "gki_dwc3_core_header":sha(z.gkih.read_bytes()),
        },
        "default_google_device_prebuilt_gki":True,
        "default_old_build_number":PREBUILT,
        "gki_source_tree_override_present":True,
        "gki_release_sourced_from_U18":GKI,
        "observed_U22_6_1_124_gki_provider_in_log":True,
        "DWC3_LLUCTL_soc_definition":dev_defs[0].strip(),
        "DWC3_LLUCTL_gki_definition":gki_defs[0].strip(),
        "DWC3_LLUCTL_soc_header_text_appearances":len(refs),
        "candidate_nonshipping_build_fix":"Explicit Bazel --use_prebuilt_gki=false --use_signed_prebuilts=false; re-audit exact KMI before any linking",
        "candidate_DWC3_fix":"Research-only targeted source API rename/adaptation; DO NOT disable USB SoC driver or suppress compiler -Werror",
        "can_flash_pixel8":False,
        "stock_CP2A_binary_equivalence_verified":False,
        "driver_KMI_module_symbols_verified":False,
        "bootable_pixel8_ubuntu":False,
        "real_device_flash_gate":"DENY"
    }
    (z.out/"U24_PROVIDER_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    md=[
        "# U24 — pinned CP2A GKI provider and DWC3 macro audit", "",
        "**SOURCE + HISTORIC BUILD LOG VERIFIED. GKI/DRIVER INTEGRATION BLOCKED. DO NOT FLASH.**", "",
        f"- Device CP2A kernel: `{SHIBA_STOCK}`.",
        f"- Pinned 6.1.157 common source SHA: `{GKI}`.",
        f"- Google Pixel-specific Bazelrc pins default prebuilt **{PREBUILT}** (U17 6.1.124).",
        "- By default the Bazel provider uses old signed GKI prebuilts, even if common source is switched to 6.1.157.",
        "- Official source override is available; U25 must explicitly disable prebuilt and signed prebuilt providers.",
        f"- Vendor DWC3 old definition: `#define DWC3_LLUCTL {dev_defs[0].strip()}`.",
        f"- New GKI DWC3 definition: `#define DWC3_LLUCTL{gki_defs[0].strip()}`.",
        "- Same register base address but different macro argument API; a source adaptation requires review.",
        "- KMI/sublevel mismatch and macro collision independently confirmed from U22 Run #3.",
        "- Build success, if later achieved, does NOT establish CP2A module CRC/AVB/board compatibility.",
        "- No phone, flashing, ABI bypass or kernel image was produced in U24.",
        "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (z.out/"U24_PROVIDER_AUDIT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

if __name__=="__main__":
    main()
