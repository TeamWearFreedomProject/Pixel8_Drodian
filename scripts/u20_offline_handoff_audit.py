#!/usr/bin/env python3
"""U20: read-only, offline three-part *research* handoff integration gate.

This validates existing U6 ext4 rootfs + U8 initramfs + U18 generic GKI
and the U19 module compatibility verdict. It is NOT a Pixel 8 boot package.
No mount, loop, phone, block writes, partition selection, or boot image pack.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

PINS = {
    "U6_rootfs": "d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e",
    "U8_initramfs": "dc50919b6a4e89dc8c27d84dee5335105c756573ef3dcf74c3465a414e50372b",
    "U18_GKI_Image": "384f1aca6a5b040a7f0fe6d3ff5f39b8813256827bf0b2f622126b2eb6d0386c",
}
STOCK_CP2A = "6.1.157-android14-11-gbd23337e42e7-ab14791245"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tool(*argv, cwd=None, input_bytes=None):
    p = subprocess.run(
        argv, cwd=cwd, input=input_bytes, capture_output=True, check=True
    )
    return p.stdout


def read_ext4(image):
    with image.open("rb") as f:
        f.seek(1024 + 56)
        if f.read(2) != bytes.fromhex("53ef"):
            raise RuntimeError("U6 rootfs missing ext4 superblock magic")
        f.seek(1024 + 120)
        label = f.read(16).split(b"\0", 1)[0]
    if label != b"SHIBA_UBUNTU":
        raise RuntimeError(f"Unexpected offline ext4 label {label!r}")
    osinfo = tool("debugfs", "-R", "cat /usr/lib/os-release", str(image)).decode(
        "utf-8", "replace"
    )
    if "VERSION_CODENAME=resolute" not in osinfo or "ID=ubuntu" not in osinfo:
        raise RuntimeError("Offline U6 ext4 is not Ubuntu Resolute")
    for entry in ("usr/lib/systemd/systemd", "usr/bin/labwc", "usr/bin/phoc"):
        stat = tool("debugfs", "-R", "stat /" + entry, str(image)).decode(
            "utf-8", "replace"
        )
        if "Inode:" not in stat:
            raise RuntimeError(f"Missing rootfs inode {entry}")
    return {"label": "SHIBA_UBUNTU", "ubuntu_release": "26.04/resolute",
            "systemd_labwc_phoc_files_present": True}


def read_initramfs(ramdisk, expected_init, require_static_probe=False):
    decompressed = tool("lz4", "-dc", str(ramdisk))
    entries = tool("cpio", "-it", "--quiet", input_bytes=decompressed).decode(
        "utf-8", "replace"
    ).splitlines()
    names = set(x.removeprefix("./") for x in entries)
    required = {"init", "bin/busybox"}
    if require_static_probe:
        required.add("bin/u8-rootfs-probe")
    if not required.issubset(names):
        raise RuntimeError("First-stage initramfs missing: " + str(required-names))
    # The U8 archive was made before /init was revised to require the static
    # filesystem UUID helper. U20 MUST repack from the current reviewed source
    # and validate THAT new initramfs, not silently pass the obsolete archive.
    init_bytes = b""
    for name in ("init", "./init"):
        p = subprocess.run(["cpio", "-i", "--to-stdout", name],
                           input=decompressed, capture_output=True)
        if p.returncode not in (0, 1):
            raise RuntimeError("cpio init extraction failed: " + p.stderr.decode(
                "utf-8", "replace"))
        if p.stdout:
            init_bytes = p.stdout
            break
    if init_bytes != expected_init.read_bytes():
        raise RuntimeError("Rebuilt U20 /init does NOT match reviewed current source")
    if require_static_probe:
        probe_bytes = b""
        for name in ("bin/u8-rootfs-probe", "./bin/u8-rootfs-probe"):
            p = subprocess.run(["cpio", "-i", "--to-stdout", name],
                               input=decompressed, capture_output=True)
            if p.stdout:
                probe_bytes = p.stdout
                break
        if not (len(probe_bytes) >= 128 and probe_bytes[:4] == b"\x7fELF" and
                int.from_bytes(probe_bytes[18:20], "little") == 183):
            raise RuntimeError("U20 static UUID helper is not an AArch64 ELF binary")
    script = init_bytes.decode("utf-8")
    for marker in ("u8.rootuuid=", "u8.research_gate=I_UNDERSTAND_THIS_IS_UNVERIFIED",
                   "mount -t ext4 -o ro,noload", "switch_root /newroot /sbin/init"):
        if marker not in script:
            raise RuntimeError("Missing guarded rootfs-handoff marker: " + marker)
    # The actual first stage is not executed. Check shell grammar.
    tool("sh", "-n", str(expected_init))
    return {"file_entries": len(names), "init_matches_prior_reviewed_script": True,
            "boot_procedure_executed": False,
            "rootfs_uuid_mapping_on_physical_shiba": "NOT_VERIFIED"}


def gki_release(image):
    with image.open("rb") as f:
        previous = b""
        while True:
            block = f.read(2*1024*1024)
            if not block:
                break
            m = re.search(rb"Linux version (6\.1\.[0-9]+-[^\x00\s]+)", previous+block)
            if m:
                return m.group(1).decode("ascii")
            previous = block[-512:]
    raise RuntimeError("U18 GKI kernel Image has no Linux version banner")


def main():
    p = argparse.ArgumentParser()
    for arg in ("rootfs", "ramdisk", "rebuilt", "gki", "u19", "u18report", "sourceinit", "out"):
        p.add_argument("--" + arg, type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    paths = {"U6_rootfs": a.rootfs, "U8_initramfs": a.ramdisk,
             "U18_GKI_Image": a.gki}
    observed = {name: sha256(path) for name, path in paths.items()}
    for name, expected in PINS.items():
        if observed[name] != expected:
            raise RuntimeError(f"U20 source artifact SHA mismatch: {name}")
    if a.rootfs.stat().st_size != 2147483648:
        raise RuntimeError("U6 rootfs is not the verified 2GiB ext4 research image")
    u19 = json.loads(a.u19.read_text(encoding="utf-8"))
    u18 = json.loads(a.u18report.read_text(encoding="utf-8"))
    if u19["real_device_flash_gate"] != "DENY" or u19[
            "safe_to_combine_U17_modules_with_U18_GKI"]:
        raise RuntimeError("U19 safe integration veto missing")
    if u18["real_device_flash_gate"] != "DENY":
        raise RuntimeError("U18 verified boot gate missing")

    fs = read_ext4(a.rootfs)
    # The U8 original is retained for provenance, and used as an input to
    # generate the new reviewed U20 initramfs. Its obsolete /init is NOT used.
    handoff = read_initramfs(a.rebuilt, a.sourceinit,
                             require_static_probe=True)
    rebuilt_sha = sha256(a.rebuilt)
    release = gki_release(a.gki)
    if not release.startswith("6.1.157-android14-11-"):
        raise RuntimeError("U18 research GKI not based on CP2A's 6.1.157 family")
    result = {
        "status": "U20_OFFLINE_ASSET_INTEGRITY_AND_INIT_HANDOFF_AUDIT_PASS",
        "rootfs_source_run": 38047914957,
        "initramfs_source_run": 38052743722,
        "gki_source_run": 38101661379,
        "u19_abi_audit_run": 38103774760,
        "part_sha256": observed,
        "new_U20_rebuilt_guarded_initramfs_sha256": rebuilt_sha,
        "historical_U8_init_stale_replaced_with_reviewed_source": True,
        "U20_static_AArch64_uuid_probe_included": True,
        "rootfs": fs,
        "handoff": handoff,
        "built_gki_kernel_release": release,
        "stock_cp2a_kernel_release": STOCK_CP2A,
        "built_kernel_release_identical_to_cp2a": release == STOCK_CP2A,
        "actual_kernel_plus_initramfs_qemu_boot_tested_this_stage": False,
        "ubuntu_systemd_boot_on_real_phone": False,
        "real_shiba_driver_module_compatibility_verified": False,
        "real_shiba_drm_touch_wifi_usb_verified": False,
        "android_verified_boot_signature_and_rollback_verified": False,
        "reusable_parts_after_future_kmi_vendor_fix": ["U6 ext4 data", "U8 gated first-stage design"],
        "physical_pixel8_modified": False,
        "boot_img_or_init_boot_partition_image_created": False,
        "user_data_or_partitions_erased": False,
        "real_device_flash_gate": "DENY",
    }
    (a.out / "U20_OFFLINE_INTEGRATION.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    rows = [
        "# U20 — Ubuntu 26.04 ARM64 rootfs + guarded handoff + pinned GKI",
        "",
        "**OFFLINE INTEGRITY AUDIT PASSED; NO PIXEL 8 BOOT IMAGE; DO NOT FLASH.**",
        "",
        "| Research part | Verified SHA256 |",
        "| --- | --- |",
    ] + [f"| {key} | `{value}` |" for key, value in observed.items()] + [
        "",
        f"- Offline ext4: `{fs['label']}`, Ubuntu {fs['ubuntu_release']}, 2 GiB.",
        "- systemd, Labwc and Phoc entries verified in offline ext4 image.",
        f"- New U20 guarded ARM64 initramfs entries: {handoff['file_entries']} (current source init byte-for-byte match).",
        f"- Newly rebuilt U20 ramdisk SHA256: `{rebuilt_sha}`.",
        "- Historical U8 packed /init was found stale in Run #1 and was REPLACED;",
        "  this run checks the reviewed current /init plus newly compiled static AArch64 UUID probe.",
        "- Guard requires explicit root UUID and research-gate token; no guessed Android partitions.",
        "- Designed ext4 access is read-only with no journal replay; actual mount and switch_root were **NOT RUN**.",
        f"- U18 GKI compiled kernel: `{release}`.",
        f"- Phone CP2A stock kernel: `{STOCK_CP2A}`.",
        "- U19 vendor modules remain built for older 6.1.124; KMI/symbols/panel not validated.",
        "",
        "## Hard stop",
        "**REAL DEVICE FLASH GATE: DENY.** This phase creates reports only,",
        "not a flashable boot/init_boot/userdata image.",
        "The parts can be associated by SHA256 but **have not booted together**",
        "on Pixel hardware or as this exact combination in a VM.",
        "No physical phone access, slot change, bootloader write, or formatting occurred.",
    ]
    (a.out / "U20_OFFLINE_INTEGRATION.md").write_text("\n".join(rows) + "\n")
    (a.out / "U20_RESEARCH_PARTS_SHA256.txt").write_text(
        "\n".join(f"{observed[k]}  {k}" for k in paths) +
        f"\n{rebuilt_sha}  U20_rebuilt_guarded_initramfs\n"
    )
    print("\n".join(rows))


if __name__ == "__main__":
    main()
