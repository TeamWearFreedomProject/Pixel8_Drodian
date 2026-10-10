#!/usr/bin/env python3
"""U10 offline-only: prepare a copy of the actual U6 ext4 image for QEMU.

Creates VM-specific, no-login systemd proof units inside a throwaway ext4
copy using debugfs. Never edits the source U6 image or touches a phone.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

SOURCE_SHA = "d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e"
REQUIRED_UUID = "d6b067e7-31e4-4aa3-8edf-d7e70fec0747"

SERVICE = """[Unit]
Description=U10 QEMU systemd PID1 execution proof (VM ONLY)
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo U10_SYSTEMD_VM_SERVICE_EXECUTED > /dev/console"
RemainAfterExit=yes
StandardOutput=journal+console
StandardError=journal+console
"""

TARGET = """[Unit]
Description=U10 isolated systemd start target (VM ONLY)
DefaultDependencies=no
Requires=u10-vm-smoke.service
After=u10-vm-smoke.service
AllowIsolate=yes
"""

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def run(args):
    p = subprocess.run(args, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f"{args!r} exit={p.returncode}\n{p.stderr[-1600:]}")
    return p.stdout + p.stderr

def debugfs(image, cmd, writable=False):
    args = ["debugfs"]
    if writable:
        args.append("-w")
    args += ["-R", cmd, str(image)]
    text = run(args)
    if any(x in text for x in ("File not found by ext2_lookup", "Filesystem not open",
                               "File exists while", "Ext2 inode is invalid")):
        raise RuntimeError("debugfs error: " + text[-500:])
    return text

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--u6",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    a=p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    if sha(a.u6)!=SOURCE_SHA: raise SystemExit("Input U6 image SHA256 mismatch")
    if a.u6.stat().st_size!=2_147_483_648: raise SystemExit("Unexpected U6 IMG size")
    hdr=run(["dumpe2fs","-h",str(a.u6)])
    if f"Filesystem UUID:          {REQUIRED_UUID}" not in hdr:
        if not re.search(r"Filesystem UUID:\s+"+re.escape(REQUIRED_UUID), hdr):
            raise SystemExit("Unexpected U6 filesystem UUID")
    if not re.search(r"Filesystem volume name:\s+SHIBA_UBUNTU",hdr):
        raise SystemExit("Unexpected U6 filesystem label")
    if "Inode:" not in debugfs(a.u6,"stat /etc/systemd/system"):
        raise SystemExit("No systemd unit directory in input rootfs")
    # Preserve original and create disposable VM-only copy, never modify U6 source.
    shutil.copyfile(a.u6,a.output)
    for name,data in (("u10-vm-smoke.service",SERVICE),("u10-vm-smoke.target",TARGET)):
        src=a.work/name
        src.write_text(data)
        text=debugfs(a.output,f"write {src} /etc/systemd/system/{name}",True)
        if "Allocated inode:" not in text: raise RuntimeError("Not injected: "+name+" "+text)
        test=debugfs(a.output,f"cat /etc/systemd/system/{name}")
        if data.strip()!=test.strip(): raise RuntimeError("Roundtrip failed: "+name)
    run(["e2fsck","-f","-n",str(a.output)])
    if sha(a.u6)!=SOURCE_SHA: raise RuntimeError("Source U6 was modified")
    meta={"original_u6_sha256":SOURCE_SHA,
          "vm_overlay_sha256":sha(a.output),
          "offline_uuid":REQUIRED_UUID,
          "modified_source_u6":False,
          "vm_test_target":"u10-vm-smoke.target",
          "service_proof_marker":"U10_SYSTEMD_VM_SERVICE_EXECUTED",
          "rootfs_actual_pixel8_compatible":False,
          "virtual_machine_only":True}
    (a.work/"U10_ROOTFS_PREP.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
