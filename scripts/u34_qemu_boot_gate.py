#!/usr/bin/env python3
"""U34: fail-closed audit of official Ubuntu 26.04 ARM64 cloud VM smoke boot.

This is deliberately a QEMU generic ARM64 VIRT machine, NOT Google Tensor G3
or a Pixel 8 emulator. A successful guest cloud-init smoke check says NOTHING
about actual stock CP2A module CRCs, panel, AVB or physical flash safety.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

IMAGE="ubuntu-26.04-server-cloudimg-arm64.img"
EXPECTED_ARCH="aarch64"
EXPECTED_OS="26.04"

def die(reason):
    raise SystemExit("U34 QEMU ARM64 CLOUD SMOKE FAIL CLOSED: "+reason)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--boot-log",type=Path,required=True)
    p.add_argument("--rc",type=Path,required=True)
    p.add_argument("--image-sha",type=Path,required=True)
    p.add_argument("--image-info",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    if not a.boot_log.is_file() or not a.rc.is_file():
        die("QEMU serial log or actual exit status unavailable")
    log=a.boot_log.read_text(encoding="utf-8",errors="replace")
    rc=int(a.rc.read_text().strip())
    digest=a.image_sha.read_text().strip()
    if not re.fullmatch("[a-f0-9]{64}",digest):
        die("cloud image SHA256 missing or malformed")
    info=json.loads(a.image_info.read_text())
    if info.get("format")!="qcow2" or info.get("virtual-size",0)<1_000_000_000:
        die("official Ubuntu cloud image not confirmed QCOW2 disk")
    # Precisely require the final cloud-init stage inside the *guest* to
    # report its own architecture and OS version, followed by shutdown.
    arch_ok=re.search(r"(?m)U34_CLOUD_INIT_FINAL_ARCH=aarch64\b",log)!=None
    os_ok=re.search(r"(?m)U34_CLOUD_INIT_FINAL_VERSION=26\.04\b",log)!=None
    completed="U34_CLOUD_INIT_FINAL_SUCCESS" in log
    early="U34_BOOTCMD_ARM64_REACHED" in log
    good=(rc==0 and arch_ok and os_ok and early and completed)
    result={
        "phase":"U34",
        "scope":"public Canonical Ubuntu 26.04 arm64 cloud image on generic QEMU virt board",
        "official_download_name":IMAGE,
        "official_cloud_image_sha256":digest,
        "checksum_verified_earlier_against_official_HTTPS_SHA256SUMS":True,
        "cryptographic_GPG_signature_checked":False,
        "qcow2_format":info.get("format"),
        "guest_architecture_aarch64_verified":arch_ok,
        "guest_version_26_04_verified":os_ok,
        "guest_cloud_init_bootcmd_reached":early,
        "guest_cloud_init_final_stage_reached":completed,
        "actual_QEMU_exit_status":rc,
        "status":"GENERIC_UBUNTU_26_04_ARM64_QEMU_SMOKE_PASS" if good
                 else "GENERIC_UBUNTU_26_04_ARM64_QEMU_SMOKE_FAIL",
        "Pixel8_shiba_hardware_emulated":False,
        "Google_Tensor_G3_device_kernel_tested":False,
        "U33_6_1_157_GKI_booted_in_QEMU":False,
        "CP2A_stock_vendor_KMI_or_module_compatibility_proven":False,
        "Pixel8_compatible_initramfs_and_DTBO_prepared":False,
        "Pixel8_UBUNTU_rootfs_partition_or_install_image_prepared":False,
        "Pixel8_recovery_and_AVB_rollback_verified":False,
        "real_Pixel8_accessed":False,
        "school_PC_admin_rights_needed":False,
        "physical_Pixel8_flash_gate":"DENY"
    }
    (a.out/"U34_QEMU_ARM64_UBUNTU2604_AUDIT.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    md=[
       "# U34: Ubuntu 26.04 ARM64 guest boot (QEMU generic machine, not Pixel 8)",
       "",
       "- Official Canonical cloud QCOW2 SHA256: "+digest,
       "- Actual QEMU exit: "+str(rc),
       "- Guest architecture aarch64: "+str(arch_ok),
       "- Guest VERSION_ID 26.04: "+str(os_ok),
       "- Guest cloud-init bootcmd stage: "+str(early),
       "- Guest cloud-init final stage: "+str(completed),
       "- Gate: "+result["status"],
       "",
       "**This VM uses an Ubuntu-supplied generic ARM64 kernel, NOT U33 Pixel 8 kernel.**",
       "It does not prove a deployable initramfs, GPU, touchscreen, modem,",
       "Android AVB, stock CP2A KMI/CRC, shiba DTBO or physical phone boot.",
       "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (a.out/"U34_QEMU_ARM64_UBUNTU2604_SUMMARY.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))
    if not good:
        die("guest's actual arch, release, final stage or QEMU shutdown did not pass")

if __name__=="__main__":
    main()
