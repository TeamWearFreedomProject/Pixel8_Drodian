#!/usr/bin/env python3
"""Validate the research-only shiba package before and after CI chroot installation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

PKG = "adaptation-google-shiba-research"
FILENAME = "usr/share/droidian-porting/shiba/port-status.json"
DOCFILE = "usr/share/doc/adaptation-google-shiba-research/README"
ALLOWED = {FILENAME, DOCFILE}

def query(deb: Path, field: str) -> str:
    return subprocess.check_output(
        ["dpkg-deb", "--field", str(deb), field], text=True).strip()

def validate(deb: Path, installed_root: Path | None) -> None:
    if query(deb, "Package") != PKG:
        raise ValueError("Unexpected Debian package name")
    if query(deb, "Architecture") != "arm64":
        raise ValueError("Research package must declare arm64")
    if "NOT FUNCTIONAL" not in query(deb, "Description"):
        raise ValueError("Package description lacks research-only warning")
    with tempfile.TemporaryDirectory(prefix="shiba-verification-") as tmp:
        root = Path(tmp) / "data"
        control = Path(tmp) / "control"
        root.mkdir()
        subprocess.run(["dpkg-deb", "--extract", str(deb), str(root)], check=True)
        subprocess.run(["dpkg-deb", "--control", str(deb), str(control)], check=True)
        ctrl = {p.name for p in control.iterdir() if p.is_file()}
        if ctrl != {"control"}:
            raise ValueError(f"No maintainer scripts/triggers permitted: {ctrl}")
        paths = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
        if paths != ALLOWED:
            raise ValueError(f"Unexpected installed package paths: {paths}")
        manifest = json.loads((root / FILENAME).read_text(encoding="utf-8"))
        if manifest["identity"]["codename"] != "shiba":
            raise ValueError("Wrong codename")
        if manifest["identity"]["architecture"] != "arm64":
            raise ValueError("Wrong architecture")
        if manifest["type"] != "research_only_not_installable_on_phone":
            raise ValueError("Manifest must be clearly non-functional")
        if manifest["phase4_evidence"]["run_id"] != 37728429488:
            raise ValueError("Unknown source-kernel evidence")
        if manifest["phase5_evidence"]["run_id"] != 37760550966:
            raise ValueError("Unknown ARM64 rootfs evidence")
        gates = manifest.get("compatibility_gate", {})
        if not gates or any(v is not False for v in gates.values()):
            raise ValueError("Must not mark unverified features as functional")
        if "DO NOT" not in (root / DOCFILE).read_text(encoding="utf-8").upper():
            raise ValueError("Missing safety limitations in README")
        if installed_root:
            if not (installed_root / FILENAME).is_file():
                raise ValueError("Package data not installed into CI rootfs")
            installed = json.loads(
                (installed_root / FILENAME).read_text(encoding="utf-8"))
            if installed != manifest:
                raise ValueError("Installed manifest mismatch")
    print("PASS: package architecture, files, scripts, metadata and safety gates")
    if installed_root:
        print("PASS: installed contents match packaged contents in disposable CI rootfs")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deb", type=Path, required=True)
    ap.add_argument("--installed-root", type=Path)
    args = ap.parse_args()
    validate(args.deb.resolve(), args.installed_root)

if __name__ == "__main__":
    main()
