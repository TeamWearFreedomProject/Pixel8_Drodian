#!/usr/bin/env python3
"""U17: non-deployable shusky source-kernel image inventory.

The Google 'shusky' family covers both Pixel 8 (shiba) and 8 Pro (husky).
Presence of *.img in dist does NOT establish shiba's correct DTBO overlay,
matching installed vendor ABI, boot security, or native Ubuntu compatibility.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

# Measured on the user's booting stock Pixel 8 / shiba via ADB (2026-10-11).
CP2A_BUILD = "CP2A.260805.005"
CP2A_KERNEL_RELEASE = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
KERNEL_BANNER = re.compile(rb"Linux version (\d+\.\d+\.\d+-[^\s\x00]+)")


def detect_kernel_release(path: Path):
    """Read-only scan of a raw Linux Image. Missing data must remain unknown."""
    if not path.is_file():
        return None
    with path.open("rb") as source:
        tail = b""
        while True:
            block = source.read(1024 * 1024)
            if not block:
                break
            window = tail + block
            found = KERNEL_BANNER.search(window)
            if found:
                return found.group(1).decode("ascii", errors="replace")
            tail = window[-256:]
    return None


def kernel_patch_relation(candidate, reference):
    """Informational version comparison, NOT an Android rollback-index test."""
    if not candidate:
        return "unknown"
    m1 = re.match(r"^(\d+)\.(\d+)\.(\d+)-", candidate)
    m2 = re.match(r"^(\d+)\.(\d+)\.(\d+)-", reference)
    if not m1 or not m2:
        return "unknown"
    a = tuple(int(x) for x in m1.groups())
    b = tuple(int(x) for x in m2.groups())
    return "older" if a < b else "newer" if a > b else "same-numeric-version"

IMAGE_NAMES = (
    "boot.img",
    "dtbo.img",
    "vendor_kernel_boot.img",
    "vendor_dlkm.img",
    "system_dlkm.img",
    "Image",
    "Image.gz",
    "Image.lz4",
)
# Separate ROM-specific, security-sensitive components must not be
# invented or silently copied from a husky package.
NOT_GENERATED = (
    "init_boot.img", "vendor_boot.img", "vbmeta.img",
    "vbmeta_system.img", "vbmeta_vendor.img", "pvmfw.img", "userdata.img",
)

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(path: Path):
    with path.open("rb") as file:
        first = file.read(12)
    if first.startswith(b"ANDROID!"):
        return "android-boot"
    if first.startswith(b"VNDRBOOT"):
        return "android-vendor-boot"
    if first.startswith(bytes.fromhex("d7b7ab1e")):
        return "android-dtbo-table"
    if first.startswith(b"\x7fELF"):
        return "ELF"
    if first.startswith(bytes.fromhex("1f8b")):
        return "gzip"
    return "unclassified"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-copy-mib", type=int, default=130)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "BUILD_ONLY_NO_DEVICE_PROVENANCE",
        "source_family": "google/shusky",
        "actual_device_baseline": {
            "codename": "shiba",
            "stock_factory_build": CP2A_BUILD,
            "stock_kernel_release_from_adb": CP2A_KERNEL_RELEASE,
            "normal_stock_android_boot_confirmed": True,
        },
        "avb_rollback_indexes_verified": False,
        "bootloader_rollback_version_verified": False,
        "active_and_inactive_slots_verified": False,
        "real_device_flash_gate": "DENY",
        "flash_gate_reasons": [
            "Build output has not been verified against stock CP2A modules and shiba DTBO",
            "Bootloader anti-rollback and AVB rollback indices are not verified",
            "Native Ubuntu rootfs boot, display and USB behavior are not verified",
        ],
        "target_requested": "Pixel 8 shiba (NOT husky)",
        "source_manifest_provided": args.manifest.is_file() and args.manifest.stat().st_size > 0,
        "actual_shiba_dtbo_selection_verified": False,
        "installed_vendor_kernel_module_abi_matched": False,
        "physical_pixel8_linux_boot_verified": False,
        "safe_to_flash": False,
        "ubuntu_rootfs_integrated": False,
        "images": {},
        "not_generated": list(NOT_GENERATED),
    }
    outimages = args.out / "research-images-UNVERIFIED"
    outimages.mkdir(parents=True, exist_ok=True)
    if args.dist.is_dir():
        for name in IMAGE_NAMES:
            source = args.dist / name
            if not source.is_file():
                report["images"][name] = {"present": False}
                continue
            size = source.stat().st_size
            data = {
                "present": True, "bytes": size, "sha256": sha256(source),
                "format_hint": classify(source), "included_in_ci_artifact": False,
            }
            if 0 < size <= args.max_copy_mib * 1024 * 1024:
                # Copy only research artifacts. Their folder name MUST NOT be
                # construed as an instruction to flash any partition.
                import shutil
                shutil.copyfile(source, outimages / name)
                data["included_in_ci_artifact"] = True
            report["images"][name] = data
    release = detect_kernel_release(args.dist / "Image")
    exact = release == CP2A_KERNEL_RELEASE if release else False
    report["built_kernel_release"] = release
    report["built_kernel_matches_stock_cp2a_exactly"] = exact
    report["built_kernel_patch_relation_to_stock"] = kernel_patch_relation(
        release, CP2A_KERNEL_RELEASE
    )
    if not exact:
        report["flash_gate_reasons"].insert(
            0, "Kernel release does not exactly match stock CP2A (or is unknown)"
        )
    ready = args.dist.is_dir() and args.manifest.is_file()
    present = [name for name, item in report["images"].items() if item.get("present")]
    report["status"] = "GOOGLE_SHUSKY_SOURCE_BUILD_FILES_PRESENT" if ready and present else "BUILD_FAILED_OR_NO_IMAGES"
    (args.out / "U17_SOURCE_IMAGE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# U17: Google shusky source-kernel research image inventory",
        "",
        "**NOT A SHIBA UBUNTU ROM. DO NOT FLASH.**",
        "",
        "The shusky source family builds components relevant to **both** Pixel 8 and Pixel 8 Pro.",
        "Actual *shiba* panel DTBO selection, installed vendor module ABI, AVB and rootfs",
        "integration have **not** been validated.",
        "",
        "## Current real-device baseline (read-only ADB verification)",
        "",
        f"- Google Pixel 8 **shiba** stock: \`{CP2A_BUILD}\`",
        f"- Stock kernel: \`{CP2A_KERNEL_RELEASE}\`",
        f"- U17 built kernel: \`{release or 'UNKNOWN'}\`",
        f"- Kernel release exactly matches stock: **{exact}**",
        f"- Numeric kernel patch relation to stock: **{report['built_kernel_patch_relation_to_stock']}**",
        "- **REAL-DEVICE FLASH GATE: DENY (research output, not CP2A-compatible firmware).**",
        "- Android rollback protection is determined by bootloader/AVB rollback metadata;",
        "  kernel patch version comparisons alone **cannot** prove rollback safety.",
        "- No flashing, bootloader replacement, AVB bypass, or A/B slot switching.",
        ""
        "",
        "| Filename | Present | Bytes | Format hint | SHA256 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for name, item in report["images"].items():
        rows.append(
            f"| {name} | {item['present']} | {item.get('bytes','—')} | "
            f"{item.get('format_hint','—')} | {item.get('sha256','—')} |"
        )
    rows += [
        "", "## Not produced / not validated",
        "", ", ".join(NOT_GENERATED), "",
        "- Native Ubuntu on real Pixel 8: **NOT VERIFIED**",
        "- Compatibility with stock shiba CP2A.260805.005: **UNVERIFIED**",
        "- Do not mix with husky / Pixel 8 Pro boot files.",
        "- No phone connected; no ADB, fastboot, device write, userdata erase or slot change.",
        "",
    ]
    (args.out / "U17_SOURCE_IMAGE_REPORT.md").write_text(
        "\n".join(rows), encoding="utf-8")
    print("\n".join(rows))
    if not ready or not present:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
