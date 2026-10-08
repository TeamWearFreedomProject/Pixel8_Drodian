#!/usr/bin/env python3
"""Generate an inert, build-only Pixel 8 shiba research adaptation .deb.

This contains documentation and machine-readable research metadata ONLY.
It intentionally installs no boot images, modules, services, udev files,
system configuration, firmware, or pre/post installation scripts.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

PKG = "adaptation-google-shiba-research"
VERSION = "0.1.0"
README = """Pixel 8 shiba — UNVERIFIED research adaptation
================================================

This Debian arm64 package is NOT a functional Droidian device adaptation.
It contains only porting research data and makes no runtime changes.

Evidence:
- Phase 4 Google shusky source-GKI kernel compilation succeeded and
  confirmed 8 requested Kconfig settings.
- Phase 5 Debian trixie arm64 minbase rootfs compiled successfully.
- Phase 6 Droidian signed repository was unavailable during CI; its
  GitHub image inventory had NO shiba image or Android API 34 generic image.

UNRESOLVED before even considering actual Pixel 8 boot:
- Exact Google kernel source / stock vendor KMI and module ABI pairing
- Android 17 vendor ↔ Halium integration and GSI compatibility
- Complete Droidian arm64 userspace plus Phosh
- shiba-specific initramfs, LXC container, display and device modules
- Split boot partition layout and recovery strategy
- Verified hardware behavior, backups and safe recovery prerequisites

No permission to flash this or any other build artifact is implied.
Do not install on a phone. This is for disposable CI rootfs only.

Source repository: https://github.com/TeamWearFreedomProject/Pixel8_Drodian
"""
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dest = args.output_dir.resolve() / f"{PKG}_{VERSION}_arm64.deb"
    status = {
        "schema_version": 1,
        "identity": {"vendor": "google", "product": "Pixel 8", "codename": "shiba",
                     "architecture": "arm64", "soc_family": "zuma"},
        "project": "TeamWearFreedomProject/Pixel8_Drodian",
        "type": "research_only_not_installable_on_phone",
        "research_base": "android-gs-shusky-6.1-android16",
        "phase4_evidence": {
            "run_id": 37728429488,
            "compiled_halium_options": [
                "CONFIG_DEVTMPFS", "CONFIG_IPC_NS", "CONFIG_PID_NS",
                "CONFIG_SQUASHFS", "CONFIG_SYSVIPC", "CONFIG_USER_NS",
                "CONFIG_UTS_NS", "CONFIG_VT"
            ],
            "boot_tested": False
        },
        "phase5_evidence": {
            "run_id": 37760550966,
            "debian_rootfs_built": True,
            "droidian_rootfs_built": False
        },
        "compatibility_gate": {
            "shiba_kernel_vendor_kmi_verified": False,
            "android17_halium_compatibility_verified": False,
            "working_droidian_arm64_rootfs": False,
            "device_adaptation_functional": False,
            "pixel8_split_boot_layout_validated": False,
            "safe_to_flash": False
        },
        "contents": "inert research metadata only; no active system changes"
    }
    with tempfile.TemporaryDirectory(prefix="shiba-research-") as td:
        root = Path(td)
        ctrl = root / "DEBIAN"
        ctrl.mkdir()
        (ctrl / "control").write_text(
            f"Package: {PKG}\n"
            f"Version: {VERSION}\n"
            "Section: misc\n"
            "Priority: optional\n"
            "Architecture: arm64\n"
            "Maintainer: TeamWearFreedomProject <noreply@github.com>\n"
            "Description: Pixel 8 shiba Droidian porting metadata (NOT FUNCTIONAL)\n"
            " Inert research data for CI verification only.\n"
            " NOT an actual device adaptation and NOT safe to flash.\n",
            encoding="utf-8")
        data = root / "usr/share/droidian-porting/shiba"
        data.mkdir(parents=True)
        (data / "port-status.json").write_text(
            json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        docs = root / "usr/share/doc" / PKG
        docs.mkdir(parents=True)
        (docs / "README").write_text(README, encoding="utf-8")
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group",
                        str(root), str(dest)], check=True)
    if not dest.is_file() or dest.stat().st_size < 500:
        raise ValueError("Expected nonempty Debian research package")
    print(f"Built: {dest} ({dest.stat().st_size} bytes)")
    print("This is NOT a bootable image nor a functional Droidian adaptation.")

if __name__ == "__main__":
    main()
