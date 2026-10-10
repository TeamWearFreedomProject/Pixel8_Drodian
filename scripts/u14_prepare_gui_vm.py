#!/usr/bin/env python3
"""U14: inject a REAL ARM64 Labwc GUI smoke test into a DISPOSABLE QEMU rootfs copy.
The verified U6 original is immutable; no Pixel 8 firmware, phone or data touched.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

SOURCE_SHA = "d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e"
SOURCE_UUID = "d6b067e7-31e4-4aa3-8edf-d7e70fec0747"
SERVICE = """[Unit]
Description=U14 true ARM64 Labwc/Wayland headless GUI handshake VM-only
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/bin/sh /etc/u14_gui_vm.sh
TimeoutStartSec=85
StandardOutput=journal+console
StandardError=journal+console
"""
TARGET = """[Unit]
Description=U14 Labwc headless test target (virtual machine ONLY)
DefaultDependencies=no
Requires=u14-gui.service
After=u14-gui.service
AllowIsolate=yes
"""

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(4*1024*1024), b""):
            h.update(buf)
    return h.hexdigest()

def execute(argv):
    a=subprocess.run(argv, text=True, capture_output=True)
    if a.returncode:
        raise RuntimeError(f"{argv} exit {a.returncode}\n{a.stderr[-1200:]}")
    return a.stdout

def dbfs(img, cmd, writable=False):
    argv=["debugfs"]
    if writable: argv.append("-w")
    argv.extend(["-R",cmd,str(img)])
    p=subprocess.run(argv,capture_output=True,text=True)
    if p.returncode or any(w in (p.stdout+p.stderr) for w in
        ("File not found by ext2_lookup","Filesystem not open","File exists while","Ext2 inode is invalid","Command not found")):
        raise RuntimeError("debugfs "+cmd+": "+(p.stdout+p.stderr)[-1000:])
    return p.stdout

def put(img,src, dest):
    a=dbfs(img,f"write {src} {dest}",True)
    if "Allocated inode:" not in a:
        raise RuntimeError("debugfs write did not allocate target "+dest+": "+a[-600:])
    if "Inode:" not in dbfs(img,f"stat {dest}"):
        raise RuntimeError("missing written inode "+dest)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--u6",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--probe",type=Path,required=True)
    p.add_argument("--gui-script",type=Path,required=True)
    a=p.parse_args()
    a.work.mkdir(parents=True,exist_ok=True)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.u6.stat().st_size != 2_147_483_648 or sha(a.u6)!=SOURCE_SHA:
        raise SystemExit("U6 original size/hash mismatch")
    meta=execute(["dumpe2fs","-h",str(a.u6)])
    if not re.search(r"Filesystem UUID:\s+"+SOURCE_UUID,meta) or not re.search(
        r"Filesystem volume name:\s+SHIBA_UBUNTU",meta):
        raise SystemExit("Original U6 ext4 UUID/label mismatch")
    for directory in ("/usr/bin","/etc","/etc/systemd/system"):
        if "Inode:" not in dbfs(a.u6,"stat "+directory):
            raise SystemExit("Missing target directory: "+directory)
    if a.probe.stat().st_size < 10000:
        raise SystemExit("Unexpectedly small ARM64 C probe")
    shutil.copyfile(a.u6,a.output)
    for name,txt in (("u14-gui.service",SERVICE),("u14-gui.target",TARGET)):
        tmp=a.work/name
        tmp.write_text(txt)
        dest="/etc/systemd/system/"+name
        put(a.output,tmp,dest)
        if dbfs(a.output,"cat "+dest).strip()!=txt.strip():
            raise RuntimeError("unit content differs: "+name)
    put(a.output,a.gui_script,"/etc/u14_gui_vm.sh")
    if dbfs(a.output,"cat /etc/u14_gui_vm.sh").strip()!=a.gui_script.read_text().strip():
        raise RuntimeError("GUI script differs")
    dest="/usr/bin/u14-wayland-probe"
    put(a.output,a.probe,dest)
    # debugfs write defaults to nonexecutable; ensure executable inode and verify.
    dbfs(a.output,f"sif {dest} mode 0100755",True)
    stat=dbfs(a.output,f"stat {dest}")
    if not re.search(r"Mode:\s+0755\b",stat):
        raise RuntimeError("ARM64 probe executable mode incorrect: "+stat[-700:])
    fsck=subprocess.run(["e2fsck","-f","-n",str(a.output)],
                        text=True,capture_output=True)
    if fsck.returncode not in (0,1):
        raise RuntimeError("U14 VM ext4 audit: "+fsck.stdout[-1100:]+fsck.stderr[-400:])
    if sha(a.u6)!=SOURCE_SHA:
        raise RuntimeError("Original U6 modified! Refusing success")
    status={
        "status":"U14_VM_ONLY_FILESYSTEM_READY",
        "original_u6_sha256":SOURCE_SHA,
        "virtual_test_rootfs_sha256":sha(a.output),
        "original_unchanged":True,
        "gui_executable":"/usr/bin/labwc",
        "gui_backend":"wlroots headless / pixman",
        "proof_binary":dest,
        "proof_binary_sha256":sha(a.probe),
        "systemd_target":"u14-gui.target",
        "phone_ubuntu_boot_tested":False,
        "gui_display_pixel8_verified":False,
        "flashable":False
    }
    (a.work/"U14_VM_ROOTFS_PREP.json").write_text(json.dumps(status,indent=2)+"\n")
    print(json.dumps(status,indent=2))

if __name__=="__main__":main()
