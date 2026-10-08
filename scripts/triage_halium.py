#!/usr/bin/env python3
"""Classify Pixel 8 / Droidian configuration differences from the Phase 2 artifact.

Read-only, build-only analysis: does not change kernel source/config or create boot images.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys

# These are triage priorities, NOT a list of changes to apply automatically.
CORE = {
    "CONFIG_SYSVIPC", "CONFIG_NAMESPACES", "CONFIG_PID_NS", "CONFIG_USER_NS",
    "CONFIG_DEVTMPFS", "CONFIG_NULL_TTY", "CONFIG_VT",
}
BOOT = {
    "CONFIG_INITRAMFS_SOURCE", "CONFIG_INITRAMFS_COMPRESSION_GZIP",
    "CONFIG_RD_GZIP", "CONFIG_SQUASHFS", "CONFIG_SQUASHFS_FILE_DIRECT",
    "CONFIG_SQUASHFS_DECOMP_MULTI_PERCPU", "CONFIG_SQUASHFS_LZ4",
    "CONFIG_SQUASHFS_LZO", "CONFIG_SQUASHFS_XZ", "CONFIG_SQUASHFS_ZSTD",
}
SECURITY = {"CONFIG_CMDLINE", "CONFIG_MODULE_SIG_FORCE", "CONFIG_MODULE_SIG_PROTECT"}
LEGACY = {
    "CONFIG_CFS_SCHED", "CONFIG_CGROUP_MEM_RES_CTLR",
    "CONFIG_CGROUP_MEM_RES_CTLR_SWAP", "CONFIG_CGROUP_MEM_RES_CTLR_KMEM",
    "CONFIG_CGROUP_HUGETLB", "CONFIG_MEMCG_SWAP",
}
ANDROID = {"CONFIG_ANDROID_BINDER_DEVICES"}
BUILD = {"CONFIG_LTO_CLANG_THIN"}
CONTAINER = {"CONFIG_CGROUP_PIDS", "CONFIG_POSIX_MQUEUE", "CONFIG_VETH"}


def config_values(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r"(CONFIG_[A-Z0-9_]+)=(.*)", line)
        if m:
            result[m.group(1)] = m.group(2)
            continue
        m = re.fullmatch(r"# (CONFIG_[A-Z0-9_]+) is not set", line)
        if m:
            result[m.group(1)] = "n"
    return result


def parse_report(path: Path) -> list[tuple[str, str, str, str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `CONFIG_"):
            continue
        fields = [part.strip() for part in line.split("|")]
        if len(fields) != 7:
            raise ValueError(f"Bad Phase 2 table row: {line[:160]}")
        key, expected, observed, verdict, source = fields[1:6]
        if not (key.startswith("`CONFIG_") and key.endswith("`")):
            raise ValueError(f"Invalid config key: {key}")
        if verdict not in ("MATCH", "DIFF", "UNKNOWN"):
            raise ValueError(f"Invalid Phase 2 verdict: {verdict}")
        rows.append((
            key.strip("`"), expected.strip("`"),
            observed.strip("`"), verdict, source.strip("`"),
        ))
    if not rows:
        raise ValueError("No Phase 2 configuration table found")
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError("Duplicate configuration keys in Phase 2 report")
    return rows


def category(key: str, expected: str, actual: str, source: str) -> tuple[str, str]:
    if expected == actual:
        return ("MATCH", "Already matches upstream fragment; do not change")
    if key in SECURITY:
        return ("SECURITY REVIEW", "Never blindly disable SELinux, module signature protection or other security controls")
    if key in CORE:
        return ("HALIUM CORE", "Investigate kernel dependencies and privileged LXC operation; may affect security")
    if key in BOOT:
        return ("BOOT/ROOTFS", "Resolve Pixel split-boot and rootfs design before choosing this setting")
    if key in ANDROID:
        return ("ANDROID INTEGRATION", "Binder device names need runtime verification, not an automatic string replacement")
    if expected == "y" and actual == "m":
        return ("MODULE VS BUILTIN", "Already available as a module; check load order and whether early boot needs it built-in")
    if key in LEGACY and actual == "(absent)":
        return ("LEGACY SYMBOL REVIEW", "May have been renamed or removed; investigate kernel Kconfig; do not add stale symbols")
    if key in BUILD:
        return ("BUILD TOOLCHAIN", "Check compiler/toolchain compatibility and existing GKI build settings")
    if key in CONTAINER:
        return ("LXC CAPABILITY", "Check whether the Android service container really needs this capability")
    if actual == "(absent)":
        return ("MISSING SYMBOL REVIEW", "Check support/dependencies before calling this a missing feature")
    if source == "container.config":
        return ("OPTIONAL CONTAINERS", "Often feature-specific; not automatically a phone-boot blocker")
    return ("FEATURE REVIEW", "Verify use in Droidian userspace and module dependency graph")


def make_report(rows: list[tuple[str, str, str, str, str]], actual: dict[str, str]) -> str:
    mismatches = []
    categories = Counter()
    checked = Counter()
    for key, expected, got, verdict, source in rows:
        observed = actual.get(key, "(absent)")
        if observed != got:
            raise ValueError(f"Phase 2 report/config mismatch for {key}: {got} != {observed}")
        correct = "MATCH" if expected == got else "DIFF"
        if verdict != correct:
            raise ValueError(f"Phase 2 verdict disagrees for {key}")
        checked[correct] += 1
        kind, reason = category(key, expected, got, source)
        if verdict == "DIFF":
            categories[kind] += 1
            mismatches.append((kind, key, expected, got, source, reason))

    if checked["DIFF"] == 0:
        raise ValueError("No differences recorded; verify the Phase 2 artifact")
    if checked["MATCH"] + checked["DIFF"] != len(rows):
        raise ValueError("Unexpected unclassified rows")

    lines = [
        "# Pixel 8 shiba — Phase 3 Halium configuration triage",
        "",
        "**BUILD ONLY / NO DEVICE ACCESS / UNVERIFIED / NOT A BOOTABLE DROIDIAN IMAGE**",
        "",
        "This report reuses the Phase 2 artifact's actual Google shusky `google-built.config`.",
        "It does not rebuild the kernel and does not change security settings, sources, or firmware.",
        "",
        "## Verified Phase 2 table",
        "",
        f"- Total checked: **{len(rows)}**",
        f"- Exact matches: **{checked['MATCH']}**",
        f"- Differences: **{checked['DIFF']}**",
        "- The table was cross-checked against the .config stored in the same artifact.",
        "",
        "## Classification of differences (review queues, not automatic fixes)",
        "",
        "| Queue | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {kind} | {count} |" for kind, count in sorted(categories.items()))
    lines.extend([
        "",
        "## Per-setting triage",
        "",
        "| Queue | Symbol | Droidian | Google shusky | Upstream fragment | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for kind, key, expected, observed, source, reason in sorted(mismatches):
        lines.append(
            f"| {kind} | `{key}` | `{expected}` | `{observed}` | `{source}` | {reason} |"
        )
    lines.extend([
        "",
        "## High-priority *investigations*",
        "",
        "1. **LXC namespaces and IPC:** confirm PID/user namespaces, SYSVIPC, devtmpfs and",
        "   the actual privileges/setup used by the Halium Android container. Enabling",
        "   namespaces changes the kernel security surface; investigate before modifying.",
        "2. **Kernel boot/initramfs:** Pixel 8 uses split boot components; a generic embedded",
        "   `CONFIG_INITRAMFS_SOURCE` recipe is not a shiba-specific boot strategy.",
        "3. **GKI / vendor ABI:** validate symbol versions, signature/protection constraints,",
        "   and alignment between the selected shusky kernel and the Pixel vendor modules.",
        "   Phase 2 built Google's `android-gs-shusky-6.1-android16` branch;",
        "   this was **not** verified to match factory `CP3A.260905.009`.",
        "4. **Userspace compatibility:** Droidian's Android 14 GSI package existing does",
        "   not demonstrate compatibility with Android 17 vendor services on Pixel 8.",
        "5. **Review optional features separately:** Waydroid, Docker, Bluetooth modules",
        "   and container networking are not all essential for the first boot.",
        "",
        "**No patches are applied. No ADB, fastboot, flash, or real-device operations.**",
        "",
    ])
    return "\n".join(lines)


def self_test() -> None:
    assert category("CONFIG_BT", "y", "m", "droidian.config")[0] == "MODULE VS BUILTIN"
    assert category("CONFIG_PID_NS", "y", "n", "halium.config")[0] == "HALIUM CORE"
    assert category("CONFIG_CMDLINE", "x", "y", "droidian.config")[0] == "SECURITY REVIEW"
    assert category("CONFIG_INITRAMFS_SOURCE", "x", "y", "droidian.config")[0] == "BOOT/ROOTFS"
    assert category("CONFIG_CGROUP_MEM_RES_CTLR", "y", "(absent)", "container.config")[0] == "LEGACY SYMBOL REVIEW"
    assert category("CONFIG_VETH", "y", "y", "droidian.config")[0] == "MATCH"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase2-report", type=Path)
    ap.add_argument("--kernel-config", type=Path)
    ap.add_argument("--output", type=Path, default=Path("phase3-triage.md"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    self_test()
    if args.self_test:
        print("Self-tests passed")
        return 0
    if not args.phase2_report or not args.kernel_config:
        ap.error("--phase2-report and --kernel-config are required")

    rows = parse_report(args.phase2_report)
    config = config_values(args.kernel_config)
    if len(config) < 500:
        raise ValueError(f"Unexpectedly small Google kernel .config ({len(config)} keys)")
    output = make_report(rows, config)
    args.output.write_text(output, encoding="utf-8")
    print(output[:12000])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"Phase 3 analysis failed: {exc}", file=sys.stderr)
        sys.exit(1)
