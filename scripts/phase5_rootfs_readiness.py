#!/usr/bin/env python3
"""Source-based Droidian shiba rootfs readiness report.

This is a research report. Do not treat it as evidence of a bootable port.
"""
import argparse
from pathlib import Path
import subprocess
import yaml

def sha(directory):
    return subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()

def check(files):
    images = files / "droidian-images"
    templates = files / "rootfs-templates"
    gsi = files / "android-system-gsi-34-bin"
    for repo in (images, templates, gsi):
        if not (repo / ".git").is_dir():
            raise RuntimeError(f"Missing upstream source checkout: {repo}")
    devices = yaml.safe_load((images / "devices.yml").read_text())
    api = devices.get("rootfs", {}).get("apilevel", [])
    if not isinstance(api, list):
        api = [api]
    recipe = (templates / "droidian_gsi_base.yaml").read_text()
    control = (gsi / "debian/control").read_text()
    gsi_ok = "Package: android-system-gsi-34" in control
    hybris_referenced = "adaptation-hybris-api{{ $apilevel }}" in recipe
    gsi_referenced = "android-system-gsi-{{ $apilevel }}" in recipe
    output = [
        "# Pixel 8 shiba — Phase 5 rootfs dependency report",
        "",
        "**UNVERIFIED — BUILD ONLY — NOT A DROIDIAN IMAGE — NO FLASH**",
        "",
        "## Official source revisions",
        "",
        f"- Droidian images: `{sha(images)}`",
        f"- Droidian rootfs templates: `{sha(templates)}`",
        f"- Droidian Android 14 GSI packaging: `{sha(gsi)}`",
        "",
        "## Source-derived facts",
        "",
        f"- Listed generic Droidian rootfs Android API levels: `{', '.join(str(x) for x in api)}`",
        f"- API 34 present in generic devices.yml: **{'YES' if 34 in api else 'NO'}**",
        f"- The separate Android 14 GSI package declares `android-system-gsi-34`: **{'YES' if gsi_ok else 'NO'}**",
        f"- Template refers to `adaptation-hybris-api<API>`: **{'YES' if hybris_referenced else 'NO'}**",
        f"- Template refers to `android-system-gsi-<API>`: **{'YES' if gsi_referenced else 'NO'}**",
        "",
        "## Known blockers",
        "",
        "- Existing 8/8 Halium Kconfig success does not establish real-device boot.",
        "- A shiba-specific Droidian adaptation package does not yet exist in this project.",
        "- Correct vendor API / Halium userspace combination for the running Pixel 8 Android 17 firmware is unverified.",
        "- The presence of a GSI 34 source repository does NOT prove an appropriate",
        "  adaptation-hybris-api34 binary package is installed or compatible.",
        "- The official generic rootfs menu must not be taken as evidence of API 34 support",
        "  unless API 34 is actually listed by the sources checked here.",
        "- A Linux rootfs alone does not include a shiba-compatible Halium Android container,",
        "  display integration, kernel modules, initramfs, or Pixel split-boot images.",
        "",
        "## Phase 5 CI output",
        "",
        "The separate arm64 rootfs build, if selected and successful, is a genuine",
        "minimal Debian arm64 filesystem, **not** a complete Droidian distribution.",
        "It can be used to validate base-architecture packaging only.",
        "",
        "**No hardware commands, no patched firmware, no bootable image.**",
        "",
    ]
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.sources)
    args.output.write_text(result, encoding="utf-8")
    print(result)

if __name__ == "__main__":
    main()
