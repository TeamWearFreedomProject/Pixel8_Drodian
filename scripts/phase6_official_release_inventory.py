#!/usr/bin/env python3
"""Audit the official Droidian GitHub nightly assets without downloading phone images."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

def generate(data: dict) -> str:
    if data.get("tag_name") != "nightly" or data.get("draft"):
        raise ValueError("Expected official published nightly release metadata")
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("GitHub release has no assets")
    entries = []
    api_set = set()
    for asset in assets:
        name = asset["name"]
        match = re.search(r"-api([0-9]+)-arm64-", name)
        if match:
            api_set.add(int(match.group(1)))
        if "-rootfs-api" in name and name.endswith(".zip"):
            entries.append((name, asset["size"], asset["browser_download_url"]))
    if not entries:
        raise ValueError("No officially published generic rootfs assets found")
    lines = [
        "# Phase 6 — Official Droidian nightly reference availability",
        "",
        "**SOURCE INVENTORY ONLY — NOT A PIXEL 8 PORT — DO NOT FLASH**",
        "",
        "- Source: [official Droidian nightly](https://github.com/droidian-images/droidian/releases/tag/nightly)",
        f"- Published at: {data.get('published_at')}",
        f"- Release tag: `{data['tag_name']}`",
        f"- Android APIs represented among official arm64 assets: `{sorted(api_set)}`",
        f"- API 34 present: **{34 in api_set}**",
        f"- A Pixel 8 shiba asset is present: **{any('shiba' in a['name'].lower() for a in assets)}**",
        "",
        "| Reference only | Compressed size (MiB) |",
        "| --- | ---: |",
    ]
    for name, size, url in sorted(entries):
        lines.append(f"| [{name}]({url}) | {size / 1048576:.1f} |")
    lines.extend([
        "",
        "These are upstream generic recovery images **for other Android API levels**,",
        "NOT a compatible image for Pixel 8's current Android 17 vendor setup.",
        "The official package snapshot server must be independently reachable",
        "and cryptographically verified to construct a new signed Droidian base.",
        "A healthy GitHub Releases endpoint does not prove the APT server is healthy.",
        "",
    ])
    return "\n".join(lines)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = generate(json.loads(args.release_json.read_text(encoding="utf-8")))
    args.output.write_text(result, encoding="utf-8")
    print(result)

if __name__ == "__main__":
    main()
