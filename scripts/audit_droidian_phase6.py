#!/usr/bin/env python3
"""Inspect official Droidian rootfs recipes for Pixel 8 shiba porting."""
import argparse
import subprocess
from pathlib import Path
import yaml

def revision(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    images = args.sources / "droidian-images"
    templates = args.sources / "rootfs-templates"
    gsi = args.sources / "android-system-gsi-34-bin"
    for path in (images, templates, gsi):
        if not (path / ".git").is_dir():
            raise ValueError(f"Source checkout missing: {path}")
    devices = yaml.safe_load((images / "devices.yml").read_text(encoding="utf-8"))
    apis = devices["rootfs"]["apilevel"]
    if not isinstance(apis, list):
        apis = [apis]
    base = (templates / "recipes/droidian_base.yaml").read_text(encoding="utf-8")
    phosh = (templates / "droidian_phosh.yaml").read_text(encoding="utf-8")
    gsi_recipe = (templates / "droidian_gsi_base.yaml").read_text(encoding="utf-8")
    control = (gsi / "debian/control").read_text(encoding="utf-8")
    keyring = templates / "apt/etc/apt/trusted.gpg.d/droidian-bootstrap.gpg"
    if not keyring.is_file() or keyring.stat().st_size < 500:
        raise ValueError("No plausible upstream Droidian GPG bootstrap key")
    checks = {
        "Droidian snapshot mirror": "releases.droidian.org/snapshots/" in base,
        "Droidian base metapackage": "droidian-base" in base,
        "Droidian Phosh metapackage": "droidian-phosh-full" in phosh,
        "Halium API specific dependency": "adaptation-hybris-api" in gsi_recipe,
        "Android 14 GSI 34 packaging source": "Package: android-system-gsi-34" in control,
    }
    if not all(checks.values()):
        raise ValueError(f"Unexpected missing official packaging dependency: {checks}")
    lines = [
        "# Phase 6 — Droidian ARM64 userspace audit",
        "",
        "**BUILD ONLY — NOT FLASHABLE — PIXEL 8 UNVERIFIED**",
        "",
        "## Official source commits",
        "",
        f"- Droidian images: `{revision(images)}`",
        f"- Rootfs templates: `{revision(templates)}`",
        f"- Android 14 GSI packaging: `{revision(gsi)}`",
        "",
        f"- Generic Android API versions: `{apis}`",
        f"- Android API 34 listed in generic images: **{34 in apis}**",
        f"- Upstream bootstrap GPG key present: **{keyring.stat().st_size} bytes**",
        "",
        "## Packaging components",
        "",
    ]
    lines.extend(f"- {name}: **{value}**" for name,value in checks.items())
    lines.extend([
        "",
        "## Next technical blockers",
        "",
        "1. Android 17 vendor / Halium-GSI compatibility is not proven.",
        "2. A working shiba-specific Droidian adaptation does not exist in this project.",
        "3. Source-built Google shusky kernel KMI/ABI with device vendor modules is unverified.",
        "4. Droidian base userspace alone does not have Phosh, Halium, or Pixel 8 boot images.",
        "",
        "**Never flash anything from this workflow.**",
        "",
    ])
    output = "\n".join(lines)
    args.output.write_text(output, encoding="utf-8")
    print(output)

if __name__ == "__main__":
    main()
