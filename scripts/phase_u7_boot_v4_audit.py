#!/usr/bin/env python3
"""U7: verify Android boot v4 research prototypes. Never execute device operations."""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def check_boot(path, expected_kernel, expected_ramdisk):
    raw = path.read_bytes()
    if len(raw) < 4096 or raw[:8] != b"ANDROID!":
        raise RuntimeError("Not an Android boot image: " + str(path))
    version, hdr_size = read_u32(raw, 40), read_u32(raw, 20)
    kernel_size, rd_size = read_u32(raw, 8), read_u32(raw, 12)
    if version != 4 or hdr_size != 1584:
        raise RuntimeError("Expected Android v4 header: " + str(path))
    if (kernel_size > 0) != expected_kernel or (rd_size > 0) != expected_ramdisk:
        raise RuntimeError("Unexpected v4 sections: " + str(path))
    off = 4096
    kernel = raw[off:off + kernel_size]
    if len(kernel) != kernel_size:
        raise RuntimeError("Truncated kernel")
    off += (kernel_size + 4095) // 4096 * 4096
    ramdisk = raw[off:off + rd_size]
    if len(ramdisk) != rd_size:
        raise RuntimeError("Truncated ramdisk")
    return {"name": path.name, "version": version, "header_bytes": hdr_size,
            "kernel_bytes": kernel_size, "ramdisk_bytes": rd_size,
            "sha256": hash_file(path), "kernel_sha256": hashlib.sha256(kernel).hexdigest(),
            "ramdisk_sha256": hashlib.sha256(ramdisk).hexdigest(),
            "ramdisk": ramdisk}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--legacy-boot", required=True, type=Path)
    p.add_argument("--kernel", required=True, type=Path)
    p.add_argument("--ramdisk-lz4", required=True, type=Path)
    p.add_argument("--ramdisk-dir", required=True, type=Path)
    p.add_argument("--boot", required=True, type=Path)
    p.add_argument("--init-boot", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    original = check_boot(args.legacy_boot, True, False)
    new_boot = check_boot(args.boot, True, False)
    new_init = check_boot(args.init_boot, False, True)
    if original["kernel_sha256"] != hash_file(args.kernel):
        raise RuntimeError("kernel extracted from legacy boot image differs")
    if new_boot["kernel_sha256"] != original["kernel_sha256"]:
        raise RuntimeError("repacked kernel differs from legacy kernel")
    if new_init["ramdisk_sha256"] != hash_file(args.ramdisk_lz4):
        raise RuntimeError("init_boot ramdisk mismatch")

    init = (args.ramdisk_dir / "init").read_text()
    binary = (args.ramdisk_dir / "bin/busybox").read_bytes()[:64]
    if not binary.startswith(b"\x7fELF") or binary[4] != 2:
        raise RuntimeError("initramfs BusyBox is not an ELF64 binary")
    if struct.unpack_from("<H", binary, 18)[0] != 183:
        raise RuntimeError("initramfs BusyBox is not AArch64")
    if "#!/bin/sh" not in init or "U7_RESEARCH_NO_ROOTFS" not in init:
        raise RuntimeError("initramfs is missing the explicit fail-closed marker")
    if "mount /dev/block" in init or "mkfs." in init or "flash" in init.lower():
        raise RuntimeError("unexpected potentially destructive initramfs content")

    decoded = subprocess.run(["lz4", "-dc", str(args.ramdisk_lz4)],
                             check=True, capture_output=True).stdout
    listing = subprocess.run(["cpio", "-it", "--quiet"], input=decoded,
                             check=True, capture_output=True).stdout.decode("utf-8", "replace")
    listing_set = set(x.strip().lstrip("./") for x in listing.splitlines())
    if "init" not in listing_set or "bin/busybox" not in listing_set:
        raise RuntimeError("initramfs archive lacks /init or BusyBox")

    data = {
        "status": "SUCCESS_ANDROID_V4_HEADER_AND_RAMDISK_STRUCTURE_ONLY",
        "flashable": False,
        "bootable_ubuntu": False,
        "ubuntu_rootfs_handoff": "NOT_IMPLEMENTED; init does not mount U6 ext4",
        "current_rom": "Evolution X Android 16; exact vendor/kernel KMI UNKNOWN",
        "input_kernel_provenance": "experimental older Google shusky build run 37721346230",
        "kernel_version_match_with_current_phone": "NOT_ESTABLISHED",
        "boot": {k: v for k, v in new_boot.items() if k != "ramdisk"},
        "init_boot": {k: v for k, v in new_init.items() if k != "ramdisk"},
        "legacy_boot_sha256": hash_file(args.legacy_boot),
        "initramfs_files": sorted(listing_set),
        "hard_blockers": [
            "Kernel not verified against actual installed Evolution X vendor modules/KMI",
            "U6 ext4 volume has no verified on-device location or volume identifier",
            "initramfs deliberately lacks mount/exec handoff to Ubuntu rootfs",
            "vendor_boot, vendor_kernel_boot, dtbo and AVB integration not validated",
            "No Pixel8 DRM, touch, GPU, USB-C display, power or rescue tests"
        ],
    }
    (args.out / "U7_METADATA.json").write_text(json.dumps(data, indent=2) + "\n")
    lines = [
        "# U7 Android v4 experimental boot structure validation",
        "",
        "**PASS (STRUCTURE ONLY) — NOT READY TO BOOT UBUNTU — DO NOT FLASH.**",
        "",
        "## From previously built Google shusky experimental kernel",
        "- Original legacy kernel sha256: " + original["kernel_sha256"],
        "- New research boot kernel sha256: " + new_boot["kernel_sha256"],
        "- v4 boot: kernel bytes " + str(new_boot["kernel_bytes"]) + ", ramdisk bytes 0",
        "- v4 init_boot: kernel bytes 0, ramdisk bytes " + str(new_init["ramdisk_bytes"]),
        "- initramfs includes AArch64 BusyBox and /init; /init is intentionally inert.",
        "- Exact current Evolution X Android16 kernel + vendor-module compatibility: UNKNOWN.",
        "- The U6 Ubuntu 26.04 ext4 rootfs is not mounted or entered by this prototype.",
        "",
        "## SHA256",
        "- Research boot: " + new_boot["sha256"],
        "- Research init_boot: " + new_init["sha256"],
        "- Research ramdisk: " + hash_file(args.ramdisk_lz4),
        "",
        "## Readiness gates",
    ]
    lines += ["- " + item for item in data["hard_blockers"]]
    lines += [
        "",
        "This exercise verified image headers, copied kernel integrity and initramfs",
        "structure on a disposable CI runner. It did not validate any real Pixel 8 boot path.",
        "",
        "**NO ADB / FASTBOOT / DEVICE / PARTITION ACTIONS.**"
    ]
    (args.out / "U7_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
