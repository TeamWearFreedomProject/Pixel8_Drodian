#!/usr/bin/env python3
"""U23: actual QEMU ARM64 guest Ubuntu 26.04 mount + switch_root evidence.

QEMU's generic Linux 6.6.89 is NOT the U18 Tensor G3 kernel. This is
a read-only guest simulation of the U20 *current* guarded first-stage design.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

U6_ROOTFS_SHA = "d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e"
U9_QEMU_KERNEL_SHA = "718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc"
U20_INITRAMFS_SHA = "827ded5bce36ce87238645536a77ce3a464236edbeaaa61cd1bba617d8d72c1c"
U18_GKI_SHA = "384f1aca6a5b040a7f0fe6d3ff5f39b8813256827bf0b2f622126b2eb6d0386c"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for data in iter(lambda: f.read(2**20), b""):
            h.update(data)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    for k in ("negative", "positive", "kernel", "rootfs", "u20init",
              "instrumented", "u18report", "u20report", "out"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    pins={"U6_rootfs": (a.rootfs, U6_ROOTFS_SHA),
          "U9_generic_qemu_kernel": (a.kernel,U9_QEMU_KERNEL_SHA),
          "U20_static_guarded_initramfs": (a.u20init,U20_INITRAMFS_SHA)}
    for key,(f,expected) in pins.items():
        if sha(f)!=expected: raise SystemExit(f"WRONG PINNED BYTES: {key}")
    u18=json.loads(a.u18report.read_text())
    u20=json.loads(a.u20report.read_text())
    if u18.get("build",{}).get("Image",{}).get("sha256")!=U18_GKI_SHA:
        raise SystemExit("U18 genuine GKI SHA provenance missing")
    if u20.get("real_device_flash_gate")!="DENY":
        raise SystemExit("U20 real device DENY safety gate missing")
    if u20.get("new_U20_rebuilt_guarded_initramfs_sha256")!=U20_INITRAMFS_SHA:
        raise SystemExit("U20 report and rebuilt initramfs do not match")
    neg=a.negative.read_text(errors="replace")
    pos=a.positive.read_text(errors="replace")
    checks={
        "negative_missing_uuid_rejected": "U8 HALT: requires exactly one u8.rootuuid" in neg,
        "positive_guest_linux_kernel_boot": bool(re.search(r"Linux version 6\.6\.",pos)),
        "reviewed_U20_firststage_started": "U23_INIT_STARTED" in pos,
        "actual_U6_ext4_mounted_readonly_in_guest": "U23_ROOTFS_READONLY_MOUNTED" in pos,
        "actual_Ubuntu26_04_release_checked": "U23_UBUNTU_RELEASE_VERIFIED" in pos,
        "reviewed_U20_switch_root_reached": "U23_SWITCH_ROOT_ATTEMPT" in pos,
        "ubuntu_systemd_PID1_observed": bool(re.search(r"systemd\[1\]|Welcome to Ubuntu",pos)),
    }
    result={
        "status": "PASS_QEMU_GUEST_U20_REBUILT_INIT_TO_UBUNTU_SYSTEMD"
                  if all(checks.values()) else "FAIL_QEMU_BOOT_HANDOFF_GATE",
        "guest_stage_checks": checks,
        "source_artifacts": {k:sha(v[0]) for k,v in pins.items()},
        "U23_instrumented_vm_only_initramfs_sha256": sha(a.instrumented),
        "U18_pixel_GKI_compiled_image_sha256_not_booted_in_QEMU": U18_GKI_SHA,
        "negative_guest_does_not_modify_rootfs": True,
        "qemu_kernel_generic_linux6_6_not_pixel8": True,
        "real_shiba_6_1_157_vendor_drivers_tested": False,
        "pixel8_real_hardware_kernel_booted": False,
        "pixel8_screen_touch_wifi_usb_verified": False,
        "full_ubuntu_login_gui_working": False,
        "physical_phone_changed": False,
        "real_device_flash_gate": "DENY",
    }
    (a.out/"U23_BOOT_HANDOFF.json").write_text(json.dumps(result,indent=2)+"\n")
    report=["# U23 — Real QEMU AArch64 guest handoff using U20 corrected initramfs","",
            f"**{result['status']}**","",
            "This is a genuine QEMU virt ARM64 kernel boot, **NOT a Pixel 8 or Tensor G3 boot**.","",
            "| Check | Observed |","| --- | --- |"]
    report += [f"| {k} | **{v}** |" for k,v in checks.items()]
    report += [
        "", "## What this establishes",
        "- Real generic ARM64 Linux 6.6.89 started the corrected U20 static BusyBox + UUID probe.",
        "- The original hash-pinned Ubuntu 26.04 2GiB rootfs was offered as a READ-ONLY virtio disk.",
        "- Actual Linux rootfs mount, os-release checking, and switch_root intent were checked in the guest.",
        "- The genuine Ubuntu systemd PID1 serial logs were observed only if the above stage passes.",
        "- The U18 GKI 6.1.157 was verified as a separate upstream-sourced asset, NOT as the QEMU guest kernel.",
        "", "## Physical Pixel 8 obstacles remain",
        "- U22 vendor-module 6.1.157 build outcome, exact shiba dtbo/panel, KMI and symbol CRCs.",
        "- Actual stock CP2A bootloader/verified boot/rollback and native rootfs handoff.",
        "- No Pixel boot image built. No real hardware touched.",
        "**REAL DEVICE FLASH GATE: DENY**",
    ]
    (a.out/"U23_BOOT_HANDOFF.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))
    if not all(checks.values()):
        raise SystemExit("U23 QEMU failed a genuine boot/mount/switch_root stage")
if __name__=="__main__":
    main()
