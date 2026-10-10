#!/usr/bin/env python3
"""U10: strict source/boot compatibility readiness, no hardware access."""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

SOURCE = {
    "shusky": "56006ae8162db285e776d85319d9942945b87194",
    "zuma": "fba447c6317f23501dbac209b6479e458800c449",
}
U7_BOOT_SHA = "1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa"
SHIBA_KERNEL_SHA = "8a3ec09cfc307e1f17b868437201b5e6f87a80840cc21bff8aea85e333db8229"

def sha(data): return hashlib.sha256(data).hexdigest()

def source_check(root):
    evidence=[]
    for name,commit in SOURCE.items():
        path=root/name
        got=subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],
                                    text=True).strip()
        if got!=commit: raise SystemExit(name+" source revision drifted")
    checks=[
        ("shusky","device-shiba.mk",("TARGET_LINUX_KERNEL_VERSION := 6.1","TARGET_KERNEL_DEVICE := shusky")),
        ("shusky","evolution.dependencies",("LineageOS/android_device_google_shusky-kernels","lineage-23.2")),
        ("zuma","BoardConfig-common.mk",("BOARD_PREBUILT_BOOTIMAGE","AB_OTA_UPDATER := true")),
    ]
    for name,path,terms in checks:
        text=(root/name/path).read_text()
        for item in terms:
            if item not in text: raise SystemExit("Source marker absent "+name+"/"+path+": "+item)
        evidence.append({"source":name,"path":path,"matches":list(terms)})
    return evidence

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",type=Path,required=True)
    p.add_argument("--boot",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    x.out.mkdir(parents=True,exist_ok=True)
    source=source_check(x.sources)
    raw=x.boot.read_bytes()
    if sha(raw)!=U7_BOOT_SHA: raise SystemExit("U7 experimental boot sha mismatch")
    if len(raw)<4096 or raw[:8]!=b"ANDROID!": raise SystemExit("No boot magic")
    version=struct.unpack_from("<I",raw,40)[0]
    length=struct.unpack_from("<I",raw,8)[0]
    if version!=4 or not (1_000_000 < length < 48_000_000):
        raise SystemExit("Unacceptable boot version/kernel length")
    kernel=raw[4096:4096+length]
    if sha(kernel)!=SHIBA_KERNEL_SHA:
        raise SystemExit("Experimental shiba kernel digest differs")
    gates={
        "public_evolution_x_android16_source_referenced":True,
        "experimental_u7_boot_header_structure_verified":True,
        "experimental_shiba_kernel_content_pinned":True,
        "installed_phone_exact_rom_fingerprint_known":False,
        "installed_phone_kernel_vendor_module_kmi_verified":False,
        "shiba_dtbo_vendor_boot_and_avb_integration_verified":False,
        "real_phone_independent_linux_rootfs_volume_identified":False,
        "display_touch_mali_usb_c_drivers_tested":False,
        "flash_ready":False
    }
    result={
        "status":"SOURCE_GATE_PASS_DEVICE_INTEGRATION_BLOCKED",
        "sources":SOURCE,"source_markers":source,
        "u7_experimental_v4_boot_sha256":U7_BOOT_SHA,
        "u7_experimental_kernel_sha256":SHIBA_KERNEL_SHA,
        "u7_experimental_kernel_bytes":length,
        "u9_qemu_kernel_not_shiba":"6.6.89 generic virt machine; must never substitute into Pixel 8",
        "current_installed_evolution_x":"Android 16 (user report), exact build fingerprint unknown",
        "criteria":gates,
        "phone_operated":False,
        "bootable_pixel8_ubuntu":False,
        "flashable":False
    }
    (x.out/"U10_SHIBA_READINESS.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# U10 — Pixel 8 shiba integration readiness (offline only)","",
           "**Verified U7 v4 research boot structure and Android16 public source markers; device boot is STILL BLOCKED.**",
           "",
           "- U7 experimental shiba v4 boot payload SHA-256 verified.",
           "- Android16 Evolution X public source shusky and zuma commits pinned.",
           "- Installed device running kernel/vendor KMI is unknown.",
           "- Vendor boot, DTBO, security, display, touch and GPU still not integrated.",
           "- U9 generic ARM64 QEMU kernel is not Tensor G3 compatible.",
           "",
           "## Gates"]
    lines += ["- "+k.replace("_"," ")+": "+str(v) for k,v in gates.items()]
    lines += ["","**NOT FLASHABLE; NO PHONE WAS ACCESSED.**"]
    (x.out/"U10_SHIBA_READINESS.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))

if __name__=="__main__":main()
