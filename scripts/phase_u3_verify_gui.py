#!/usr/bin/env python3
"""Check a disposable Ubuntu 26.04 ARM64 rootfs for two GUI package sets.

This script only inspects the rootfs and adds research-only session metadata.
It does not create boot images or attempt to access a phone or a display.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

PACKAGES = (
    "phosh", "phoc", "phosh-osk-stevia",
    "labwc", "waybar", "foot", "kanshi", "xwayland", "dbus-user-session"
)
BINARIES = ("phoc", "labwc", "waybar", "foot", "kanshi")
DESKTOP_ENTRY = """[Desktop Entry]
Name=Ubuntu U3 Labwc Desktop (research)
Comment=Manual external-desktop candidate; not configured for automatic switching
Exec=labwc
TryExec=labwc
Type=Application
DesktopNames=labwc
"""


def read_dpkg_status(root):
    status = root / "var/lib/dpkg/status"
    if not status.is_file():
        raise RuntimeError("no dpkg status in rootfs")
    installed = {}
    for stanza in status.read_text(errors="replace").split("\n\n"):
        fields = {}
        for line in stanza.splitlines():
            if ": " in line and not line.startswith((" ", "\t")):
                key, value = line.split(": ", 1)
                fields[key] = value
        if fields.get("Status") == "install ok installed" and fields.get("Package"):
            installed[fields["Package"]] = {
                "version": fields.get("Version"),
                "architecture": fields.get("Architecture")
            }
    return installed


def file_is_arm64_elf(path):
    if not path.is_file():
        return False
    with path.open("rb") as f:
        h = f.read(20)
    if len(h) < 20 or h[:4] != b"\x7fELF" or h[4] != 2:
        return False
    order = "<" if h[5] == 1 else ">" if h[5] == 2 else None
    return bool(order and struct.unpack_from(order + "H", h, 18)[0] == 183)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root, out = args.root, args.out
    out.mkdir(parents=True, exist_ok=True)
    release = (root / "etc/os-release").read_text(errors="replace")
    if "VERSION_CODENAME=resolute" not in release:
        raise SystemExit("FAIL: not Ubuntu resolute")
    installed = read_dpkg_status(root)
    missing = [name for name in PACKAGES if name not in installed]
    if missing:
        raise SystemExit("FAIL: missing required packages: " + ", ".join(missing))
    wrong = [name for name in PACKAGES
             if installed[name]["architecture"] not in ("arm64", "all")]
    if wrong:
        raise SystemExit("FAIL: wrong installed architecture: " + ", ".join(wrong))
    binary_results = {
        name: file_is_arm64_elf(root / "usr/bin" / name) for name in BINARIES
    }
    missing_bins = [name for name, good in binary_results.items() if not good]
    if missing_bins:
        raise SystemExit("FAIL: missing/non-arm64 ELF: " + ", ".join(missing_bins))

    desktop = root / "usr/share/wayland-sessions/shiba-u3-labwc.desktop"
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(DESKTOP_ENTRY)

    policy = {
        "status": "BUILD_ONLY_NO_HARDWARE_TEST",
        "target": "Google Pixel 8 (shiba)",
        "current_phone_os_at_report": "Evolution X Android 16 (user-reported)",
        "reference_vendor_firmware": "older Android 17 CP3A.260905.009 (not current ROM)",
        "phone_session": "Phosh + Phoc Wayland mobile UI",
        "on_screen_keyboard": "phosh-osk-stevia",
        "desktop_session": "Labwc + Waybar + Foot",
        "desktop_selection": "Manual session entry; not automatic plug-in switching",
        "hotplug_automatic_mode_switching": False,
        "external_display_hardware_tested": False,
        "gpu_acceleration_tested": False,
        "touchscreen_tested": False,
        "bootable_phone_firmware": False,
        "safety": "DO NOT FLASH. No ADB or fastboot, no hardware test.",
    }
    cfg = root / "etc/shiba-u3/session-research.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n")

    results = {"status": "PASS_PACKAGE_AND_ARCH_METADATA_ONLY",
               "target": "arm64 Ubuntu 26.04 resolute",
               "package_versions": {p: installed[p] for p in PACKAGES},
               "arm64_elf_binaries": binary_results,
               "desktop_session_entry": "/usr/share/wayland-sessions/shiba-u3-labwc.desktop",
               "limitations": policy}
    (out / "U3_METADATA.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = [
        "# Ubuntu Phase U3: ARM64 touch + desktop userspace research",
        "",
        "**PASS: packages installed and basic architecture metadata verified**",
        "",
        "## Two candidate sessions",
        "- **Phone:** Phosh + Phoc + Stevia touch keyboard.",
        "- **Desktop:** Labwc + Waybar + Foot, with Kanshi available for future monitor policy.",
        "",
        "## Verified packages (dpkg: install ok installed, arm64/all)",
    ]
    for package in PACKAGES:
        info = installed[package]
        lines.append("- {}: {} ({})".format(package, info["version"], info["architecture"]))
    lines += [
        "",
        "## Architecture checks",
        "- All {} inspected executable ELF headers identify AArch64 (machine 183).".format(len(BINARIES)),
        "- Phosh is validated by installed arm64 package metadata, not an assumed /usr/bin/phosh ELF path.",
        "- The image includes a manual Labwc Wayland session descriptor.",
        "- Phosh session packages are installed; graphical startup was NOT attempted.",
        "",
        "## NOT demonstrated",
        "- No real Wayland/DRM session, touchscreen or GPU hardware test.",
        "- No USB-C external display or monitor hotplug test.",
        "- No automatic switching from mobile UI to desktop on cable insertion.",
        "- No Pixel 8 boot support, modem/telephony, power management or ABI compatibility.",
        "- User's current Evolution X Android 16 installation is NOT the earlier Android 17 vendor sample.",
        "- No firmware, Android partitions, ADB, fastboot or flashing operations.",
        "",
        "**UNVERIFIED FOR HARDWARE — BUILD ONLY — NOT BOOTABLE — DO NOT FLASH**"
    ]
    (out / "U3_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
