#!/usr/bin/env python3
"""U5: OFFLINE rootfs archive and Evolution X bka source metadata inspection.

Never accesses a Pixel device, extracts files, mounts partitions, or emits
boot/flashable images. The initramfs contract is metadata only.
"""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

U3_SHA = "40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a"
PINNED = {
    "shusky": "56006ae8162db285e776d85319d9942945b87194",
    "zuma": "fba447c6317f23501dbac209b6479e458800c449"
}
REQUIRED = ("phosh", "phoc", "phosh-osk-stevia", "labwc", "waybar",
            "foot", "kanshi", "xwayland", "dbus-user-session")
PATTERNS = [
    ("shusky", "device-shiba.mk",
     ["TARGET_LINUX_KERNEL_VERSION := 6.1",
      "TARGET_KERNEL_DEVICE := shusky",
      "include device/google/zuma/common.mk"]),
    ("shusky", "evolution.dependencies",
     ["LineageOS/android_device_google_shusky-kernels", "lineage-23.2"]),
    ("shusky", "BoardConfigCommon.mk",
     ["BOARD_VENDOR_KERNEL_RAMDISK_KERNEL_MODULES_LOAD_RAW",
      "BOARD_VENDOR_KERNEL_RAMDISK_KERNEL_MODULES"]),
    ("shusky", "recovery/modules.load.vendor_kernel_boot",
     ["goog_touch_interface.ko", "ftm5.ko", "goodix_brl_touch.ko"]),
    ("zuma", "BoardConfig-common.mk",
     ["TARGET_RECOVERY_FSTAB_GENRULE := gen_fstab.zuma-sw-encrypt",
      "AB_OTA_UPDATER := true",
      "BOARD_PREBUILT_BOOTIMAGE",
      "TARGET_USERIMAGES_USE_F2FS := true",
      "TARGET_USERIMAGES_USE_EXT4 := true"])
]
BLOCKERS = [
    "Exact installed Android 16 Evolution X kernel and vendor KMI are unknown.",
    "No tested Pixel 8 shiba Linux boot image or initramfs exists.",
    "No independently identified, safely isolated Linux root filesystem volume.",
    "Android userdata is not spare disk space; replacement can destroy Android data.",
    "GPU, display, touchscreen, external USB-C output and power remain unverified.",
    "No reviewed rescue/rollback or boot-ready firmware integration."
]


def reject(why):
    raise SystemExit("U5 FAILED CLOSED: " + why)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(buf)
    return value.hexdigest()


def source_check(base):
    revisions, evidence = {}, []
    for name, expected in PINNED.items():
        actual = subprocess.check_output(
            ["git", "-C", str(base / name), "rev-parse", "HEAD"],
            text=True).strip()
        if actual != expected:
            reject("upstream commit mismatch: " + name)
        revisions[name] = actual
    for name, file, terms in PATTERNS:
        p = base / name / file
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        hits = []
        for term in terms:
            pos = next((i for i, line in enumerate(lines, 1) if term in line), None)
            if pos is None:
                reject("source marker missing: " + str(p) + ": " + term)
            hits.append({"line": pos, "marker": term})
        evidence.append({"source": name, "path": file, "markers": hits,
                         "sha256": sha(p)})
    deps = json.loads((base / "shusky" / "evolution.dependencies").read_text())
    kdep = [x for x in deps if "kernel" in x.get("repository", "").lower()]
    if not kdep:
        reject("no current source tree kernel dependency declared")
    return revisions, evidence, kdep


def installed(status):
    package_map = {}
    for block in status.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ": " in line and not line.startswith((" ", "\t")):
                key, val = line.split(": ", 1)
                fields[key] = val
        if fields.get("Status") == "install ok installed":
            name = fields.get("Package")
            if name:
                package_map[name] = {
                    "version": fields.get("Version"),
                    "architecture": fields.get("Architecture")
                }
    return package_map


def inspect_u3(path):
    if sha(path) != U3_SHA:
        reject("U3 tarball did not match previously verified sha256")
    with tarfile.open(path, "r:xz") as archive:
        members, regular_bytes = {}, 0
        stats = {"files": 0, "directories": 0, "symlinks": 0}
        for item in archive:
            name = item.name
            while name.startswith("./"):
                name = name[2:]
            if not name:
                continue
            if name.startswith("/") or ".." in Path(name).parts:
                reject("suspicious archive member path: " + name)
            if name in members:
                reject("duplicate archive member: " + name)
            members[name] = item
            if item.isfile():
                stats["files"] += 1
                regular_bytes += item.size
            elif item.isdir():
                stats["directories"] += 1
            elif item.issym():
                stats["symlinks"] += 1

        def read_regular(key, limit):
            item = members.get(key)
            if item is None or not item.isfile() or item.size > limit:
                reject("required regular rootfs file missing: " + key)
            stream = archive.extractfile(item)
            if stream is None:
                reject("unable to read rootfs file: " + key)
            return stream.read(limit + 1).decode("utf-8", errors="replace")

        os_release = read_regular("usr/lib/os-release", 32768)
        if "VERSION_CODENAME=resolute" not in os_release:
            reject("unexpected Ubuntu release")
        packages = installed(read_regular("var/lib/dpkg/status", 15 * 1024 * 1024))
        gui = {}
        for package in REQUIRED:
            found = packages.get(package)
            if not found or found.get("architecture") not in ("arm64", "all"):
                reject("missing or wrong architecture GUI package: " + package)
            gui[package] = found
        policy = json.loads(read_regular("etc/shiba-u3/session-research.json", 65536))
        manual = read_regular("usr/share/wayland-sessions/shiba-u3-labwc.desktop", 65536)
        if "Exec=labwc" not in manual or policy.get("bootable_phone_firmware") is not False:
            reject("U3 nonbootable UI policy not present")
    return {
        "compressed_bytes": path.stat().st_size,
        "uncompressed_regular_file_payload_bytes": regular_bytes,
        "tar_member_count": len(members),
        "tar_member_types": stats,
        "ubuntu_release": "26.04 resolute",
        "architecture": "arm64",
        "gui_packages": gui,
        "manual_labwc_session": True,
        "hardware_bootability_proven": False,
    }


def contract():
    return {
        "schema": "u5-initramfs-mount-DESIGN-ONLY",
        "device": "shiba", "architecture": "arm64",
        "rootfs": {
            "kind": "separate_linux_volume_candidate",
            "filesystem_candidate": "ext4",
            "verified_partition_uuid": None,
            "android_userdata_can_be_overwritten": False,
            "proposed_first_mount": "read_only_if_proven_safe",
        },
        "initramfs": {
            "status": "NOT_IMPLEMENTED",
            "prerequisites": [
                "matching shiba kernel and device tree",
                "verified kernel module KMI",
                "verified root volume source and filesystem support",
                "fail-closed rootfs identity check",
                "reviewed init handoff and rollback",
            ],
        },
        "flashable": False, "bootable": False, "hardware_review_required": True,
    }


def contract_is_valid(obj):
    root = obj.get("rootfs", {})
    return (
        obj.get("device") == "shiba" and
        obj.get("architecture") == "arm64" and
        root.get("kind") == "separate_linux_volume_candidate" and
        root.get("filesystem_candidate") == "ext4" and
        root.get("verified_partition_uuid") is None and
        root.get("android_userdata_can_be_overwritten") is False and
        obj.get("flashable") is False and obj.get("bootable") is False and
        obj.get("hardware_review_required") is True
    )


def policy_tests(obj):
    tests = {"valid_inert_design": contract_is_valid(obj)}
    for key, wrong in (("device", "husky"), ("flashable", True),
                       ("hardware_review_required", False)):
        copy = json.loads(json.dumps(obj))
        copy[key] = wrong
        tests["reject_" + key] = not contract_is_valid(copy)
    copy = json.loads(json.dumps(obj))
    copy["rootfs"]["kind"] = "android_userdata"
    tests["reject_userdata_repurposing"] = not contract_is_valid(copy)
    copy = json.loads(json.dumps(obj))
    copy["rootfs"]["verified_partition_uuid"] = "UNVERIFIED"
    tests["reject_fabricated_volume_id"] = not contract_is_valid(copy)
    if not all(tests.values()):
        reject("offline design contract negative test failed")
    return tests


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--u3", required=True, type=Path)
    p.add_argument("--sources", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    revisions, evidence, deps = source_check(a.sources)
    data = inspect_u3(a.u3)
    design = contract()
    tests = policy_tests(design)
    output = {
        "result": "PASS_OFFLINE_U5_RESEARCH_NOT_READY_TO_FLASH",
        "device": "shiba",
        "current_phone_os_user_report": "Evolution X Android 16",
        "exact_installed_rom_build": "UNKNOWN",
        "rootfs_metadata": data,
        "upstream_revisions": revisions,
        "source_patterns": evidence,
        "kernel_dependency_declarations": deps,
        "initramfs_design": design,
        "design_mock_tests": tests,
        "blocking_issues": BLOCKERS,
    }
    (a.out / "U5_AUDIT.json").write_text(json.dumps(output, indent=2) + "\n")
    (a.out / "U5_INITRAMFS_CONTRACT.json").write_text(
        json.dumps(design, indent=2) + "\n")
    lines = [
        "# Ubuntu U5: rootfs and Android16 source compatibility gate",
        "",
        "**PASS offline audit; FAIL boot/flash readiness.**",
        "",
        "## Real U3 Ubuntu GUI rootfs",
        "- U3 SHA256 verification: PASS",
        "- tar.xz compressed bytes: " + str(data["compressed_bytes"]),
        "- Total uncompressed regular-file payload bytes: " +
        str(data["uncompressed_regular_file_payload_bytes"]),
        "- Regular files: " + str(data["tar_member_types"]["files"]),
        "- Directories: " + str(data["tar_member_types"]["directories"]),
        "- Symlinks: " + str(data["tar_member_types"]["symlinks"]),
        "- Ubuntu 26.04 ARM64 with " + str(len(REQUIRED)) + " verified GUI packages.",
        "",
        "## Current-source references, not exact installed ROM",
    ]
    for name, commit in revisions.items():
        lines.append("- " + name + " pinned commit: " + commit)
    lines += [
        "- Evolution X Android16 bka device tree: kernel 6.1; "
        "LineageOS shusky-kernels lineage-23.2 dependency.",
        "- Zuma Android tree: A/B boot-partition family; "
        "recovery fstab indicates Android storage/encryption assumptions.",
        "- User-installed build fingerprint and matching vendor module ABI: UNKNOWN.",
        "",
        "## Inert Linux boot architecture contract",
        "- Requires a separately verified Linux filesystem; no Android userdata overwrite.",
        "- Rootfs volume identifier is UNASSIGNED by design.",
        "- Device-specific initramfs does NOT yet exist.",
        "- " + str(len(tests)) + " offline fail-closed contract tests passed.",
        "",
        "## Barriers to native boot",
    ]
    lines += ["- " + item for item in BLOCKERS]
    lines += [
        "",
        "**NO DEVICE ACCESS, NO ADB/FASTBOOT, NO FLASHABLE IMAGE CREATED.**"
    ]
    (a.out / "U5_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
