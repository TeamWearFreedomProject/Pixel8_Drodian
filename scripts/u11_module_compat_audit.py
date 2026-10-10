#!/usr/bin/env python3
"""U11 offline-only shiba Evolution X module-manifest and U7 kernel audit.

Module filenames in an upstream manifest DO NOT establish driver compatibility.
No ADB, fastboot, mounts, partition writes, hardware or flashable firmware.
"""
import argparse
import csv
import hashlib
import json
import struct
import subprocess
from pathlib import Path

PINS = {
    "shusky": "56006ae8162db285e776d85319d9942945b87194",
    "zuma": "fba447c6317f23501dbac209b6479e458800c449",
    "module_manifest": "9bba989e7dba6f33258049b113adcb33c89054e8",
}
U7_BOOT_SHA = "1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa"
U7_KERNEL_SHA = "8a3ec09cfc307e1f17b868437201b5e6f87a80840cc21bff8aea85e333db8229"
ROLES = ("modules.load", "vendor_kernel_boot.modules.load",
         "vendor_dlkm.modules.load", "system_dlkm.modules.load")


def fail(message):
    raise SystemExit("U11 FAILED CLOSED: " + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_pin(folder, expected):
    got = subprocess.check_output(
        ["git", "-C", str(folder), "rev-parse", "HEAD"], text=True).strip()
    if got != expected:
        fail("source changed: " + str(folder))
    return got


def manifest(folder, name):
    lines = (folder / "6.1" / name).read_text().splitlines()
    rows = [line.strip() for line in lines if line.strip()]
    if not rows or any(not x.endswith(".ko") for x in rows):
        fail("not an expected module list: " + name)
    if len(rows) != len(set(rows)):
        fail("duplicate paths in " + name)
    return rows


def board_specific(path):
    names = [line.split("|", 1)[1] for line in path.read_text().splitlines()
             if line.startswith("modprobe|")]
    if not names or any(not x.endswith(".ko") or "/" in x for x in names):
        fail("unexpected modprobe syntax: " + str(path))
    return names


def boot_check(path):
    data = path.read_bytes()
    if sha(data) != U7_BOOT_SHA or data[:8] != b"ANDROID!":
        fail("U7 experimental boot mismatch")
    version = struct.unpack_from("<I", data, 40)[0]
    header = struct.unpack_from("<I", data, 20)[0]
    size = struct.unpack_from("<I", data, 8)[0]
    if version != 4 or header != 1584 or not 1_000_000 < size < 48_000_000:
        fail("unexpected Android v4 header")
    kernel = data[4096:4096+size]
    if len(kernel) != size or sha(kernel) != U7_KERNEL_SHA:
        fail("unexpected experimental kernel bytes")
    return {"android_header": version, "kernel_bytes": size,
            "kernel_sha256": U7_KERNEL_SHA, "boot_sha256": U7_BOOT_SHA}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--boot", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    pins = {key: source_pin(args.sources / key, commit)
            for key, commit in PINS.items()}

    module_folder = args.sources / "module_manifest"
    tracked = subprocess.check_output(
        ["git", "-C", str(module_folder), "ls-files"], text=True).splitlines()
    binary_files = [x for x in tracked
                    if x.endswith((".ko", ".img", ".dtb", ".dtbo"))]
    if binary_files:
        fail("Unexpected binary files in pinned manifest repo")

    modules = {name: manifest(module_folder, name) for name in ROLES}
    if modules["modules.load"] != modules["vendor_kernel_boot.modules.load"]:
        fail("common ordered module lists differ, must manually inspect")
    shiba = board_specific(module_folder / "6.1" / "init.insmod.shiba.cfg")
    husky = board_specific(module_folder / "6.1" / "init.insmod.husky.cfg")
    if "goodix_brl_touch.ko" not in shiba or "ftm5.ko" not in husky:
        fail("unexpected board-specific touchscreen driver names")

    device_src = args.sources / "shusky"
    if "TARGET_LINUX_KERNEL_VERSION := 6.1" not in (
            device_src / "device-shiba.mk").read_text():
        fail("Evolution X no longer declares Linux kernel 6.1")
    deps = json.loads((device_src / "evolution.dependencies").read_text())
    if not any(x.get("repository") == "LineageOS/android_device_google_shusky-kernels"
               and x.get("branch") == "lineage-23.2" for x in deps):
        fail("missing pinned lineage-23.2 kernel manifest dependency")
    if "BOARD_VENDOR_KERNEL_RAMDISK_KERNEL_MODULES_LOAD" not in (
            device_src / "BoardConfigCommon.mk").read_text():
        fail("vendor kernel module boot ordering not wired")
    recovery = (device_src / "recovery" /
                "modules.load.vendor_kernel_boot").read_text()
    recovery_rows = [line.strip() for line in recovery.splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
    if not recovery_rows:
        fail("no vendor recovery module list")

    all_names = {Path(x).name for arr in modules.values() for x in arr}
    recovery_names = {Path(x).name for x in recovery_rows}
    missing_in_manifests = sorted(set(shiba) - all_names)
    missing_in_recovery = sorted(set(shiba) - recovery_names)
    boot = boot_check(args.boot)
    counts = {name: {"entries": len(rows),
                     "distinct_basenames": len({Path(x).name for x in rows})}
              for name, rows in modules.items()}

    with (args.out / "U11_MODULE_INVENTORY.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("role", "module_path", "module_basename",
                         "shiba_board_load", "husky_board_load"))
        for role, rows in modules.items():
            for item in rows:
                base = Path(item).name
                writer.writerow((role, item, base, base in shiba, base in husky))

    outcome = {
        "status": "PASS_METADATA_AUDIT_BINARY_KMI_UNKNOWN",
        "source_commits": pins,
        "kernel_target_from_source": "6.1",
        "driver_ko_binaries_in_source_repo": 0,
        "actual_vermagic_available": False,
        "module_sha256_available": False,
        "role_manifest_counts": counts,
        "ordered_common_manifest_equal_vendor_kernel_boot": True,
        "shiba_specific_modprobe": shiba,
        "husky_specific_modprobe": husky,
        "shiba_only": sorted(set(shiba) - set(husky)),
        "husky_only": sorted(set(husky) - set(shiba)),
        "shiba_names_not_in_any_manifest": missing_in_manifests,
        "shiba_names_not_in_recovery_vendor_kernel_boot": missing_in_recovery,
        "recovery_module_list_entries": len(recovery_rows),
        "experimental_u7_boot": boot,
        "installed_phone_build_fingerprint": "NOT_OBSERVED",
        "installed_phone_kernel_vendor_module_vermagic": "NOT_OBSERVED",
        "pixel8_bootable": False,
        "flashable": False,
        "physical_phone_modified": False,
    }
    (args.out / "U11_AUDIT.json").write_text(
        json.dumps(outcome, indent=2) + "\n")
    lines = [
        "# U11 — shiba kernel and vendor module integration audit",
        "",
        "**STATIC SOURCE/MANIFEST AUDIT PASS; BINARY ABI NOT PROVEN.**",
        "",
        "## Public source pins",
    ]
    lines += ["- " + key + ": " + pin for key, pin in pins.items()]
    lines += [
        "- Evolution X Android16 shiba device tree declares Linux 6.1.",
        "- It depends on the lineage-23.2 shusky kernel *manifest* repository.",
        "- That public repository contains ZERO actual .ko drivers or .img firmware.",
        "",
        "## Module list sizes (not installed driver counts)",
    ]
    lines += ["- " + role + ": " + str(c["entries"]) for role, c in counts.items()]
    lines += [
        "- The common modules.load and vendor_kernel_boot.modules.load have "
        "identical order and content.",
        "",
        "## shiba vs husky board-specific startup modules",
        "- shiba: " + ", ".join(shiba),
        "- husky: " + ", ".join(husky),
        "- shiba only: " + ", ".join(outcome["shiba_only"]),
        "- husky only: " + ", ".join(outcome["husky_only"]),
        "- shiba named drivers absent from public manifests: " +
        (", ".join(missing_in_manifests) if missing_in_manifests else "none"),
        "- shiba named drivers absent from recovery module list: " +
        (", ".join(missing_in_recovery) if missing_in_recovery else "none"),
        "",
        "## Existing U7 experimental kernel proof",
        "- Android boot header v4, kernel bytes: " + str(boot["kernel_bytes"]),
        "- U7 kernel SHA256: " + U7_KERNEL_SHA,
        "- No matching ROM vendor module binaries or modversion proof available.",
        "",
        "## Hard stop",
        "- Actual installed Evolution X Android16 fingerprint/vendor modules unknown.",
        "- Matching filenames or kernel 6.1 alone do NOT prove binary compatibility.",
        "- Pixel 8 Pro husky firmware is NOT interchangeable with Pixel 8 shiba.",
        "- QEMU Linux 6.6.89 is NOT a Tensor G3 firmware kernel.",
        "- No new bootable image. No flash, ADB or device access.",
        "",
        "**BUILD ONLY — PHONE FLASH READINESS: FALSE.**",
    ]
    (args.out / "U11_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
