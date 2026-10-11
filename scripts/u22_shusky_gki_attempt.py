#!/usr/bin/env python3
"""U22 research: real shusky vendor build attempt on pinned 6.1.157 GKI.

Build failure is a finding and is NEVER hidden as a compatible Pixel 8 ROM.
No device operations, image repack, or verified-boot metadata alterations.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PIN = "bd23337e42e794964a89f47596daf1209a25ee1a"
BASELINE = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
EXPECT_VENDOR = {
    "kernel/devices/google/shusky": "a88953f657282d6e52c6c0b3669ca3a890907518",
    "kernel/devices/google/zuma": "eb90f2862e78b4c409ff992e116c44e81f836e9e",
}

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()

def kernel_banner(p):
    if not p.is_file():
        return None
    prev = b""
    with p.open("rb") as f:
        while True:
            block = f.read(2**20)
            if not block:
                break
            m = re.search(rb"Linux version (6\.1\.\d+-[^\x00\s]+)", prev+block)
            if m:
                return m.group(1).decode("ascii", "replace")
            prev = block[-256:]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--build-exit", type=int, required=True)
    ap.add_argument("--checkout-commit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    actual = a.checkout_commit.read_text().strip().lower()
    if actual != PIN:
        raise RuntimeError("Pinned GKI commit changed; refusing U22 report")
    src = {p.get("name"): dict(p.attrib) for p in
           ET.parse(a.manifest).getroot().findall("project")}
    manifest_gki = src.get("kernel/common", {}).get("revision")
    if manifest_gki != PIN:
        raise RuntimeError("Resolved manifest does not contain exact GKI sha")
    if not a.log.is_file():
        raise RuntimeError("Missing compiler log; cannot claim build attempted")
    dist = a.source_dir / "out/shusky/dist"
    binaries = {}
    for name in ("Image", "boot.img", "dtbo.img", "vendor_kernel_boot.img",
                 "vendor_dlkm.img", "system_dlkm.img"):
        p = dist / name
        if p.is_file():
            binaries[name] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    ko = sorted(dist.glob("*.ko")) if dist.is_dir() else []
    actual_kernel = kernel_banner(dist / "Image")
    compiler_success = a.build_exit == 0
    release_family = bool(actual_kernel and actual_kernel.startswith(
        "6.1.157-android14-11-"))
    source_shas = {k: src.get(k, {}).get("revision") for k in EXPECT_VENDOR}
    report = {
        "status": ("U22_RESEARCH_BUILD_SUCCEEDED_VENDOR_ABI_UNPROVEN" if compiler_success
                   else "U22_REAL_BUILD_FAILED_COMPILER_EVIDENCE_PRESERVED"),
        "build_command": "bash ./build_shusky.sh",
        "build_exit_code": a.build_exit,
        "source_gki_commit": actual,
        "manifest_kernel_common_revision": manifest_gki,
        "stock_cp2a_uname": BASELINE,
        "built_kernel_release": actual_kernel,
        "built_kernel_6_1_157_android14_11": release_family,
        "built_kernel_exactly_stock_release": actual_kernel == BASELINE,
        "source_vendor_git_revisions": source_shas,
        "vendor_revisions_equal_historical_U17": {
            k: source_shas[k] == v for k, v in EXPECT_VENDOR.items()
        },
        "output_files": binaries,
        "individual_ko_count": len(ko),
        "ko_basenames_sample": [p.name for p in ko[:35]],
        "full_KMI_symbol_modversions_stability_proven": False,
        "vendor_ko_vermagic_matches_stock_cp2a_proven": False,
        "shiba_panel_dtbo_selected_tested": False,
        "stock_cp2a_signed_boot_identity_proven": False,
        "native_ubuntu_on_pixel8_booted": False,
        "device_modified": False,
        "real_device_flash_gate": "DENY",
    }
    (a.out / "U22_SHUSKY_6_1_157_REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    lines = [
        "# U22 — Pixel 8 shusky vendor rebuild against pinned GKI 6.1.157",
        "", "**RESEARCH BUILD ONLY — DO NOT FLASH.**", "",
        f"- Source kernel commit pinned: \`{actual}\`.",
        f"- Previous U17 source vendor revisions matched: {report['vendor_revisions_equal_historical_U17']}",
        f"- Actual compiler exit code: **{a.build_exit}**.",
        f"- Build result: **{'SUCCEEDED' if compiler_success else 'FAILED'}**.",
        f"- Real built kernel release: \`{actual_kernel or 'NOT GENERATED'}\`.",
        f"- Number of distinct distribution .ko files: {len(ko)}.",
        f"- Kernel in 6.1.157/android14-11 family: {release_family}.",
        f"- Exact installed CP2A release matched: {actual_kernel == BASELINE}.",
        "", "## Generated files (if any)",
    ] + [f"- {n}: {v['bytes']} bytes; SHA256 \`{v['sha256']}\`"
         for n, v in binaries.items()] + [
        "", "## Hard blockers",
        "- Compiler success does NOT prove stock vendor driver symbol CRCs/KMI.",
        "- Presence of DTBO is not proof of actual shiba panel/touch overlay selection.",
        "- No CP2A signed boot chain, no Ubuntu initramfs boot, no AVB rollback evidence.",
        "- No automatic acceptance of \`boot.img\`, DTBO or modules as deployable.",
        "- No device connected, no fastboot or partition/slot operations.",
        "**REAL DEVICE FLASH GATE: DENY.**",
    ]
    (a.out / "U22_SHUSKY_6_1_157_REPORT.md").write_text(
        "\n".join(lines) + "\n"
    )
    print("\n".join(lines))

if __name__ == "__main__":
    main()
