#!/usr/bin/env python3
"""U36 offline validation of QEMU ARM64-only stage-0-to-Ubuntu-Base lab.

'PASS' means structural/audit checks passed, NEVER Pixel 8 boot readiness.
Generated disk & Android research boot images are not published.
"""
import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

PHASE="U36"
MARKER="QEMU_ARM64_UBUNTU_26.04_U36_ONLY"

def die(reason):
    raise SystemExit("U36 HANDOFF LAB GATE FAILED: "+reason)

def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def debugfs_read(image,path):
    result=subprocess.run(["debugfs","-R",f"cat {path}",str(image)],
        check=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode!=0 or b"not found" in result.stderr:
        die(f"missing ext4 lab path: {path}")
    return result.stdout.decode("utf-8","replace")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--rootfs",type=Path,required=True)
    parser.add_argument("--initramfs",type=Path,required=True)
    parser.add_argument("--stage0",type=Path,required=True)
    parser.add_argument("--lab-init",type=Path,required=True)
    parser.add_argument("--base-sha256",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    if not all(p.is_file() for p in (a.rootfs,a.initramfs,a.stage0,a.lab_init,a.base_sha256)):
        die("required built source, ext4, initramfs or official base hash missing")
    s=a.stage0.read_text()
    lab=a.lab_init.read_text()
    assert s.startswith("#!/bin/busybox sh")
    # A build-time denylist: platform-specific flash/partition operations
    # are forbidden in the experimental PID1 and rootfs shell.
    for content in (s,lab):
        for forbidden in ("fastboot ","adb ","dd if=","mkfs.","cryptsetup ","wipefs ","mount -o rw", "flash_", "/dev/block/by-name/userdata"):
            if forbidden in content:
                die("unsafe rootfs/initramfs operation in lab scripts: "+forbidden)
    for required in ("u36.lab=1","u36.root=/dev/vdb","/proc/device-tree/model",
                     "linux,dummy-virt","mount -t ext4 -o ro",
                     "switch_root /newroot /sbin/init", "U36_QEMU_ARM64_SWITCH_ROOT_INVOKED"):
        if required not in s:
            die("missing explicit fail-closed QEMU switch_root guard: "+required)
    if "U36_LAB_SWITCH_ROOT_AARCH64_UBUNTU_BASE_OK" not in lab:
        die("post-handoff witness missing")
    if MARKER not in debugfs_read(a.rootfs,"/etc/u36-lab-rootfs"):
        die("ext4 lab identity marker mismatch")
    if 'VERSION_ID="26.04' not in debugfs_read(a.rootfs,"/etc/os-release"):
        die("Ubuntu Base rootfs release is not 26.04")
    if "U36_LAB_SWITCH_ROOT_AARCH64_UBUNTU_BASE_OK" not in debugfs_read(a.rootfs,"/sbin/init"):
        die("new root /sbin/init is not U36 lab witness")
    if a.rootfs.stat().st_size<500_000_000:
        die("lab ext4 rootfs unexpectedly small")
    # Check initramfs was generated and contains both init and busybox.
    listing=subprocess.run(["sh","-c","gzip -dc \"$1\" | cpio --quiet -t",
                            "_",str(a.initramfs)],
                           capture_output=True,text=True,check=False)
    if listing.returncode!=0 or not {"./init","./bin/busybox"}.issubset(set(listing.stdout.splitlines())):
        die("new ARM64 initramfs missing /init or /bin/busybox")
    digest=a.base_sha256.read_text().strip()
    if "ubuntu-base-26.04.1-base-arm64.tar.gz" not in digest or len(digest.split()[0])!=64:
        die("Canonical Ubuntu Base checksum attestation missing")
    report={
        "phase":"U36",
        "status":"OFFLINE_RESEARCH_QEMU_HANDOFF_ARTIFACT_LAYOUT_PASS",
        "ubuntu_release":"26.04.1 (Base only; no graphical desktop)",
        "ubuntu_base_sha256_report":digest,
        "read_only_ext4_lab_rootfs_sha256":hash_file(a.rootfs),
        "arm64_stage0_initramfs_sha256":hash_file(a.initramfs),
        "qemu_machine_explicit_allowlist":True,
        "root_device_explicit_only":"/dev/vdb",
        "rootfs_marker_verified_in_ext4":True,
        "rootfs_lab_init_witness_verified_in_ext4":True,
        "stage0_switch_root_script_present":True,
        "actual_QEMU_guest_switch_root_seen":False,
        "Ubuntu_systemd_desktop_confirmed":False,
        "Pixel8_hardware_compatibility_confirmed":False,
        "stock_CP2A_KMI_AVB_dtbo_recovery_confirmed":False,
        "real_device_flash_gate":"DENY"
    }
    (a.out/"U36_OFFLINE_HANDOFF_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    (a.out/"U36_OFFLINE_HANDOFF_REPORT.md").write_text(
       "# U36 QEMU ARM64 research handoff layout\n\n"
       "- Ubuntu Base ext4 root marker present: YES\n"
       "- Exact AArch64 static BusyBox in initramfs: U35 prerequisite\n"
       "- QEMU virt model check: REQUIRED\n"
       "- Generic ext4 rootfs opened read-only by PID1: IN SCRIPT, NOT RUNTIME PROVEN\n"
       "- switch_root + QEMU-only /sbin/init witness: IN SCRIPT, NOT RUNTIME PROVEN\n"
       "- Actual QEMU switch_root success: NOT VERIFIED by this static gate\n"
       "- Functional Ubuntu systemd/Wayland: NOT VERIFIED\n"
       "- shiba/Pixel 8 CP2A ABI, AVB, DTBO or real hardware recovery: NOT VERIFIED\n\n"
       "**REAL DEVICE FLASH GATE: DENY.**\n")
    print("U36 PASS: offline QEMU-only handoff layout; REAL DEVICE FLASH DENY")

if __name__=="__main__":
    main()
