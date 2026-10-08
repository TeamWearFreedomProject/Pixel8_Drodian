#!/usr/bin/env python3
"""Audit a BUILD-ONLY Halium candidate .config against Phase 2 shusky baseline.

No kernel modification, signing changes, or device access.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re


def config(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r"(CONFIG_[A-Z0-9_]+)=(.*)", line)
        if m:
            result[m[1]] = m[2]
            continue
        m = re.fullmatch(r"# (CONFIG_[A-Z0-9_]+) is not set", line)
        if m:
            result[m[1]] = "n"
    if len(result) < 500:
        raise ValueError(f"Suspiciously small kernel .config: {path} ({len(result)} keys)")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    before, after = config(args.baseline), config(args.candidate)
    requested = config_fragment(args.fragment)
    lines = [
        "# Pixel 8 shiba: Halium kernel fragment experiment",
        "",
        "**UNVERIFIED — BUILD ONLY — DO NOT FLASH**",
        "",
        "This report compares the Pixel 8 shusky baseline and candidate",
        "kernel configurations produced by Google Kleaf. The candidate",
        "is not a boot-tested kernel and is not a Droidian image.",
        "",
        "| Setting | Phase 2 baseline | Candidate | Requested |",
        "| --- | --- | --- | --- |",
    ]
    failures = []
    for key, expected in sorted(requested.items()):
        old, actual = before.get(key, "(absent)"), after.get(key, "(absent)")
        lines.append(f"| `{key}` | `{old}` | `{actual}` | `{expected}` |")
        if actual != expected:
            failures.append(f"{key}: requested {expected}, received {actual}")

    lines.extend([
        "",
        f"Requested settings: **{len(requested)}**",
        f"Settings confirmed in candidate: **{len(requested)-len(failures)}**",
        f"Unmet requested settings: **{len(failures)}**",
        "",
        "## Security changes",
        "",
        f"- CONFIG_MODULE_SIG_PROTECT: {before.get('CONFIG_MODULE_SIG_PROTECT')} -> {after.get('CONFIG_MODULE_SIG_PROTECT')}",
        f"- CONFIG_MODULE_SIG_FORCE: {before.get('CONFIG_MODULE_SIG_FORCE')} -> {after.get('CONFIG_MODULE_SIG_FORCE')}",
        "- SELinux/module signature protections were not intentionally relaxed by this experiment.",
        "",
        "## Limitations",
        "",
        "- Candidate Kconfig changes may alter GKI KMI/ABI and module behavior.",
        "- A successful Google kernel build is not equivalent to Halium or Droidian boot.",
        "- Current Android 17 vendor blobs and the selected Google source branch",
        "  have NOT been verified as an exact matching pair.",
        "- Android 14 Halium/GSI integration, Droidian rootfs, init_boot",
        "  and other Pixel 8 split-boot details remain unresolved.",
        "",
    ])
    if failures:
        lines.extend(["## Unmet requirements", ""] + [f"- {x}" for x in failures])
    else:
        lines.append("**All requested settings appeared in the built .config.**")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output.read_text(encoding="utf-8"))
    return 1 if failures else 0


def config_fragment(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"(CONFIG_[A-Z0-9_]+)=(y|m|n)", line)
        if not match:
            raise ValueError(f"Unexpected fragment syntax: {line}")
        if match[1] in result:
            raise ValueError(f"Duplicate fragment option: {match[1]}")
        result[match[1]] = match[2]
    if not result:
        raise ValueError("Empty fragment")
    forbidden = {"CONFIG_MODULE_SIG_PROTECT", "CONFIG_MODULE_SIG_FORCE",
                 "CONFIG_SECURITY_SELINUX", "CONFIG_SECURITY_SELINUX_BOOTPARAM"}
    if result.keys() & forbidden:
        raise ValueError("Sensitive security options must not be changed in this experiment")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
