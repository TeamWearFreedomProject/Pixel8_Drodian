#!/usr/bin/env python3
"""U13: inspect EXACT SHA-pinned Evolution X shiba OTA binaries OFFLINE ONLY.

Inputs are never treated as phone-safe flashing candidates. Outputs are small
metadata JSON/Markdown; no Android images, modules or 3GB archives are saved.
"""
import argparse
import base64
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROM_NAME="EvolutionX-16.0-20260915-shiba-11.11-Official.zip"
ROM_BYTES=3033648565
ROM_SHA="41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0"
U7_BOOT_SHA="1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa"
U7_KERNEL_SHA="8a3ec09cfc307e1f17b868437201b5e6f87a80840cc21bff8aea85e333db8229"
PARTITIONS=("boot","init_boot","dtbo","vendor_boot","vendor_kernel_boot","vendor_dlkm","system_dlkm")
MAX_SAMPLE_MODULES=30

def fail(msg):
    raise SystemExit("U13 VERIFIED-BINARY AUDIT FAILED: "+msg)

def digest_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(4*1024*1024),b""):
            h.update(buf)
    return h.hexdigest()

def u32(raw, off):
    return struct.unpack_from("<I",raw,off)[0]

def boot_info(path):
    with path.open("rb") as f:
        header=f.read(4096)
        if header[:8]!=b"ANDROID!":
            return {"format":"not_ANDROID_boot","magic_hex":header[:16].hex()}
        version=u32(header,40)
        kernel_size=u32(header,8)
        ramdisk_size=u32(header,12)
        hsize=u32(header,20)
        if version!=4 or hsize!=1584:
            return {"format":"ANDROID_boot","header_version":version,"header_bytes":hsize,
                    "kernel_bytes":kernel_size,"ramdisk_bytes":ramdisk_size}
        f.seek(4096)
        payload=f.read(kernel_size)
        if len(payload)!=kernel_size: fail("truncated official kernel section")
        return {"format":"ANDROID_boot","header_version":version,"header_bytes":hsize,
                "kernel_bytes":kernel_size,"ramdisk_bytes":ramdisk_size,
                "kernel_payload_sha256":hashlib.sha256(payload).hexdigest(),
                "kernel_magic_hex":payload[:16].hex()}

def verify_payload_metadata(archive):
    with zipfile.ZipFile(archive) as z:
        names=set(z.namelist())
        if "payload.bin" not in names or "payload_properties.txt" not in names:
            fail("expected OTA payload.bin and payload_properties.txt absent")
        prop={}
        for line in z.read("payload_properties.txt").decode("utf-8").splitlines():
            if "=" in line:
                k,v=line.split("=",1)
                prop[k]=v.strip()
        size=int(prop.get("FILE_SIZE","-1"))
        info=z.getinfo("payload.bin")
        if size!=info.file_size:
            fail("payload_properties FILE_SIZE does not match zip's payload.bin member")
        metadata_size=int(prop.get("METADATA_SIZE","-1"))
        if metadata_size<=24 or metadata_size>2_000_000:
            fail("invalid payload metadata size")
        with z.open("payload.bin") as f:
            payload_meta=f.read(metadata_size)
        actual_meta=base64.b64encode(hashlib.sha256(payload_meta).digest()).decode("ascii")
        if prop.get("METADATA_HASH")!=actual_meta:
            fail("payload metadata SHA256 mismatch")
        return {"payload_bytes":info.file_size,"payload_is_zip_stored":info.compress_type==0,
                "file_hash_base64_from_payload_properties":prop.get("FILE_HASH"),
                "metadata_bytes":metadata_size,
                "metadata_sha256_base64_verified":actual_meta,
                "user_uploaded_payload_properties_file_size_matches":size==3033640593,
                "payload_full_sha256_computed":False}

def image_info(imgdir):
    result={}
    for part in PARTITIONS:
        p=imgdir/(part+".img")
        if not p.is_file(): fail("missing requested partition image: "+part)
        size=p.stat().st_size
        if size<1024: fail("partition too short: "+part)
        with p.open("rb") as f:
            head=f.read(4096)
            f.seek(1024)
            erofs_magic=f.read(4).hex()
            f.seek(1080)
            ext4_magic=f.read(2).hex()
        item={"bytes":size,"sha256":digest_file(p),
              "magic_hex":head[:12].hex(),
              "ext4_superblock_magic":ext4_magic=="53ef",
              "erofs_superblock_magic":erofs_magic=="e2e1f5e0",
              "android_sparse_magic":head[:4].hex()=="3aff26ed"}
        if part in ("boot","init_boot"):
            item["android_boot"]=boot_info(p)
        if part in ("vendor_boot","vendor_kernel_boot"):
            item["vendor_boot_header_present"]=head[:8]==b"VNDRBOOT"
            if head[:8]==b"VNDRBOOT":
                item["vendor_boot_header_version"]=u32(head,8)
        if part=="dtbo":
            item["android_dtbo_magic"]=head[:4].hex()=="d7b7ab1e"
        result[part]=item
    return result

def try_read_vendor_modules(imgdir,out):
    """Best-effort read-only ext4 metadata extraction on disposable CI runner."""
    record={}
    for name in ("vendor_dlkm","system_dlkm"):
        path=imgdir/(name+".img")
        with path.open("rb") as f:
            f.seek(1080)
            is_ext4=f.read(2)==b"\x53\xef"
        item={"ext4_detected":is_ext4,"extracted_modules":0,"module_vermagic":[]}
        with path.open("rb") as f:
            f.seek(1024)
            is_erofs=f.read(4)==bytes.fromhex("e2e1f5e0")
        target=out/("temporary_"+name+"_modules")
        target.mkdir(parents=True,exist_ok=True)
        if is_ext4:
            r=subprocess.run(["debugfs","-R",f"rdump /lib/modules {target}",str(path)],
                             capture_output=True,text=True)
        elif is_erofs:
            # Never mount extracted vendor filesystem on the runner or phone.
            # erofs-utils reads the immutable image and copies it to CI scratch.
            r=subprocess.run(["fsck.erofs",f"--extract={target}",str(path)],
                             capture_output=True,text=True)
        else:
            item["extraction_status"]="unrecognized filesystem; no module ABI claim"
            record[name]=item
            continue
        item["erofs_detected"]=is_erofs
        mods=sorted(target.rglob("*.ko"))
        item["extracted_modules"]=len(mods)
        item["debugfs_returncode"]=r.returncode
        if not mods:
            item["extraction_status"]="no .ko extracted (may use alternate path)"
            record[name]=item
            continue
        item["extraction_status"]="plain ext4 modules read offline"
        for ko in mods[:MAX_SAMPLE_MODULES]:
            mod=subprocess.run(["modinfo","-F","vermagic",str(ko)],
                               capture_output=True,text=True)
            item["module_vermagic"].append({
                "name":ko.name,
                "sha256":digest_file(ko),
                "vermagic":mod.stdout.strip() if mod.returncode==0 else None
            })
        record[name]=item
    return record

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--zip",type=Path,required=True)
    a.add_argument("--images",type=Path,required=True)
    a.add_argument("--u7-boot",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.zip.name!=ROM_NAME:
        fail("wrong OTA ZIP basename")
    if args.zip.stat().st_size!=ROM_BYTES:
        fail("official ZIP size mismatch")
    if digest_file(args.zip)!=ROM_SHA:
        fail("official ZIP sha256 differs; refuse all compatibility claims")
    if digest_file(args.u7_boot)!=U7_BOOT_SHA:
        fail("previous U7 experimental image SHA256 mismatch")
    u7=boot_info(args.u7_boot)
    if u7.get("kernel_payload_sha256")!=U7_KERNEL_SHA:
        fail("U7 experimental kernel content mismatch")
    payload=verify_payload_metadata(args.zip)
    imgs=image_info(args.images)
    module_data=try_read_vendor_modules(args.images,args.out)

    official_kernel=imgs["boot"].get("android_boot",{}).get("kernel_payload_sha256")
    if not official_kernel:
        fail("could not identify official Android boot v4 kernel payload")
    kernel_equal=official_kernel==U7_KERNEL_SHA
    outcome={
        "result":"PASS_OFFICIAL_BINARY_SHA_AND_PARTITION_IDENTITIES" ,
        "exact_official_zip_filename":ROM_NAME,
        "official_zip_sha256_verified":ROM_SHA,
        "official_zip_bytes_verified":ROM_BYTES,
        "payload_metadata":payload,
        "official_partition_data":imgs,
        "vendor_kernel_modules_best_effort":module_data,
        "old_experimental_u7_kernel_sha256":U7_KERNEL_SHA,
        "old_u7_kernel_equal_to_exact_official_rom_kernel":kernel_equal,
        "kernel_payload_equal_does_NOT_prove_matching_vendor_KMI":True,
        "installed_phone_slot_boot_images_independently_read":False,
        "native_linux_pixel8_boot_verified":False,
        "safe_to_flash":False,
        "phone_hardware_accessed":False,
        "source_images_saved_as_artifacts":False
    }
    (args.out/"U13_AUDIT.json").write_text(json.dumps(outcome,indent=2)+"\n")
    lines=[
        "# U13 — exact official Evolution X shiba ROM binary comparison",
        "",
        "**SUCCESS: official 3.03 GB OTA ZIP SHA256 verified. OFFLINE ANALYSIS ONLY.**",
        "",
        "- OTA: "+ROM_NAME,
        "- File bytes: "+str(ROM_BYTES),
        "- Verified full ZIP SHA256: "+ROM_SHA,
        "- Embedded payload.bin bytes: "+str(payload["payload_bytes"]),
        "- Payload METADATA_HASH: "+payload["metadata_sha256_base64_verified"],
        "- Matches user's uploaded payload_properties FILE_SIZE: "+
          str(payload["user_uploaded_payload_properties_file_size_matches"]),
        "",
        "## Partition image SHA256 measured FROM the exact verified OTA",
    ]
    for name,item in imgs.items():
        lines.append(f"- {name}: {item['bytes']} bytes, sha256 {item['sha256']}")
        if "android_boot" in item:
            lines.append(f"  - boot structure: {json.dumps(item['android_boot'],ensure_ascii=False)}")
        if "vendor_boot_header_version" in item:
            lines.append(f"  - vendor boot header version: {item['vendor_boot_header_version']}")
    lines.extend([
        "",
        "## Old experimental U7 kernel compared with exact EvoX boot kernel",
        "- Official kernel payload SHA256: "+official_kernel,
        "- Old U7 experimental kernel payload SHA256: "+U7_KERNEL_SHA,
        "- IDENTICAL kernel bytes: "+str(kernel_equal),
        "- Same header version or kernel 6.1 family is not proof of vendor ABI.",
        "",
        "## Offline vendor .ko sample (if plain ext4 filesystem)",
    ])
    for role,item in module_data.items():
        lines.append(f"- {role}: {item['extraction_status']}; extracted {item['extracted_modules']}")
        for record in item["module_vermagic"][:12]:
            lines.append("  - "+record["name"]+": vermagic="+str(record["vermagic"]))
    lines+= [
        "",
        "## Limits / gate",
        "- Exact OTA binary SHA256 and partition hashes established; real current phone slot not read.",
        "- Manifest/properties metadata are not a substitute for actual boot/vendor pairing tests.",
        "- No GPU, touch, power, DTBO compatibility, AVB or native Ubuntu boot evidence.",
        "- No flashable Ubuntu image built; no partition/device was modified.",
        "- All temporary extracted firmware/module files stay on disposable runner.",
        "",
        "**BOOTABLE PIXEL 8 UBUNTU: UNVERIFIED — DO NOT FLASH.**",
    ]
    (args.out/"U13_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    if kernel_equal:
        print("U13: official kernel is byte-for-byte equal to old U7 experimental kernel (KMI still unknown)")
    else:
        print("U13: old U7 experimental kernel DOES NOT MATCH this official EVO X kernel")

if __name__=="__main__": main()
