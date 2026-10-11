#!/usr/bin/env python3
"""U30: reconcile OPTIONAL RTL8150 disabled in Kconfig with both output inventories.

Pinned-GKI source-only CI experiment. U25 already excluded ONLY optional
USB RTL8150 with a guarded Kconfig change. Native Google Kleaf checks the
gki_defconfig, and then requires all modules.bzl implicit module outputs.
Both declarations must reflect the reviewed U25 exclusion. All other USB,
SoC and WLAN modules are preserved; never deploy or flash this build.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

PIN="bd23337e42e794964a89f47596daf1209a25ee1a"

def stop(reason):
    raise SystemExit("U30 OPTIONAL USB MODULE FAIL CLOSED: "+reason)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def get_diff(src,rel):
    return subprocess.run(
        ["git","-C",str(src/"aosp"),"diff","--",rel],
        text=True,capture_output=True,check=True
    ).stdout

def validate_delta(diff,old_line):
    changed=[
        line for line in diff.splitlines()
        if line.startswith(("+","-")) and not line.startswith(("+++","---"))
    ]
    if len(changed)!=1 or changed[0]!=old_line:
        stop("unexpected Git diff for optional RTL8150 line: "+repr(changed))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    src=args.src
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    actual=subprocess.check_output(
        ["git","-C",str(src/"aosp"),"rev-parse","HEAD"],text=True
    ).strip()
    if actual!=PIN:
        stop("source Git SHA differs from pinned r9 Linux 6.1.157")

    kconfig=src/"aosp/drivers/net/usb/Kconfig"
    defconfig=src/"aosp/arch/arm64/configs/gki_defconfig"
    implicit=src/"aosp/modules.bzl"
    if not all(p.is_file() for p in (kconfig,defconfig,implicit)):
        stop("official Kconfig, gki_defconfig or modules.bzl absent")
    if kconfig.read_text().count("config USB_RTL8150\n\tdepends on BROKEN\n")!=1:
        stop("reviewed optional RTL8150 Kconfig exclusion missing")

    original_config=defconfig.read_text()
    old_config_line="CONFIG_USB_RTL8150=m\n"
    if original_config.count(old_config_line)!=1:
        stop("expected exactly one optional RTL8150 defconfig entry")
    original_defconfig_sha=sha(defconfig)
    defconfig.write_text(original_config.replace(old_config_line,"",1))
    diff_config=get_diff(src,"arch/arm64/configs/gki_defconfig")
    validate_delta(diff_config,"-CONFIG_USB_RTL8150=m")
    (out/"U30_OPTIONAL_RTL8150_CONFIG_DIFF.txt").write_text(diff_config)

    original_modules=implicit.read_text()
    expected='"drivers/net/usb/rtl8150.ko",'
    if original_modules.count(expected)!=1:
        stop("expected exactly one implicit output for optional RTL8150")
    if "get_gki_modules_list" not in original_modules:
        stop("GKI implicit module inventory API unexpected")
    original_module_sha=sha(implicit)
    old_module_lines=re.findall(
        r'(?m)^[ \t]*"drivers/net/usb/rtl8150\.ko",[ \t]*$',
        original_modules
    )
    if len(old_module_lines)!=1:
        stop("exact RTL8150 module list declaration unexpected")
    old_line=old_module_lines[0]
    lines=original_modules.splitlines(keepends=True)
    remainder=[
        line for line in lines
        if line.rstrip("\r\n")!=old_line
    ]
    if len(lines)-len(remainder)!=1:
        stop("module line removal count differs from 1")
    implicit.write_text("".join(remainder))
    diff_modules=get_diff(src,"modules.bzl")
    validate_delta(diff_modules,"-"+old_line)
    (out/"U30_OPTIONAL_RTL8150_GKI_MODULE_OUTS_DIFF.txt").write_text(diff_modules)

    report={
      "phase":"U30",
      "status":"GKI_6_1_157_OPTIONAL_RTL8150_INVENTORIES_ALIGNED_CI_ONLY",
      "pinned_upstream_gki_sha":PIN,
      "disabled_optional_USB_nic":"RTL8150",
      "prior_Kconfig_exclusion_verified":True,
      "gki_defconfig_only_entry_removed":"CONFIG_USB_RTL8150=m",
      "gki_defconfig_original_sha256":original_defconfig_sha,
      "gki_defconfig_updated_sha256":sha(defconfig),
      "modules_bzl_only_entry_removed":"drivers/net/usb/rtl8150.ko",
      "modules_bzl_original_sha256":original_module_sha,
      "modules_bzl_updated_sha256":sha(implicit),
      "other_kernels_WLAN_DWC3_modules_disabled":False,
      "stock_CP2A_compatible_or_flashable":False,
      "real_device_flash_gate":"DENY"
    }
    (out/"U30_OPTIONAL_RTL8150_CONFIG_PATCH.json").write_text(
        json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
