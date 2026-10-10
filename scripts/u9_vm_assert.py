#!/usr/bin/env python3
"""U9 offline QEMU boot-log verifier.

Log assertion is NOT evidence that Pixel 8 can boot Ubuntu.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

def digest(path):
    s=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            s.update(part)
    return s.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--negative",required=True,type=Path)
    p.add_argument("--positive",required=True,type=Path)
    p.add_argument("--rootfs",required=True,type=Path)
    p.add_argument("--kernel",required=True,type=Path)
    p.add_argument("--initramfs",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    negative=a.negative.read_text(errors="replace")
    positive=a.positive.read_text(errors="replace")
    expected_neg="U8 HALT: requires exactly one u8.rootuuid"
    negative_pass=expected_neg in negative
    stage={
        "guest_kernel_console":bool(re.search(r"Linux version 6\.6\.",positive)),
        "early_init_started":"U9_INIT_STARTED" in positive,
        "rootfs_volume_readonly_mounted":"U9_ROOTFS_READONLY_MOUNTED" in positive,
        "ubuntu_os_identity_validated":"U9_UBUNTU_RELEASE_VERIFIED" in positive,
        "switch_root_about_to_execute":"U9_SWITCH_ROOT_ATTEMPT" in positive,
        "systemd_pid1_observed":bool(re.search(r"systemd\[1\]|Welcome to Ubuntu",positive)),
        "ubuntu_login_prompt_observed":bool(re.search(r"login:\s*$",positive,re.M))
    }
    if not negative_pass:
        raise SystemExit("QEMU negative test did not report missing UUID rejection")
    if not stage["guest_kernel_console"] or not stage["early_init_started"]:
        raise SystemExit("QEMU guest Linux/initramfs did not reach early init")
    if not stage["rootfs_volume_readonly_mounted"] or not stage["ubuntu_os_identity_validated"]:
        raise SystemExit("QEMU did not verify read-only mount of the actual Ubuntu U6 rootfs")
    if not stage["switch_root_about_to_execute"]:
        raise SystemExit("QEMU never reached the intended switch_root execution path")
    if not stage["systemd_pid1_observed"]:
        raise SystemExit("QEMU has not demonstrated that systemd became PID1")
    results={
        "result":"PASS_QEMU_AARCH64_KERNEL_TO_INITRAMFS_TO_SYSTEMD",
        "negative_missing_uuid_gate":negative_pass,
        "positive_stage_markers":stage,
        "real_qemu_kernel_boot":True,
        "real_ext4_mount_readonly_in_qemu":True,
        "rootfs_handoff_systemd_observed":True,
        "qemu_generic_kernel_sha256":digest(a.kernel),
        "u9_initramfs_sha256":digest(a.initramfs),
        "u6_ext4_sha256":digest(a.rootfs),
        "pixel8_device_tested":False,
        "pixel8_bootable":False,
        "flashable":False,
        "limits":[
            "QEMU virt kernel and virtio block are NOT Tensor G3 drivers",
            "No Pixel 8 current Evolution X vendor KMI or DTBO match",
            "No Pixel 8 firmware, verified boot or rootfs partition mapping",
            "No Pixel 8 screen/touch/GPU/USB-C/power hardware test"
        ]
    }
    (a.out/"U9_RESULTS.json").write_text(json.dumps(results,indent=2)+"\n")
    lines=["# U9 — QEMU ARM64 actual kernel boot and Ubuntu rootfs handoff",
           "",
           "**PASS: generic emulated ARM64 boot, NOT Pixel 8 firmware.**",
           "",
           "- Missing UUID rejected in guest: "+str(negative_pass)]
    lines += ["- "+k.replace("_"," ")+": "+str(v) for k,v in stage.items()]
    lines += ["","- Kernel SHA256: "+results["qemu_generic_kernel_sha256"],
              "- U9 initramfs SHA256: "+results["u9_initramfs_sha256"],
              "- U6 ext4 SHA256: "+results["u6_ext4_sha256"],
              "","## What the test cannot show"]
    lines += ["- "+k for k in results["limits"]]
    lines += ["","**NO PHONE ACTIONS, NO FLASHABLE IMAGE.**"]
    (a.out/"U9_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))

if __name__=="__main__":main()
