#!/usr/bin/env python3
"""U17: non-deployable shusky source-kernel image inventory.

The Google 'shusky' family covers both Pixel 8 (shiba) and 8 Pro (husky).
Presence of *.img in dist does NOT establish shiba's correct DTBO overlay,
matching installed vendor ABI, boot security, or native Ubuntu compatibility.
"""
import argparse
import hashlib
import json
from pathlib import Path

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
        "- Compatibility with Evolution X Android 16 or the currently modified device: **UNKNOWN**",
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
