#!/usr/bin/env python3
"""U19: non-destructive binary compatibility audit of *actual* U17/U18 CI products.

A matching major KMI family or a .ko filename is not proof that a module
will load with CP2A's kernel. This audit MUST NOT generate flash firmware.
"""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

STOCK = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
EXPECTED_U17 = "6.1.124-android14-11-g8d713f9e8e7b-ab13202960"
EXPECTED_GKI_COMMIT = "bd23337e42e794964a89f47596daf1209a25ee1a"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def raw_image_identity(path, sha):
    if not path.is_file() or digest(path) != sha:
        raise RuntimeError(f"Missing or tampered upstream image: {path}")


def get_kernel_release(image):
    with image.open("rb") as f:
        previous = b""
        while True:
            piece = f.read(2 * 1024 * 1024)
            if not piece:
                break
            match = re.search(rb"Linux version (6\.1\.[0-9]+-[^\x00\s]+)", previous + piece)
            if match:
                return match.group(1).decode("ascii", "replace")
            previous = piece[-512:]
    raise RuntimeError(f"Kernel version banner not found in {image}")


def vermagic_scan(image):
    """Count raw ext4 string occurrences. NOT distinct modules or loaded drivers."""
    findings = collections.Counter()
    with image.open("rb") as f:
        previous = b""
        while True:
            block = f.read(2 * 1024 * 1024)
            if not block:
                break
            buffer = previous + block
            if not buffer.startswith(b""):
                raise AssertionError("unreachable")
            end = len(buffer) - 256
            # Scanning the overlap only once avoids duplicate vermagic counts.
            for m in re.finditer(rb"vermagic=(6\.1\.[^\x00\r\n]{8,150})\x00", buffer):
                if m.start() < end or len(block) < 2 * 1024 * 1024:
                    findings[m.group(1).decode("ascii", "replace")] += 1
            previous = buffer[end:] if end > 0 else buffer
    return dict(findings)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--u17", type=Path, required=True)
    p.add_argument("--u18", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    u17_report = json.loads((args.u17 / "U17_SOURCE_IMAGE_REPORT.json").read_text())
    u18_report = json.loads((args.u18 / "U18_CP2A_GKI_REPORT.json").read_text())
    u17dir = args.u17 / "research-images-UNVERIFIED"
    u18image = args.u18 / "research-UNVERIFIED/GKI-6.1.157-r9-Image-DO-NOT-FLASH"

    for name in ("Image", "vendor_dlkm.img", "system_dlkm.img", "dtbo.img", "vendor_kernel_boot.img"):
        raw_image_identity(u17dir / name, u17_report["images"][name]["sha256"])
    raw_image_identity(u18image, u18_report["build"]["Image"]["sha256"])
    u17kernel = get_kernel_release(u17dir / "Image")
    u18kernel = get_kernel_release(u18image)
    if u17kernel != EXPECTED_U17:
        raise RuntimeError("U17 binary kernel release changed unexpectedly")
    if not u18kernel.startswith("6.1.157-android14-11-"):
        raise RuntimeError("U18 is not an Android14-11 6.1.157 kernel")
    if u18_report["observed_commit"] != EXPECTED_GKI_COMMIT:
        raise RuntimeError("U18 GKI source provenance changed")
    results = {}
    allkeys = set()
    for name in ("vendor_dlkm.img", "system_dlkm.img"):
        path = u17dir / name
        with path.open("rb") as f:
            f.seek(1080)
            if f.read(2) != bytes.fromhex("53ef"):
                raise RuntimeError(f"Unexpected ext4 superblock: {name}")
        marks = vermagic_scan(path)
        if not marks:
            raise RuntimeError(f"No modinfo vermagic evidence in {name}")
        allkeys.update(marks)
        results[name] = {
            "size_bytes": path.stat().st_size,
            "sha256": digest(path),
            "vermagic_occurrences_NOT_distinct_modules": marks,
            "all_observed_vamagic_6_1_157": all(x.startswith("6.1.157") for x in marks),
        }

    report = {
        "status": "U19_OFFLINE_BINARY_ABI_AUDIT_PASS_INTEGRATION_BLOCKED",
        "source_artifacts": {
            "u17_run": 38099633940, "u18_run": 38101661379
        },
        "stock_cp2a_uname": STOCK,
        "u17_built_vendor_kernel_release": u17kernel,
        "u18_built_gki_release": u18kernel,
        "u18_source_git_commit": EXPECTED_GKI_COMMIT,
        "u17_vendor_modules": results,
        "vermagic_strings_found": sorted(allkeys),
        "all_examined_module_vermagic_6_1_157": all(
            x.startswith("6.1.157") for x in allkeys
        ),
        "actual_CP2A_stock_vendor_module_binaries_obtained": False,
        "module_symbol_crc_validation_performed": False,
        "shiba_dtbo_runtime_selection_verified": False,
        "device_panel_touch_gpu_compatibility_verified": False,
        "safe_to_combine_U17_modules_with_U18_GKI": False,
        "valid_pixel8_ubuntu_boot_image_created": False,
        "physical_device_modified": False,
        "real_device_flash_gate": "DENY",
    }
    if report["all_examined_module_vermagic_6_1_157"]:
        raise RuntimeError("Unexpected U17 module set: re-investigate before changing verdict")
    (args.out / "U19_VENDOR_ABI_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    rows = [
        "# U19 — Pixel 8 vendor module vs CP2A exact GKI offline audit", "",
        "**AUDIT PASSED. INTEGRATION BLOCKED. DO NOT FLASH.**", "",
        f"- CP2A on-device kernel: \`{STOCK}\`",
        f"- Older U17 shusky build kernel: \`{u17kernel}\`",
        f"- U18 build kernel (official matching source): \`{u18kernel}\`",
        "- U18's GKI commit is genuine, but its compiled kernel is not a signed CP2A stock image.",
        "",
        "| U17 module container | Observed raw vermagic text / frequency |",
        "| --- | --- |",
    ]
    for name, data in results.items():
        for mark, count in data["vermagic_occurrences_NOT_distinct_modules"].items():
            rows.append(f"| {name} | \`{mark}\` — {count} occurrences |")
    rows += [
        "",
        "**These counts are raw metadata occurrences, not installed drivers, and",
        "not a full module symbol/KMI proof.**",
        "",
        "Correct shiba + CP2A vendor module binaries and DTBO provenance are",
        "still required before any mixing or rootfs handoff can be validated.",
        "Do not attempt to load or flash U17 6.1.124 modules on CP2A.",
        "No physical phone, ADB/fastboot, rollback actions or device writes.",
        "**REAL DEVICE FLASH GATE: DENY.**",
    ]
    (args.out / "U19_VENDOR_ABI_REPORT.md").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
