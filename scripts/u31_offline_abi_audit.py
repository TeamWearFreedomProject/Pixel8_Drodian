#!/usr/bin/env python3
"""U31 offline Pixel 8 source-built ABI/board metadata audit, NOT device validation.

Reads the isolated U31 build output and verified U30 evidence. Inspects the
source-built GKI Image, exported symbol CRC table, available .ko vermagic and
their imported CRCs, and DTBO file structure. No phone, fastboot, userdata,
flashing, privileged host operations, Android stock dump, or release binaries.

Crucial: the reference here is *our research kernel*. The original shiba
CP2A vendor module/Module.symvers/bootloader/DTBO references are NOT present,
so a healthy offline check can NEVER authorize physical boot or flashing.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

GKI_SHA = "bd23337e42e794964a89f47596daf1209a25ee1a"
STOCK_RELEASE = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
EXPECTED_IMAGE_SHA_U30 = "86c8bd5a89088033bc01dec4e40fb40e37238d567064328b4c49b08dc4d9cdbc"
EXPECTED_IMAGE_BYTES_U30 = 35633664
OLD_124 = "6.1.124-android14-11"

def die(message):
    raise SystemExit("U31 OFFLINE ABI AUDIT FAIL CLOSED: " + message)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def kernel_banner(path):
    previous = b""
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            result = re.search(rb"Linux version (6\.1\.[^\x00\s]+)", previous + chunk)
            if result:
                return result.group(1).decode("ascii", "replace")
            previous = chunk[-2048:]
    return None

def command(argv, timeout=25):
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, check=False)
        return (p.returncode, p.stdout.strip(), p.stderr.strip()[:600])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return (127, "", str(exc)[:600])

def module_listing(src):
    # Results are limited to staged build outputs. Never scan host or phone.
    roots = [src/"bazel-bin/private/google-modules",
             src/"bazel-bin/private/devices/google/shusky",
             src/"out/shusky/dist"]
    paths = {}
    for root in roots:
        if not root.exists():
            continue
        rc, listing, _ = command(
            ["find", "-L", str(root), "-maxdepth", "12",
             "-type", "f", "-name", "*.ko"], timeout=90)
        if rc != 0:
            continue
        for line in listing.splitlines():
            p = Path(line)
            if p.is_file():
                try:
                    resolved = str(p.resolve())
                    paths.setdefault(resolved, p)
                except OSError:
                    continue
    return list(paths.values())

def read_symvers(path):
    exports = {}
    samples = []
    malformed = 0
    with path.open(errors="replace") as f:
        for line in f:
            cols = line.strip().split()
            if len(cols) < 3 or not re.fullmatch(r"0x[0-9a-fA-F]{1,8}", cols[0]):
                malformed += 1
                continue
            symbol, crc = cols[1], int(cols[0], 16)
            if symbol in exports and exports[symbol] != crc:
                die("exported symbol "+symbol+" has conflicting CRCs")
            exports[symbol] = crc
            if len(samples) < 6:
                samples.append({"symbol": symbol, "crc": "%08x" % crc})
    if not exports:
        die("source GKI Module.symvers exported symbol table empty")
    return exports, samples, malformed

def inspect_ko(path, exports):
    rc, name, _ = command(["modinfo", "-F", "name", str(path)])
    vm_rc, vm, vm_err = command(["modinfo", "-F", "vermagic", str(path)])
    data = {"module": name if rc == 0 and name else path.name,
            "source": str(path),
            "bytes": path.stat().st_size,
            "vermagic": vm if vm_rc == 0 else None,
            "vermagic_read_error": vm_err if vm_rc else None,
            "vermagic_has_6_1_157_prefix": bool(vm_rc == 0 and
                  vm.startswith("6.1.157-android14-11")),
            "module_crc_compared_count": 0, "module_crc_disagree_count": 0,
            "unmatched_external_symbols": 0}
    rc, text, error = command(["modprobe", "--show-modversions", str(path)])
    data["module_crc_inspection_rc"] = rc
    if rc != 0:
        data["module_crc_inspection_error"] = error
    else:
        disagreements = []
        examples_missing = []
        for line in text.splitlines():
            cols = line.strip().split(None, 1)
            if len(cols) != 2 or not re.fullmatch(r"0x[0-9a-fA-F]{1,8}", cols[0]):
                continue
            expected = exports.get(cols[1].strip())
            if expected is None:
                data["unmatched_external_symbols"] += 1
                if len(examples_missing) < 4:
                    examples_missing.append(cols[1].strip())
                continue
            data["module_crc_compared_count"] += 1
            if int(cols[0], 16) != expected:
                data["module_crc_disagree_count"] += 1
                if len(disagreements) < 5:
                    disagreements.append(cols[1].strip())
        data["crc_mismatch_symbol_examples"] = disagreements
        data["symbol_not_in_base_gki_examples"] = examples_missing
    return data

def dtbo_description(path):
    if not path.is_file():
        return {"present": False, "CP2A_board_overlay_equivalent": False}
    with path.open("rb") as f:
        head=f.read(32)
    if len(head) != 32:
        return {"present": True, "header_valid": False,
                "sha256": digest(path)}
    (magic,total,header_size,entry_size,entry_count,offset,page,version) = (
        struct.unpack(">8I",head))
    okay=(magic == 0xd7b7ab1e and 32 <= header_size <= 1024
          and entry_size >= 32 and entry_count < 10000
          and total <= path.stat().st_size and
          offset + entry_size * entry_count <= total)
    return {"present": True, "header_valid": okay,
            "bytes": path.stat().st_size, "sha256": digest(path),
            "android_dt_table_magic": hex(magic),
            "entry_count": entry_count, "dt_table_version": version,
            "CP2A_board_overlay_equivalent": False}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--src", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--u30", type=Path, required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original=json.loads(args.u30.read_text())
    if original.get("stage") != "U30_SHUSKY_VENDOR_FULL_DIST" or (
        original.get("real_bazel_exit") != 0 or
        original.get("Image_release_actual") != "6.1.157-android14-11" or
        original.get("Image_sha256") != EXPECTED_IMAGE_SHA_U30 or
        original.get("Image_bytes") != EXPECTED_IMAGE_BYTES_U30 or
        original.get("real_device_flash_gate") != "DENY"):
        die("historic U30 success reference is not the verified run #6")
    rc,git,err=command(["git","-C",str(args.src/"aosp"),"rev-parse","HEAD"])
    if rc!=0 or git != GKI_SHA:
        die("current CI source not pinned to official r9 6.1.157: "+err)

    direct=args.src/"bazel-bin/aosp/kernel_aarch64/Image"
    full=args.src/"out/shusky/dist/Image"
    symvers=args.src/"bazel-bin/aosp/kernel_aarch64/kernel_aarch64_Module.symvers"
    for path in (direct,full,symvers):
        if not path.is_file():
            die("required genuine source-build file missing: "+str(path))
    direct_sha=digest(direct)
    full_sha=digest(full)
    direct_banner=kernel_banner(direct)
    full_banner=kernel_banner(full)
    if not direct_banner or not direct_banner.startswith("6.1.157-android14-11"):
        die("source GKI Image banner not 6.1.157")
    if full_banner!=direct_banner or full_sha!=direct_sha:
        die("the shusky distributed Image differs from source-built GKI Image")
    if OLD_124 in full_banner:
        die("stale 6.1.124 Image selected unexpectedly")

    exports, samples, malformed=read_symvers(symvers)
    modules=module_listing(args.src)
    inspected=[]
    # Cap for report size; enumerate all names and inspect up to 180 real files.
    for module in modules[:180]:
        inspected.append(inspect_ko(module,exports))
    mismatch_count=sum(m["module_crc_disagree_count"] for m in inspected)
    vermagic_bad=[m["module"] for m in inspected
                  if not m["vermagic_has_6_1_157_prefix"]]
    compare_count=sum(m["module_crc_compared_count"] for m in inspected)

    dist=args.src/"out/shusky/dist"
    dtbo=dtbo_description(dist/"dtbo.img")
    outputs={}
    for name in ("Image","Image.gz","Image.lz4","dtbo.img",
                 "vendor_kernel_boot.img","vendor_dlkm.img","system_dlkm.img"):
        path=dist/name
        outputs[name]={"present":path.is_file()}
        if path.is_file():
            outputs[name].update({"size_bytes":path.stat().st_size,
                                  "sha256":digest(path)})
    result={
        "phase":"U31",
        "status":"U31_RESEARCH_OFFLINE_INVENTORY_COMPLETE_NOT_CP2A_DEVICE_CERTIFIED",
        "source_gki_git_sha":GKI_SHA,
        "historic_U30_reference_sha256":EXPECTED_IMAGE_SHA_U30,
        "actual_source_gki_Image_sha256":direct_sha,
        "actual_shusky_full_Image_sha256":full_sha,
        "Image_banners_match":direct_banner==full_banner,
        "actual_Image_release":full_banner,
        "matches_complete_CP2A_stock_build_banner":full_banner==STOCK_RELEASE,
        "CP2A_stock_6_1_157_full_release":STOCK_RELEASE,
        "rebuilt_Image_matches_historic_U30_image_sha256":full_sha==EXPECTED_IMAGE_SHA_U30,
        "source_GKI_symvers_sha256":digest(symvers),
        "source_GKI_exported_symbol_count":len(exports),
        "source_GKI_symvers_malformed_rows":malformed,
        "source_GKI_symbol_crc_examples":samples,
        "vendor_modules_found_as_direct_ko":len(modules),
        "vendor_modules_inspected":len(inspected),
        "module_vermagic_mismatch_count":len(vermagic_bad),
        "module_vermagic_mismatch_examples":vermagic_bad[:15],
        "kernel_exported_symbol_crc_comparisons":compare_count,
        "kernel_exported_symbol_crc_disagreements":mismatch_count,
        "all_vendor_module_CRCs_checked":len(modules)<=180 and len(modules)>0,
        "vendor_module_crc_sample":[{
            k:v for k,v in m.items() if k!="source"
        } for m in inspected[:35]],
        "shusky_dist_files":outputs,
        "shusky_dtbo_table":dtbo,
        "stock_CP2A_module_symvers_or_stock_vendor_modules_provided":False,
        "stock_CP2A_vendor_module_crc_compatibility_proven":False,
        "stock_CP2A_DTBO_panel_compatibility_proven":False,
        "stock_CP2A_AVB_rollback_and_rescue_verified":False,
        "Ubuntu_rootfs_boot_proven":False,
        "administrative_rights_on_user_PC_required":False,
        "physical_Pixel8_ever_accessed":False,
        "device_flash_gate":"DENY"
    }
    (args.out/"U31_OFFLINE_ABI_BOARD_AUDIT.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    md=[
       "# U31 — real offline GKI/vendor ABI and board metadata audit",
       "",
       "**RESEARCH AUDIT, NOT CP2A STOCK ABI CERTIFICATION. DEVICE FLASH GATE DENY.**",
       "",
       "- U30 genuine source Image and U31 full shusky Image: SHA256 "+direct_sha,
       "- Kernel banner: "+full_banner,
       "- Official Pixel 8 shiba CP2A release: "+STOCK_RELEASE,
       "- Source GKI Module.symvers exported symbols: "+str(len(exports)),
       "- Direct available .ko files: "+str(len(modules)),
       "- Modules inspected: "+str(len(inspected)),
       "- Module vermagic mismatches within research build: "+str(len(vermagic_bad)),
       "- CRC matches compared with *research GKI* exports: "+str(compare_count),
       "- CRC disagreements in inspected research modules: "+str(mismatch_count),
       "- DTBO file exists: "+str(dtbo["present"]),
       "- DTBO Android table header valid: "+str(dtbo.get("header_valid")),
       "- DTBO table entries: "+str(dtbo.get("entry_count","NOT INSPECTED")),
       "",
       "## Remaining physical-device blockers",
       "- No reference CP2A kernel Module.symvers or stock vendor modules; imported",
       "  symbol CRCs and actual runtime ABI equivalence are NOT proven.",
       "- Full CP2A kernel release suffix, source patch delta, shiba panel/DTBO",
       "  overlays, functional GPU/touch, USB recovery and AVB/rollback unverified.",
       "- No rootfs storage plan or on-device Linux boot test performed.",
       "- The CI output includes hashes and bounded text metadata, NOT kernel",
       "  images, vendor images or a flashable payload.",
       "",
       "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (args.out/"U31_OFFLINE_ABI_BOARD_AUDIT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))
    if mismatch_count:
        die("real experimental module CRC mismatches found, not a green ABI audit")
    if vermagic_bad:
        die("real experimental module vermagic mismatches found")
    if dtbo["present"] and not dtbo.get("header_valid"):
        die("invalid DTBO table header from experimental dist")
    if not inspected:
        print("U31 NOTE: no direct .ko accessible in Bazel output; module "
              "CRC evidence is incomplete and remains NO-GO.")

if __name__=="__main__":
    main()
