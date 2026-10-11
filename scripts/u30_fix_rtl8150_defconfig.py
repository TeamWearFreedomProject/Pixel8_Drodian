#!/usr/bin/env python3
"""U30: keep optional RTL8150 exclusion and r9 GKI defconfig consistent.

U25 disabled a legacy external RTL8150 USB-Ethernet module using its own
Kconfig depends on BROKEN, but left CONFIG_USB_RTL8150=m in Google's
gki_defconfig. Native source kernel_build checks the configuration with
savedefconfig, so the dangling request fails compilation before any kernel
objects build. We only remove this exact stale request in disposable CI.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

PIN="bd23337e42e794964a89f47596daf1209a25ee1a"

def stop(msg):
    raise SystemExit("U30 RTL8150 GKI CONFIG FAIL CLOSED: "+msg)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--src",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    src=args.src
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    actual=subprocess.check_output(
        ["git","-C",str(src/"aosp"),"rev-parse","HEAD"],text=True
    ).strip()
    if actual!=PIN:
        stop("not the pinned official 6.1.157 r9 GKI")
    cfg=src/"aosp/arch/arm64/configs/gki_defconfig"
    kconfig=src/"aosp/drivers/net/usb/Kconfig"
    module_file=src/"aosp/modules.bzl"
    if not cfg.is_file() or not kconfig.is_file() or not module_file.is_file():
        stop("expected pinned kernel defconfig/Kconfig/module list files missing")
    k=kconfig.read_text()
    if k.count("config USB_RTL8150\n\tdepends on BROKEN\n")!=1:
        stop("U25 exclusion is not present exactly as reviewed")
    data=cfg.read_text()
    if data.count("CONFIG_USB_RTL8150=m\n")!=1:
        stop("expected exactly one old RTL8150=m line; config changed")
    before=sha(cfg)
    replacement=data.replace("CONFIG_USB_RTL8150=m\n","",1)
    if "CONFIG_USB_RTL8150" in replacement:
        stop("other RTL8150 entries need source review")
    cfg.write_text(replacement)
    diff=subprocess.run(
        ["git","-C",str(src/"aosp"),"diff","--","arch/arm64/configs/gki_defconfig"],
        text=True,capture_output=True,check=True
    ).stdout
    lines=[x for x in diff.splitlines() if (x.startswith("+") or x.startswith("-"))
           and not (x.startswith("+++") or x.startswith("---"))]
    if lines!=["-CONFIG_USB_RTL8150=m"]:
        stop("unexpected GKI defconfig diff; refusing to proceed")
    (out/"U30_OPTIONAL_RTL8150_CONFIG_DIFF.txt").write_text(diff)

    # kernel_aarch64 declares GKI module_implicit_outs through modules.bzl.
    # U30 Stage1 compiled for ~15 minutes, then the strict Kleaf rule rejected
    # missing rtl8150.ko: the optional module's build output was still listed.
    modules=module_file.read_text()
    expected_module='"drivers/net/usb/rtl8150.ko",'
    module_candidates=re.findall(
        r'(?m)^[ \t]*"drivers/net/usb/rtl8150\.ko",[ \t]*
        "source_pin":PIN,
        "source_path":"aosp/arch/arm64/configs/gki_defconfig",
        "kconfig_user_approved_exclusion_preserved":True,
        "source_original_sha256":before,
        "source_updated_sha256":sha(cfg),
        "gki_modules_bzl_original_sha256":module_before,
        "gki_modules_bzl_updated_sha256":sha(module_file),
        "gki_implicit_module_outs_removed":"drivers/net/usb/rtl8150.ko",
        "all_other_GKI_module_outs_retained":True,
        "config_line_removed":"CONFIG_USB_RTL8150=m",
        "other_modules_disabled_by_this_change":False,
        "integrated_SoC_USB_disabled":False,
        "gki_source_is_byte_identical_to_stock":False,
        "production_runtime_compatibility_verified":False,
        "real_device_flash_gate":"DENY"
    }
    (out/"U30_OPTIONAL_RTL8150_CONFIG_PATCH.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
,modules
    )
    if len(module_candidates)!=1 or modules.count(expected_module)!=1:
        stop("GKI module list changed, expected one rtl8150.ko output only")
    if "get_gki_modules_list" not in modules:
        stop("Google GKI source module list is not recognized")
    module_before=sha(module_file)
    retained=[
        line for line in modules.splitlines(keepends=True)
        if not re.fullmatch(r'[ \t]*"drivers/net/usb/rtl8150\.ko",[ \t]*\r?\n?',line)
    ]
    revised="".join(retained)
    if len(modules.splitlines())-len(revised.splitlines())!=1:
        stop("unexpected number of GKI module entries changed")
    if expected_module in revised:
        stop("RTL8150 still remains in GKI implicit outs after patch")
    module_file.write_text(revised)
    module_diff=subprocess.run(
        ["git","-C",str(src/"aosp"),"diff","--","modules.bzl"],
        text=True,capture_output=True,check=True
    ).stdout
    changed=[
        line for line in module_diff.splitlines()
        if line.startswith(("+","-")) and not line.startswith(("+++","---"))
    ]
    if len(changed)!=1 or not re.fullmatch(
        r'-[ \t]*"drivers/net/usb/rtl8150\.ko",[ \t]*',changed[0]
    ):
        stop("GKI implicit modules diff modified more than optional RTL8150 output")
    (out/"U30_OPTIONAL_RTL8150_GKI_MODULE_OUTS_DIFF.txt").write_text(module_diff)

    report={
        "status":"U30_LEGACY_OPTIONAL_RTL8150_GKI_CONFIG_RECONCILED_SOURCE_ONLY",
        "source_pin":PIN,
        "source_path":"aosp/arch/arm64/configs/gki_defconfig",
        "kconfig_user_approved_exclusion_preserved":True,
        "source_original_sha256":before,
        "source_updated_sha256":sha(cfg),
        "config_line_removed":"CONFIG_USB_RTL8150=m",
        "other_modules_disabled_by_this_change":False,
        "integrated_SoC_USB_disabled":False,
        "gki_source_is_byte_identical_to_stock":False,
        "production_runtime_compatibility_verified":False,
        "real_device_flash_gate":"DENY"
    }
    (out/"U30_OPTIONAL_RTL8150_CONFIG_PATCH.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
