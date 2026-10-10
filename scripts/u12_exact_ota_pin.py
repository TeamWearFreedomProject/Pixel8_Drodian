#!/usr/bin/env python3
"""U12: pin the user's EXACT Evolution X shiba build from the official OTA index.

Provenance-only. Does not download/parse any 3GB OTA ROM or produce images.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

OTA_REPO_COMMIT = "b400c98274f840b503e142782957cd37d699f0bb"
EXACT_NAME = "EvolutionX-16.0-20260915-shiba-11.11-Official.zip"
EXACT_SHA = "41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0"
EXACT_BYTES = 3033648565
OFFICIAL_IMAGES = ["boot", "dtbo", "vendor_kernel_boot", "vendor_boot"]
REQUIRED_JSON_KEYS = {"filename","sha256","size","download","version","buildtype",
                      "initial_installation_images","device","timestamp"}
REFERENCE_U7_SHA = "1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa"


def fail(text):
    raise SystemExit("U12 STRICT FAIL: "+text)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ota",type=Path,required=True)
    p.add_argument("--u7",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rev=subprocess.check_output(["git","-C",str(args.ota),"rev-parse","HEAD"],
                                text=True).strip()
    if rev!=OTA_REPO_COMMIT: fail("OTA source HEAD does not match pinned commit")
    path=args.ota/"builds/shiba.json"
    response=json.loads(path.read_text())["response"]
    if len(response)!=1: fail("Expected one official OTA record")
    data=response[0]
    if not REQUIRED_JSON_KEYS.issubset(data): fail("OTA fields missing")
    checks={
        "filename_is_exact": data["filename"]==EXACT_NAME,
        "sha256_is_official_pinned":data["sha256"]==EXACT_SHA,
        "size_is_official_pinned":data["size"]==EXACT_BYTES,
        "device_is_shiba":data["device"]=="Pixel 8",
        "version_is_11_11":data["version"]=="11.11",
        "buildtype_user":data["buildtype"]=="user",
        "official_images_match":data["initial_installation_images"]==OFFICIAL_IMAGES,
        "ota_url_exact":data["download"]==
            "https://cdn.evolution-x.org/shiba/16/"+EXACT_NAME+"/download",
    }
    if not all(checks.values()): fail("Official build changed: "+str(checks))
    # Husky is a separate phone; its filename and hash must differ.
    husky=json.loads((args.ota/"builds/husky.json").read_text())["response"][0]
    if husky["sha256"]==EXACT_SHA or husky["filename"]==EXACT_NAME:
        fail("husky vs shiba source confusion")
    boot=args.u7.read_bytes()
    if hashlib.sha256(boot).hexdigest()!=REFERENCE_U7_SHA:
        fail("old experimental U7 boot mismatch")
    result={
        "status":"PASS_EXACT_OFFICIAL_OTA_METADATA_ONLY",
        "user_confirmed_installed_build_name":EXACT_NAME,
        "official_ota_index_commit":rev,
        "official_ota_record":data,
        "official_sha256_is_METADATA_ONLY":True,
        "downloaded_exact_rom_bytes":False,
        "archive_sha256_computed_locally":False,
        "read_original_ota_payload_bin":False,
        "verified_kernel_module_abi":False,
        "experimental_u7_boot_separate_from_official":True,
        "prior_experimental_u7_boot_sha256":REFERENCE_U7_SHA,
        "pro_and_standard_builds_not_interchangeable":True,
        "bootable_pixel8_ubuntu":False,
        "safe_to_flash":False,
        "physical_device_access":False,
        "assertions":checks,
        "next_step":"Acquire exact official 3.03 GB OTA ZIP, verify SHA-256 before binary vendor/kernel inspection. Never treat names as compatible binaries."
    }
    (args.out/"U12_OFFICIAL_BUILD.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=[
        "# U12: officially pinned Evolution X 16.0 Pixel 8 shiba 20260915 v11.11",
        "",
        "**SUCCESS: exact OTA metadata matched; downloaded ROM binary still NOT verified.**",
        "",
        "- Official metadata repo: https://github.com/Evolution-X/OTA/tree/bka",
        "- Pinned bka source commit: "+rev,
        "- Confirmed official filename: "+EXACT_NAME,
        "- Official file length: "+str(EXACT_BYTES)+" bytes (about 3.03 GB decimal)",
        "- Official SHA256 (not independently hashed yet): "+EXACT_SHA,
        "- Official source download link: "+data["download"],
        "- Build type: user, version 11.11, Google Pixel 8 (shiba), Android 16.",
        "- Official companion initial installation image names: "+
          ", ".join(OFFICIAL_IMAGES),
        "- They are *names*, not binary SHA/vermagic/DTBO compatibility evidence.",
        "- Verified U7 RESEARCH boot SHA256 (different provenance): "+REFERENCE_U7_SHA,
        "- No ROM ZIP or payload.bin was downloaded by this audit.",
        "- No actual installed kernel version or vendor module KMI was established.",
        "- No device access, partition operations or flashable image was created.",
        "",
        "## Decision",
        "- The user's build identity is now linked to official, pinned OTA metadata.",
        "- Next binary comparison needs the EXACT ZIP contents verified against SHA-256.",
        "- No official kernel/vendor pairing may be inferred until then.",
        "",
        "**BUILD-ONLY RESEARCH; PIXEL8 UBUNTU STILL NOT FLASHABLE.**"
    ]
    (args.out/"U12_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))


if __name__=="__main__":main()
