#!/usr/bin/env python3
"""U36 audit: Ubuntu Base ARM64 read-only chroot execution in generic QEMU virt.

Never claim that a QEMU guest mounting a secondary lab disk and running
Ubuntu Base /bin/sh has verified the Pixel 8 kernel, initramfs switch_root,
stock CP2A firmware compatibility, any real phone boot, or safe flashing.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

U35_KERNEL_SHA = "d87f989330a8bdfb49af796bd70ab0f33c37fa8cdb106146a2fd3d26b5bf7030"
U35_INITRAMFS_SHA = "13220360e211b80f6607d01bfe3becec3b61f35178cf4eea3d0ea72128f3edc7"
U35_BASE_SHA = "5a1906794ced63a71a8119c3f211ef5f0bbe0a243001b4bbd41fdf80c5b219fd"

def reject(why):
    raise SystemExit("U36 GENERIC QEMU ROOTFS GATE DENY: " + why)

def hash_file(p):
    h = hashlib.sha256()
    with p.open("rb") as fp:
        for block in iter(lambda: fp.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def main():
    a = argparse.ArgumentParser()
    for name in ("serial_log", "exit_code", "u35_evidence", "base_tar",
                 "qemu_cloud_sha", "qemu_cloud_info"):
        a.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    p = a.parse_args()
    p.out.mkdir(parents=True, exist_ok=True)
    ref = json.loads(p.u35_evidence.read_text())
    if (ref.get("phase") != "U35"
        or ref.get("status") != "EXPERIMENTAL_BOOT_INITBOOT_AND_UBUNTU_BASE_PACKAGING_OFFLINE_PASS"
        or ref.get("physical_Pixel8_flash_gate") != "DENY"
        or ref.get("hardware_boot_verified") is not False
        or ref.get("kernel_release") != "6.1.157-android14-11"):
        reject("U35 immutable successful report identity/safety conditions changed")
    if (ref["boot_img_lab"]["kernel_sha256"] != U35_KERNEL_SHA
        or ref["init_boot_img_lab"]["ramdisk_sha256"] != U35_INITRAMFS_SHA
        or ref["Ubuntu_Base_26_04_ARM64_official_tar_sha256"] != U35_BASE_SHA):
        reject("U35 input research evidence hash is not the inspected successful build")
    if hash_file(p.base_tar) != U35_BASE_SHA:
        reject("fresh Canonical Ubuntu Base tar is NOT the same bytes as U35")
    image_sha = p.qemu_cloud_sha.read_text().strip()
    if not re.fullmatch(r"[a-f0-9]{64}", image_sha):
        reject("cloud Ubuntu image digest invalid")
    disk = json.loads(p.qemu_cloud_info.read_text())
    if disk.get("format") != "qcow2" or disk.get("virtual-size", 0) < 1000000000:
        reject("unsupported generic cloud image disk metadata")
    rc = int(p.exit_code.read_text().strip())
    log = p.serial_log.read_text(encoding="utf-8", errors="replace")
    gates = {
        "cloud_init_bootcmd": "U36_GUEST_BOOTCMD_REACHED" in log,
        "ubuntu_cloud_guest_arch": bool(re.search(r"U36_GUEST_KERNEL_ARCH=aarch64\b", log)),
        "read_only_lab_ext4_mount": "U36_GUEST_LAB_ROOT_MOUNT_READONLY=TRUE" in log,
        "ubuntu_base_shell_exec_inside_chroot":
            "U36_CHROOT_UBUNTU_BASE_SHELL_EXECUTED=TRUE" in log,
        "ubuntu_base_version_from_inside_chroot":
            bool(re.search(r"U36_CHROOT_UBUNTU_BASE_VERSION=26\.04\b", log)),
        "ubuntu_base_arch_from_inside_chroot":
            bool(re.search(r"U36_CHROOT_KERNEL_ARCH=aarch64\b", log)),
        "post_chroot_guest_completion": "U36_GUEST_AFTER_CHROOT_SUCCESS" in log,
        "actual_qemu_exit_zero": rc == 0
    }
    passed = all(gates.values())
    result = {
        "phase": "U36",
        "status": "QEMU_UBUNTU_BASE_ARM64_READONLY_CHROOT_EXEC_PASS"
                  if passed else "QEMU_UBUNTU_BASE_ARM64_READONLY_CHROOT_EXEC_FAIL",
        "scope": "GENERIC QEMU ARM64 virt; official Ubuntu cloud image kernel, separate Canonical Ubuntu Base ext4 lab disk mounted read-only and executed via chroot",
        "verified_u35_run": 38196600339,
        "verified_u35_boot_kernel_payload_sha256": U35_KERNEL_SHA,
        "verified_u35_initramfs_payload_sha256": U35_INITRAMFS_SHA,
        "reused_identical_canonical_ubuntu_base_tar_sha256": U35_BASE_SHA,
        "generic_qemu_cloud_image_sha256": image_sha,
        "actual_qemu_exit_code": rc,
        "checks": gates,
        "real_initramfs_pid1_tested": False,
        "initramfs_switch_root_tested": False,
        "U33_shiba_research_GKI_booted_in_QEMU": False,
        "shiba_cp2a_kernel_vendor_KMI_compatibility_proven": False,
        "shiba_dtbo_panel_avb_rollback_recovery_checked": False,
        "ubuntu_display_desktop_or_phone_peripherals_tested": False,
        "ubuntu_base_is_configured_desktop_os": False,
        "physical_phone_accessed": False,
        "produced_pixel8_flashable_image": False,
        "physical_pixel8_flash_gate": "DENY"
    }
    (p.out / "U36_QEMU_ARM64_BASE_READONLY_CHROOT_AUDIT.json").write_text(
        json.dumps(result, indent=2) + "\n")
    report = [
        "# U36 — actual Ubuntu Base arm64 shell execution within generic QEMU guest",
        "",
        "- Fresh Canonical Base tar SHA256 matches previous U35: " + U35_BASE_SHA,
        "- QEMU cloud image SHA256: " + image_sha,
        "- Actual QEMU exit: " + str(rc),
        "- CI gate: " + result["status"],
        "",
        *("- " + key + ": " + ("PASS" if ok else "FAIL")
          for key, ok in gates.items()),
        "",
        "This is **guest read-only mount + chroot**, NOT a Linux PID1",
        "initramfs switch_root and NOT Pixel 8 hardware emulation.",
        "Ubuntu Base alone is not a fully installed Ubuntu desktop.",
        "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (p.out / "U36_QEMU_ARM64_BASE_READONLY_CHROOT_SUMMARY.md").write_text(
        "\n".join(report) + "\n")
    print("\n".join(report))
    if not passed:
        reject("one or more guest serial and exit requirements failed")

if __name__ == "__main__":
    main()
