#!/usr/bin/env python3
"""U18 read-only CP2A GKI source verification and compiled kernel report.

NO flashing, AVB bypass, rollback changes, or device interaction. Checking the
Git commit of the official AOSP GKI source does not validate shiba vendor
modules, device trees, the proprietary display stack, or the stock boot image.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

DEVICE = "shiba"
STOCK_BUILD = "CP2A.260805.005"
STOCK_FINGERPRINT = "google/shiba/shiba:17/CP2A.260805.005/15828068:user/release-keys"
STOCK_UNAME = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
GKI_TAG = "android14-6.1-2025-12_r9"
GKI_COMMIT = "bd23337e42e794964a89f47596daf1209a25ee1a"
GKI_FAMILY = "android14-6.1"
GKI_PATCHLEVEL = (6, 1, 157)


def parse_makefile(text):
    fields = {}
    for k, v in re.findall(r"^(VERSION|PATCHLEVEL|SUBLEVEL|EXTRAVERSION)\s*=\s*(.*)$", text, re.M):
        fields[k] = v.strip()
    if not all(x in fields for x in ("VERSION", "PATCHLEVEL", "SUBLEVEL")):
        raise ValueError("missing VERSION/PATCHLEVEL/SUBLEVEL in official Makefile")
    return tuple(int(fields[x]) for x in ("VERSION", "PATCHLEVEL", "SUBLEVEL"))


def extract_banner(path):
    if not path or not path.is_file():
        return None
    matcher = re.compile(rb"Linux version ([^\x00\n]+)")
    tail = b""
    with path.open("rb") as stream:
        while True:
            piece = stream.read(1024 * 1024)
            if not piece:
                break
            match = matcher.search(tail + piece)
            if match:
                return match.group(1)[:240].decode("ascii", errors="replace")
            tail = piece[-1024:]
    return None


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("source", "build"), required=True)
    p.add_argument("--tag-commit", required=True)
    p.add_argument("--makefile", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dist", type=Path)
    p.add_argument("--manifest", type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    observed_commit = args.tag_commit.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", observed_commit):
        raise SystemExit("FAIL: expected full 40-hex Git commit")
    version = parse_makefile(args.makefile.read_text(encoding="utf-8"))
    exact_commit = observed_commit == GKI_COMMIT
    exact_version = version == GKI_PATCHLEVEL
    provenance_ok = exact_commit and exact_version

    result = {
        "phase": args.phase,
        "source": "https://android.googlesource.com/kernel/common",
        "tag": GKI_TAG,
        "expected_commit": GKI_COMMIT,
        "observed_commit": observed_commit,
        "tag_matches_exact_source_commit": exact_commit,
        "gki_family": GKI_FAMILY,
        "source_kernel_version": ".".join(map(str, version)),
        "source_patch_version_6_1_157": exact_version,
        "source_provenance_pass": provenance_ok,
        "stock_cp2a": {
            "device": DEVICE, "build": STOCK_BUILD,
            "fingerprint_observed_via_adb": STOCK_FINGERPRINT,
            "uname_release_observed_via_adb": STOCK_UNAME,
        },
        "build": {},
        "pixel8_vendor_module_kmi_compatibility_verified": False,
        "pixel8_shiba_dtbo_panel_verified": False,
        "pixel8_android_verified_boot_rollback_verified": False,
        "identical_to_stock_cp2a_boot_img_sha256_verified": False,
        "ubuntu_userspace_integrated": False,
        "physical_pixel8_linux_boot_verified": False,
        "real_device_flash_gate": "DENY",
    }

    if args.phase == "build":
        if not args.dist or not args.manifest:
            raise SystemExit("FAIL: build phase requires --dist and --manifest")
        result["resolved_build_manifest_present"] = (
            args.manifest.is_file() and args.manifest.stat().st_size > 0
        )
        for name in ("Image", "Image.gz", "Image.lz4", "boot.img", "System.map", "vmlinux"):
            f = args.dist / name
            if f.is_file():
                result["build"][name] = {
                    "exists": True, "bytes": f.stat().st_size, "sha256": digest(f)
                }
        image = args.dist / "Image"
        banner = extract_banner(image)
        result["built_kernel_banner"] = banner
        release = banner.split(" ", 1)[0] if banner else None
        result["built_kernel_release"] = release
        result["built_kernel_release_matches_stock_cp2a"] = release == STOCK_UNAME
        result["source_exact_but_not_proof_of_stock_binary_identity"] = True
        result["built_arm64_kernel_present"] = image.is_file() and image.stat().st_size > 0
    else:
        result["build_status"] = "NOT_RUN_IN_SOURCE_PHASE"

    result["status"] = (
        "SOURCE_PIN_VERIFIED"
        if provenance_ok and args.phase == "source"
        else "GKI_COMPILE_SUCCEEDED_NONFLASHABLE"
        if provenance_ok and result.get("built_arm64_kernel_present")
        else "NOT_VERIFIED"
    )
    (args.out / "U18_CP2A_GKI_REPORT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = [
        "# U18 — Pixel 8 CP2A exact GKI source / nonflashable build evidence", "",
        "| Check | Result |", "| --- | --- |",
        f"| Stock Pixel 8 | {STOCK_BUILD} |",
        f"| Stock kernel observed by ADB | \`{STOCK_UNAME}\` |",
        f"| Official GKI tag | \`{GKI_TAG}\` |",
        f"| Source tag peeled commit | \`{observed_commit}\` |",
        f"| Exact source commit match | **{exact_commit}** |",
        f"| Source Makefile version | {'.'.join(map(str, version))} |",
        f"| Source provenance PASS | **{provenance_ok}** |",
    ]
    if args.phase == "build":
        markdown.extend([
            f"| GKI Image built | **{result.get('built_arm64_kernel_present', False)}** |",
            f"| Built kernel release | \`{result.get('built_kernel_release')}\` |",
            f"| Built release matches CP2A | **{result.get('built_kernel_release_matches_stock_cp2a', False)}** |",
        ])
    markdown.extend([
        "| Pixel 8 device kernel modules / display verified | **NO** |",
        "| Bootloader/AVB rollback index verified | **NO** |",
        "| Ubuntu boot on Pixel 8 verified | **NO** |",
        "| Real device flash permission | **DENY** |",
        "",
        "**DO NOT FLASH.** Matching AOSP source commit is not the same as",
        "reproducing Google's signed CP2A boot chain, vendor ABI, shiba DTBO,",
        "or running Ubuntu on the physical device. No phone was connected.",
        "",
    ])
    for name, item in result["build"].items():
        markdown.append(f"- Research build file \`{name}\`: {item['bytes']} bytes, SHA256 \`{item['sha256']}\`.")
    (args.out / "U18_CP2A_GKI_REPORT.md").write_text("\n".join(markdown)+"\n", encoding="utf-8")
    print("\n".join(markdown))
    if not provenance_ok:
        raise SystemExit("FAIL: source commit or version mismatch; fail closed")
    if args.phase == "build" and not result.get("built_arm64_kernel_present"):
        raise SystemExit("FAIL: build did not produce an ARM64 Image")


if __name__ == "__main__":
    main()
