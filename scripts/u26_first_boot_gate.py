#!/usr/bin/env python3
"""U26: verify real isolated QEMU guest boot-failure gates and cross-phase evidence.

Never connects to a physical Pixel 8, performs no flashing/partition action,
and NEVER confuses an offline guest boot with CP2A shiba hardware readiness.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOTFS_SHA="d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e"
QEMU_KERNEL_SHA="718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc"
RAMDISK_SHA="827ded5bce36ce87238645536a77ce3a464236edbeaaa61cd1bba617d8d72c1c"
GKI_SOURCE="bd23337e42e794964a89f47596daf1209a25ee1a"
STOCK="6.1.157-android14-11-gbd23337e42e7-ab14791245"

EXPECTED_CASES={
    "NO_CONSENT":"U8 HALT: research opt-in token missing",
    "BAD_UUID":"U8 HALT: UUID format rejected",
    "DUPLICATE_UUID":"U8 HALT: requires exactly one u8.rootuuid",
    "UNMATCHED_UUID":"U8 HALT: verified Linux root volume not found",
}

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for data in iter(lambda:f.read(2**21),b""):h.update(data)
    return h.hexdigest()

def check(cond,msg):
    if not cond:raise SystemExit("U26 FAIL CLOSED: "+msg)

def main():
    p=argparse.ArgumentParser()
    for arg in ("rootfs","qemu-kernel","u20-initramfs","u18-report","u19-report",
                "u20-report","u23-report","u24-report","logdir","out"):
        p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    phases={}
    for stage,fn in (
        ("U18",a.u18_report),("U19",a.u19_report),("U20",a.u20_report),
        ("U23",a.u23_report),("U24",a.u24_report)):
        phases[stage]=json.loads(fn.read_text(encoding="utf-8"))
    actual={
      "U6 rootfs":digest(a.rootfs),
      "U9 QEMU kernel":digest(a.qemu_kernel),
      "U20 guarded initramfs":digest(a.u20_initramfs)
    }
    for key,expected in [
        ("U6 rootfs",ROOTFS_SHA),
        ("U9 QEMU kernel",QEMU_KERNEL_SHA),
        ("U20 guarded initramfs",RAMDISK_SHA)]:
        check(actual[key]==expected,"source artifact SHA mismatch: "+key)
    check(phases["U18"]["observed_commit"]==GKI_SOURCE,"U18 GKI source provenance drift")
    check(phases["U18"]["real_device_flash_gate"]=="DENY","U18 missing DENY")
    check(phases["U19"]["real_device_flash_gate"]=="DENY","U19 missing DENY")
    check(phases["U19"]["safe_to_combine_U17_modules_with_U18_GKI"] is False,
          "old 6.1.124 modules were marked safe")
    check(phases["U20"]["new_U20_rebuilt_guarded_initramfs_sha256"]==RAMDISK_SHA,
          "U20 ramdisk evidence changed")
    check(phases["U20"]["real_device_flash_gate"]=="DENY","U20 missing DENY")
    check(phases["U23"]["status"]=="PASS_QEMU_GUEST_U20_REBUILT_INIT_TO_UBUNTU_SYSTEMD",
          "U23 positive Ubuntu systemd VM boot not proven")
    check(phases["U23"]["real_device_flash_gate"]=="DENY","U23 missing DENY")
    check(phases["U24"]["status"]=="U24_OFFICIAL_PINNED_SOURCE_PROVIDER_AND_DWC3_COLLISION_CONFIRMED",
          "U24 source provider evidence missing")
    check(phases["U24"]["real_device_flash_gate"]=="DENY","U24 missing DENY")
    checks={}
    for name, expected_text in EXPECTED_CASES.items():
        path=a.logdir/f"U26_{name}.log"
        text=path.read_text(errors="replace")
        checks[name]={
            "expected_halt":expected_text,
            "halt_observed":expected_text in text,
            "ubuntu_systemd_started":("systemd[1]" in text or "Welcome to Ubuntu" in text),
            "switch_root_attempted":("switch_root" in text),
        }
        check(checks[name]["halt_observed"],f"{name}: no expected safe HALT")
        check(not checks[name]["ubuntu_systemd_started"],f"{name}: unexpectedly booted Ubuntu")
    verified={
      "gki_exact_official_6_1_157_source":True,
      "real_ubuntu_rootfs_mount_and_systemd_in_QEMU_only":True,
      "malformed_or_ambiguous_boot_parameters_halt_in_QEMU":True,
      "stock_CP2A_shiba_modules_symbol_and_KMI_compatibility":False,
      "correct_shiba_dtbo_panel_and_touch_verified":False,
      "working_usb_serial_kernel_diagnostics_on_device":False,
      "bootloader_AVB_rollback_and_recovery_verified":False,
      "physical_ubuntu_rootfs_location_proven_safe":False,
      "physical_ubuntu_first_boot_completed":False
    }
    report={
      "status":"U26_NEGATIVE_BOOT_SAFETY_TESTS_PASS_PHYSICAL_BOOT_DENIED",
      "stock_CP2A_kernel":STOCK,
      "offline_sha256":actual,
      "input_CI_evidence":[
          "U18 generic GKI 6.1.157 source", "U19 older vendor ABI mismatch",
          "U20 guarded initramfs", "U23 actual QEMU Ubuntu systemd",
          "U24 prebuilt dependency and DWC3 header source evidence"
      ],
      "U25_vendor_source_rebuild_status":"NOT_REPRESENTED_IN_THIS_SEPARATE_PRESTARTED_VM_GATE",
      "negative_boot_cases":checks,
      "boot_preflight_requirements":verified,
      "safe_to_boot_pixel8":False,
      "safe_to_flash_pixel8":False,
      "physical_pixel8_modified":False,
      "real_device_flash_gate":"DENY"
    }
    (a.out/"U26_BOOT_SAFETY_GATE.json").write_text(json.dumps(report,indent=2)+"\n")
    md=[
        "# U26 — actual ARM64 VM negative boot guards and Pixel 8 first-boot preflight", "",
        "**QEMU NEGATIVE CONTROLS PASS / PIXEL 8 FIRST BOOT NOT APPROVED**","",
        "| QEMU rejected parameter set | Expected guard | Rejected |",
        "| --- | --- | --- |",
    ]
    for name,case in checks.items():
        md.append(f"| {name} | \`{case['expected_halt']}\` | **{case['halt_observed']}** |")
    md.extend([
        "", "## What is actually complete",
        "- U18 GKI source identity 6.1.157 (not signed stock binary).",
        "- U20 Ubuntu 26.04 ext4 + guarded initramfs source proof.",
        "- U23 kernel -> initramfs -> real Ubuntu systemd boot in **generic QEMU**.",
        "- U26 guards reject invalid/missing consent, malformed, duplicate or",
        "  mismatched rootfs UUID, with no guest Ubuntu handoff.",
        "", "## U30 physical Pixel 8 boot readiness blockers",
    ])
    for key,done in verified.items():
        md.append(("- VERIFIED: " if done else "- BLOCKED: ")+key)
    md.extend([
        "", "**REAL DEVICE FLASH GATE: DENY**",
        "No hardware detected; no Android boot image, init_boot, userdata or partition operations.",
        "Passing this VM safety stage does not override U22/U25 physical driver",
        "ABI and on-device rootfs blockers, or consent/recovery review.",
    ])
    (a.out/"U26_BOOT_SAFETY_GATE.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

if __name__=="__main__":main()
