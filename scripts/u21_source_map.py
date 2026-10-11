#!/usr/bin/env python3
"""U21 immutable Google shusky + GKI manifest comparison and board map.

No device I/O. This is a source map, not an ABI validation, signed kernel,
bootloader rollback test, or native Ubuntu port.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

STOCK_KERNEL = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
GKI_COMMIT = "bd23337e42e794964a89f47596daf1209a25ee1a"
U17_KERNEL = "6.1.124-android14-11-g8d713f9e8e7b-ab13202960"
REQUIRED = {
    "kernel/common": "aosp",
    "kernel/devices/google/shusky": "private/devices/google/shusky",
    "kernel/devices/google/zuma": "private/devices/google/zuma",
    "kernel/google-modules/display/common": "private/google-modules/display/common",
    "kernel/google-modules/touch/common": "private/google-modules/touch/common",
}

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def source_map(xmlfile):
    root = ET.parse(xmlfile).getroot()
    return {p.get("name"): dict(p.attrib) for p in root.findall("project")}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--u17", type=Path, required=True)
    p.add_argument("--u18", type=Path, required=True)
    p.add_argument("--refs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    u17report = json.loads((a.u17 / "U17_SOURCE_IMAGE_REPORT.json").read_text())
    u18report = json.loads((a.u18 / "U18_CP2A_GKI_REPORT.json").read_text())
    shusky = source_map(a.u17 / "U17_MANIFEST_RESOLVED.xml")
    gki = source_map(a.u18 / "U18_RESOLVED_MANIFEST.xml")
    u17image = a.u17 / "research-images-UNVERIFIED/Image"
    if sha256(u17image) != u17report["images"]["Image"]["sha256"]:
        raise RuntimeError("U17 kernel failed artifact SHA256 check")
    if u17report["built_kernel_release"] != U17_KERNEL:
        raise RuntimeError("U17 source kernel identity changed")
    if u18report["observed_commit"] != GKI_COMMIT:
        raise RuntimeError("U18 pinned GKI source commit changed")
    for name, path in REQUIRED.items():
        if name not in shusky or shusky[name].get("path") != path:
            raise RuntimeError("U17 official source project absent: " + name)
    if "kernel/common" not in gki or gki["kernel/common"]["revision"] != GKI_COMMIT:
        raise RuntimeError("U18 resolved manifest missing exact kernel/common SHA")

    dtbo_file = a.u17 / "U17_SOURCE_DTS_LIST.txt"
    dts = dtbo_file.read_text().splitlines()
    shiba = [x for x in dts if "shiba" in x.lower()]
    husky = [x for x in dts if "husky" in x.lower()]
    if not any("shiba" in s.lower() for s in shiba):
        raise RuntimeError("No shiba overlay inputs in U17 source inventory")
    if not any("husky" in s.lower() for s in husky):
        raise RuntimeError("Expected family husky overlay inventory absent")

    # This branch-ref list is measured by the CI Git probe, NOT inferred.
    refs = a.refs.read_text().splitlines()
    remote_branches = sorted(set(
        row.rsplit("refs/heads/", 1)[-1] for row in refs if "refs/heads/" in row
    ))
    wanted = "android-gs-shusky-6.1-android16"
    if wanted not in remote_branches:
        raise RuntimeError("Official shusky Android16 branch not visible")
    android17 = [x for x in remote_branches if x.endswith("android17") or "-android17-" in x]
    report = {
        "status": "PASS_PUBLIC_SOURCE_MAP_CP2A_VENDOR_REVISION_NOT_PROVEN",
        "stock_shiba_cp2a_kernel": STOCK_KERNEL,
        "u17_vendor_source_branch": wanted,
        "u17_vendor_source_common_git_revision": shusky["kernel/common"]["revision"],
        "u17_actual_built_kernel": U17_KERNEL,
        "u18_exact_gki_common_commit": GKI_COMMIT,
        "u18_source_patch_level": u18report["source_kernel_version"],
        "official_shusky_branch_probe_refs": remote_branches,
        "candidate_android17_named_shusky_branches_visible_in_probe": android17,
        "shusky_manifest_project_count": len(shusky),
        "gki_manifest_project_count": len(gki),
        "shiba_dts_list": shiba,
        "husky_dts_list": husky,
        "vendor_projects_pinned_in_u17": {k: shusky[k] for k in REQUIRED},
        "gki_6_1_157_exact_source_commit_verified": True,
        "CP2A_exact_shiba_vendor_source_revision_verified": False,
        "compatible_vendor_modules_and_KMI_symbols_verified": False,
        "safe_to_combine_old_u17_modules_with_new_gki": False,
        "bootable_ubuntu_pixel8": False,
        "real_device_flash_gate": "DENY",
    }
    (a.out / "U21_SOURCE_MAP.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    rows = [
        "# U21 — pinned shiba vendor source vs CP2A GKI source", "",
        "**SOURCE INVENTORY PASS / CP2A VENDOR MODULE REVISION UNKNOWN. DO NOT FLASH.**", "",
        f"- CP2A real phone: \`{STOCK_KERNEL}\`.",
        f"- U18 official GKI source: \`{GKI_COMMIT}\` / 6.1.157.",
        f"- U17 device build: \`{U17_KERNEL}\`.",
        f"- U17 shusky manifest common commit: \`{shusky['kernel/common']['revision']}\`.",
        f"- U17 shusky vendor tree: \`{shusky['kernel/devices/google/shusky']['revision']}\`.",
        f"- U17 source references {len(shusky)} Git projects; U18 references {len(gki)}.",
        f"- Google shusky branch probe matched {len(remote_branches)} named refs;",
        f"  android17-labeled refs among the probe: {', '.join(android17) or 'none seen (not proof of absence elsewhere)'}.",
        "", "## Separate physical board inputs",
        f"- Pixel 8 shiba DTS filenames: {len(shiba)}",
        f"- Pixel 8 Pro husky DTS filenames: {len(husky)}",
        "",
        "| Google source project | U17 source revision |",
        "| --- | --- |",
    ]
    for key in REQUIRED:
        rows.append(f"| {key} | \`{shusky[key]['revision']}\` |")
    rows.extend([
        "", "## Blockers",
        "- No vendor commit tied to real \`CP2A.260805.005\` has been verified.",
        "- No evidence that the old 6.1.124 module set links against U18 6.1.157.",
        "- DTS filename presence cannot validate selected shiba DTBO or panel.",
        "- Android OS version and kernel GKI generation are distinct.",
        "- Source mapping has NOT built device drivers for 6.1.157.",
        "- No phone connected, no bootloader/partition changes.",
        "**REAL DEVICE FLASH GATE: DENY.**",
    ])
    (a.out / "U21_SOURCE_MAP.md").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))

if __name__ == "__main__":
    main()
