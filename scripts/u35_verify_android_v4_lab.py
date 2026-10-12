#!/usr/bin/env python3
"""U35: fail-closed offline Android boot header V4 *laboratory* structure check.

Verifies mkbootimg-generated boot and init_boot actually contain the exact U33
research GKI compressed Image and U35 ARM64 initramfs bytes. An identical CRC
or byte-level boot header is NOT evidence that the Pixel 8 will boot: matching
CP2A vendor modules, init_boot/AVB, actual board, DTBO and recovery are absent.

NO physical device, ADB, fastboot, partition writes or unlocking anywhere.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

PAGE=4096
HEADER_V4=1584
RELEASE="6.1.157-android14-11"
STOCK="6.1.157-android14-11-gbd23337e42e7-ab14791245"

def fail(s):
    raise SystemExit("U35 LAB STRUCTURE FAIL CLOSED: "+s)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1<<20),b""):
            h.update(data)
    return h.hexdigest()

def align(v):
    return (v+PAGE-1)//PAGE*PAGE

def parse_boot_v4(path):
    if not path.is_file():
        fail("missing Android image: "+str(path))
    with path.open("rb") as f:
        h=f.read(HEADER_V4)
        if len(h)!=HEADER_V4 or h[:8]!=b"ANDROID!":
            fail("invalid boot image magic/header: "+str(path))
        ksize,rsize,osinfo,hsize=struct.unpack_from("<4I",h,8)
        vers=struct.unpack_from("<I",h,40)[0]
        signature=struct.unpack_from("<I",h,1580)[0]
        if vers!=4 or hsize!=HEADER_V4:
            fail("expected official Android v4 boot header")
        if signature!=0:
            fail("lab image unexpectedly contains a signature; AVB not audited")
        if ksize>70*1024*1024 or rsize>16*1024*1024:
            fail("unbounded component size")
        if osinfo!=0:
            fail("lab OS patch/version must not falsely claim CP2A stock")
        if len(h[44:1580].rstrip(b"\x00"))!=0:
            fail("unknown cmdline injected into lab header")
        if path.stat().st_size != PAGE+align(ksize)+align(rsize):
            fail("unexpected trailer/padding/extra data in research image")
        f.seek(PAGE)
        kernel=f.read(ksize)
        f.seek(PAGE+align(ksize))
        ramdisk=f.read(rsize)
    return {
        "header_version":vers,
        "header_size":hsize,
        "kernel_bytes":ksize,
        "ramdisk_bytes":rsize,
        "kernel_sha256":hashlib.sha256(kernel).hexdigest(),
        "ramdisk_sha256":hashlib.sha256(ramdisk).hexdigest(),
        "file_bytes":path.stat().st_size,
        "file_sha256":sha(path),
        "has_AVB_signature":False
    }

def kernel_banner(image):
    prev=b""
    with image.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            found=re.search(rb"Linux version (6\.1\.[^\x00\s]+)",prev+block)
            if found:
                return found.group(1).decode("ascii","replace")
            prev=block[-2048:]
    return None

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--boot",type=Path,required=True)
    a.add_argument("--init-boot",type=Path,required=True)
    a.add_argument("--kernel",type=Path,required=True)
    a.add_argument("--compressed-kernel",type=Path,required=True)
    a.add_argument("--ramdisk",type=Path,required=True)
    a.add_argument("--ubuntu-base-tar",type=Path,required=True)
    a.add_argument("--rootfs-image",type=Path,required=True)
    a.add_argument("--busybox",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    kernel_release=kernel_banner(args.kernel)
    if kernel_release!=RELEASE:
        fail("GKI raw Image release does not match pinned 6.1.157")
    if args.kernel.stat().st_size!=35633664:
        fail("unexpected source-built GKI Image byte count")
    with args.busybox.open("rb") as f:
        elf=f.read(20)
    if len(elf)<20 or elf[:4]!=b"\x7fELF" or elf[4]!=2 or elf[5]!=1 or struct.unpack_from("<H",elf,18)[0]!=183:
        fail("initramfs BusyBox is not 64-bit little-endian AArch64 ELF")
    boot=parse_boot_v4(args.boot)
    init_boot=parse_boot_v4(args.init_boot)
    if boot["kernel_bytes"]==0 or boot["ramdisk_bytes"]!=0:
        fail("boot.img must contain ONLY GKI kernel, no generic ramdisk")
    if init_boot["kernel_bytes"]!=0 or init_boot["ramdisk_bytes"]==0:
        fail("init_boot.img must contain ONLY U35 initramfs, no kernel")
    if boot["kernel_sha256"]!=sha(args.compressed_kernel):
        fail("boot.img embedded bytes differ from the freshly built GKI Image.lz4")
    if init_boot["ramdisk_sha256"]!=sha(args.ramdisk):
        fail("init_boot.img embedded bytes differ from the new initramfs archive")
    if args.ubuntu_base_tar.stat().st_size<10_000_000:
        fail("Canonical Ubuntu Base 26.04 ARM64 tar unexpectedly small")
    if args.rootfs_image.stat().st_size<500_000_000:
        fail("rootfs lab filesystem image unexpectedly small")
    result={
        "phase":"U35",
        "status":"EXPERIMENTAL_BOOT_INITBOOT_AND_UBUNTU_BASE_PACKAGING_OFFLINE_PASS",
        "target_device":"Pixel 8 shiba only (no on-phone test)",
        "Tensor_Linux_reference":"Tenser-Linux/Tensor-Linux documents husky; no husky binaries imported",
        "kernel_release":kernel_release,
        "stock_CP2A_complete_kernel_release":STOCK,
        "exact_stock_kernel_release_matches":kernel_release==STOCK,
        "raw_research_GKI_Image_sha256":sha(args.kernel),
        "compressed_research_GKI_Image_lz4_sha256":sha(args.compressed_kernel),
        "boot_img_lab":boot,
        "init_boot_img_lab":init_boot,
        "Ubuntu_Base_26_04_ARM64_official_tar_sha256":sha(args.ubuntu_base_tar),
        "Ubuntu_Base_ext4_lab_image_sha256":sha(args.rootfs_image),
        "U35_stage0_busybox_arm64_sha256":sha(args.busybox),
        "initramfs_only_early_stage0_not_a_functional_ubuntu_handoff":True,
        "pixel8_vendor_kernel_boot_vendor_ramdisk_dtbo_used_from_stock":False,
        "tensor_g3_shiba_specific_board_DTBO_verified":False,
        "stock_CP2A_module_crc_equivalence_verified":False,
        "rootfs_partition_selection_or_decryption_verified":False,
        "AVB_rollback_recovery_verified":False,
        "Ubuntu_graphics_touch_wireless_tested":False,
        "hardware_boot_verified":False,
        "physical_pixel8_accessed":False,
        "boot_or_flash_safe":False,
        "physical_Pixel8_flash_gate":"DENY"
    }
    out=args.out
    (out/"U35_OFFLINE_BOOTV4_UBUNTU_LAB_REPORT.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    md=[
       "# U35 — Android boot v4 + Ubuntu ARM64 packaging audit",
       "",
       "- Actual pinned GKI kernel Image: "+kernel_release,
       "- Android boot.img: v4, kernel payload ONLY, "+str(boot["file_bytes"])+" bytes",
       "- Android init_boot.img: v4, initramfs payload ONLY, "+str(init_boot["file_bytes"])+" bytes",
       "- Embedded kernel SHA matches generated Image.lz4: TRUE",
       "- Embedded ramdisk SHA matches U35 new initramfs: TRUE",
       "- Stage-0 BusyBox is AArch64 ELF: TRUE",
       "- Official Ubuntu Base ARM64 tar and bare ext4 laboratory image: present",
       "",
       "**No real phone image approved. These are UNVERIFIED lab images.**",
       "Ubuntu Base is not a configured phone desktop. Stage-0 only diagnoses",
       "startup; NO real-device rootfs mount/Ubuntu userspace handoff is built.",
       "No AVB signature, vendor boot chain, shiba panel DTBO or stock CP2A",
       "module compatibility verification. No kernel/userdata/bootloader flash.",
       "",
       "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (out/"U35_OFFLINE_BOOTV4_UBUNTU_LAB_REPORT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

if __name__=="__main__":
    main()
