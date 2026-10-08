#!/usr/bin/env python3
"""Build-only Droidian/Halium readiness audit for Pixel 8 shiba.

The script inspects PUBLIC upstream source snippets and an optional compiled
Google kernel .config. It never builds boot firmware or modifies a device.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def read_config(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        enabled = re.match(r"^(CONFIG_[A-Z0-9_]+)=(.*)$", line)
        disabled = re.match(r"^# (CONFIG_[A-Z0-9_]+) is not set$", line)
        if enabled:
            result[enabled.group(1)] = enabled.group(2)
        elif disabled:
            result[disabled.group(1)] = "n"
    return result


def revision(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def parse_mk(content: str, key: str) -> str:
    match = re.search(r"^" + re.escape(key) + r"\s*=\s*(.*?)\s*$", content, re.M)
    return match.group(1) if match else "(not found)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--config", type=Path)
    ap.add_argument("--output", type=Path, default=Path("halium-report.md"))
    args = ap.parse_args()

    fragments = args.sources / "common_fragments"
    packaging = args.sources / "linux-android-common-6.1-android14"
    gsi = args.sources / "android-system-gsi-34-bin"

    for path in (fragments, packaging, gsi):
        if not (path / ".git").exists():
            raise SystemExit(f"Missing upstream source checkout: {path}")

    info = (packaging / "debian/android-kernel-info.mk").read_text(encoding="utf-8")
    settings = (packaging / "debian/kernel-info.mk").read_text(encoding="utf-8")
    upstream_ver = ".".join(parse_mk(info, k) for k in ("VERSION", "PATCHLEVEL", "SUBLEVEL"))

    requirements = {}
    for name in ("halium.config", "droidian.config", "container.config"):
        fragment = read_config(fragments / name)
        for key, value in fragment.items():
            if key in requirements and requirements[key][0] != value:
                raise SystemExit(f"Conflicting upstream requirements: {key}")
            requirements[key] = (value, name)

    actual = read_config(args.config) if args.config else None
    if args.config and not args.config.is_file():
        raise SystemExit(f"Missing built .config: {args.config}")

    rows = []
    counts = {"MATCH": 0, "DIFF": 0, "UNKNOWN": 0}
    for key, (expected, source) in sorted(requirements.items()):
        got = "(not inspected)" if actual is None else actual.get(key, "(absent)")
        verdict = "UNKNOWN" if actual is None else ("MATCH" if got == expected else "DIFF")
        counts[verdict] += 1
        rows.append(f"| \`{key}\` | \`{expected}\` | \`{got}\` | {verdict} | \`{source}\` |")

    lines = [
        "# Pixel 8 (shiba) — Droidian/Halium compatibility audit",
        "",
        "**BUILD ONLY — NO FLASH — NOT A WORKING DROIDIAN PORT**",
        "",
        "## Upstream inputs (exact commits)",
        "",
        f"- Droidian 6.1 configuration fragments: \`{revision(fragments)}\`",
        f"- Droidian Android 14 GKI Debian packaging: \`{revision(packaging)}\`",
        f"- Droidian Android 14 GSI package: \`{revision(gsi)}\`",
        "",
        "## Key observations",
        "",
        f"- Droidian GKI package kernel version recorded upstream: **{upstream_ver}**.",
        "- Uploaded factory reference: **CP3A.260905.009**, kernel **6.1.162-android14-11**.",
        "- The upstream 6.1 GKI packaging is generic. It is NOT a Pixel 8 device adaptation.",
        "- Source branch and factory kernel remain unverified for an exact build match.",
        "- Android 14 GSI package existence does NOT prove it works with Pixel 8 Android 17 vendor blobs.",
        f"- Droidian generic packaging boot-header setting: \`{parse_mk(settings, 'KERNEL_BOOTIMAGE_VERSION')}\`.",
        f"- Droidian generic packaging FLASH_ENABLED: \`{parse_mk(settings, 'FLASH_ENABLED')}\`.",
        "- Droidian runs Debian userspace and a minimal Android environment in an LXC container. LXC is not a VM, but it is a container.",
        "",
        "## Kernel configuration comparison",
        "",
        f"- Examined compiled Google kernel config: **{'YES' if actual is not None else 'NO — upstream-only audit'}**.",
        f"- MATCH: {counts['MATCH']}, DIFF: {counts['DIFF']}, UNKNOWN: {counts['UNKNOWN']}.",
        "",
        "| Config | Droidian requested | Google built config | Comparison | Fragment |",
        "| --- | --- | --- | --- | --- |",
        *rows,
        "",
        "**Interpretation:** DIFF means a configuration discrepancy to investigate, not automatic proof that the device is incompatible.",
        "Some upstream fragments intentionally request security-related or packaging-specific changes;",
        "do not apply them automatically. For example, disabling SELinux or module signature enforcement",
        "requires careful security review. In particular, the built vendor and GKI must remain mutually compatible.",
        "",
        "## Remaining blockers",
        "",
        "1. Identify or create a valid shiba-specific Droidian/Halium adaptation package.",
        "2. Verify vendor/Halium compatibility against the actual Android 17 device image.",
        "3. Plan Pixel 8 split boot/init_boot/vendor_boot/vendor_kernel_boot layouts and verified boot.",
        "4. Package a test rootfs only when device adaptation dependencies are clear.",
        "",
        "No artifact from this workflow is intended to be flashed or booted.",
        "",
    ]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(args.output.read_text(encoding="utf-8")[:9000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
