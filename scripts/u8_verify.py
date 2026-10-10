#!/usr/bin/env python3
"""U8 image/reference verification; NOT a Pixel8 boot or flash test."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path

HUSKY_SHA="3ef1f4e6675ffef522d939e5bb7dd9fdb06c6da60cde784b4ec7fe14e99dff9f"
U6_SHA="d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e"
U7_SHA="66d4c4f5f797d3809dfbe58b7ba2840daf697cf5aa4f54c42de28f52f86dbe6b"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def checked(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError("Command failed: "+ " ".join(map(str,cmd))+" "+r.stderr[-200:])
    return r.stdout

def husky(p):
    if sha(p)!=HUSKY_SHA: raise RuntimeError("Upstream ZIP SHA differs")
    result={}
    with zipfile.ZipFile(p) as z:
        if z.testzip(): raise RuntimeError("Reference ZIP CRC failure")
        files={Path(i.filename).name:i for i in z.infolist() if not i.is_dir()}
        for name in ("boot_a.img","init_boot_a.img","vendor_boot_a.img",
                     "vendor_kernel_boot_a.img","dtbo_a.img"):
            if name not in files or files[name].file_size>140*1024*1024:
                raise RuntimeError("Bad husky reference member "+name)
            b=z.read(files[name])
            d={"size":len(b),"sha256":hashlib.sha256(b).hexdigest()}
            if name in ("boot_a.img","init_boot_a.img"):
                if b[:8]!=b"ANDROID!" or struct.unpack_from("<I",b,40)[0]!=4:
                    raise RuntimeError("Bad reference Android v4 boot header")
                d["android_boot_header"]=4
            result[name]=d
    return result

def volume(p):
    if sha(p)!=U6_SHA or p.stat().st_size!=2147483648:
        raise RuntimeError("U6 ext4 hash/size mismatch")
    raw=checked(["dumpe2fs","-h",str(p)])
    fields={}
    for row in raw.splitlines():
        if ":" in row:
            k,v=row.split(":",1)
            fields[k.strip()]=v.strip()
    if fields.get("Filesystem volume name")!="SHIBA_UBUNTU":
        raise RuntimeError("Unexpected ext4 label")
    uuid=fields.get("Filesystem UUID","")
    fmt=r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    if not re.fullmatch(fmt,uuid): raise RuntimeError("Bad ext4 UUID")
    osrel=checked(["debugfs","-R","cat /usr/lib/os-release",str(p)])
    if "ID=ubuntu" not in osrel or "VERSION_CODENAME=resolute" not in osrel:
        raise RuntimeError("Wrong Ubuntu rootfs identity")
    def present(name):
        r=subprocess.run(["debugfs","-R","stat "+name,str(p)],capture_output=True,text=True)
        return "Inode:" in r.stdout and "not found" not in r.stderr
    return {"uuid_in_offline_image":uuid,"label":"SHIBA_UBUNTU",
            "sbin_init_inode":present("/sbin/init"),
            "systemd_inode":present("/usr/lib/systemd/systemd")}

def initcheck(p):
    s=p.read_text()
    for marker in ("u8.rootuuid=","u8.research_gate=I_UNDERSTAND_THIS_IS_UNVERIFIED",
                   "mount -t ext4 -o ro,noload","SHIBA_UBUNTU",
                   "VERSION_CODENAME=resolute","switch_root /newroot /sbin/init"):
        if marker not in s: raise RuntimeError("U8 init missing feature: "+marker)
    for forbidden in ("mkfs.","fastboot ","mount -o rw","dd if="):
        if forbidden in s: raise RuntimeError("Forbidden init token: "+forbidden)
    if s.index("mount -t proc proc /proc")>s.index("cat /proc/cmdline"):
        raise RuntimeError("U8 proc read before proc mount")
    checked(["sh","-n",str(p)])
    return {"static_guards_checked":True,"executed_under_real_kernel":False}

def model():
    good=["u8.rootuuid=12345678-1234-1234-1234-123456789abc",
          "u8.research_gate=I_UNDERSTAND_THIS_IS_UNVERIFIED"]
    def valid(xs):
        uu=[x[12:] for x in xs if x.startswith("u8.rootuuid=")]
        return len(uu)==1 and xs.count(good[1])==1 and bool(re.fullmatch(
          r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",uu[0]))
    test={"allowed":valid(good),"missing_uuid":not valid(good[1:]),
          "missing_optin":not valid(good[:1]),"duplicate":not valid(good+[good[0]]),
          "wrong_uuid":not valid(["u8.rootuuid=userdata",good[1]])}
    if not all(test.values()): raise RuntimeError("Policy model failed")
    return test

def main():
    a=argparse.ArgumentParser()
    for x in ("root_img","u7_init_boot","husky_zip","init_script","ramdisk","out"):
        a.add_argument("--"+x.replace("_","-"),type=Path,required=True)
    z=a.parse_args()
    z.out.mkdir(parents=True,exist_ok=True)
    if sha(z.u7_init_boot)!=U7_SHA: raise RuntimeError("U7 reference hash mismatch")
    b=z.u7_init_boot.read_bytes()
    if b[:8]!=b"ANDROID!" or struct.unpack_from("<I",b,40)[0]!=4:
        raise RuntimeError("Wrong U7 reference image")
    if z.ramdisk.stat().st_size<100000: raise RuntimeError("New cpio missing")
    ref,fs,gates,tests=husky(z.husky_zip),volume(z.root_img),initcheck(z.init_script),model()
    result={"status":"PASS_STATIC_RESEARCH_NOT_BOOTABLE","husky_zip_used_as_reference":True,
       "u7_uses_husky_kernel":False,"husky_reference":ref,"u6_ext4":fs,
       "u7_initboot_sha256":U7_SHA,"u8_cpio_sha256":sha(z.ramdisk),
       "u8_cpio_size":z.ramdisk.stat().st_size,"guards":gates,"mock_checks":tests,
       "real_rootfs_handoff_executed":False,"flashable":False,"bootable":False,
       "blockers":["Current EvolutionX kernel/vendor KMI unknown",
          "Linux filesystem has no verified phone-side volume mapping",
          "initramfs not yet tested in real kernel or emulator",
          "vendor_boot/DTBO/AVB/display/GPU/touch not integrated"]}
    (z.out/"U8_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Ubuntu U8 guarded rootfs handoff — offline audit",
       "","**PASS static checks, NOT bootable and NOT flashable.**",
       "- Husky official ZIP used for layout reference, NOT for U7 kernel.",
       "- U7 source: earlier experimental Google shusky CI kernel.",
       "- U6 ext4 label SHIBA_UBUNTU / UUID inside offline image: "+fs["uuid_in_offline_image"],
       "- /sbin/init inode: "+str(fs["sbin_init_inode"]),
       "- /usr/lib/systemd/systemd inode: "+str(fs["systemd_inode"]),
       "- U8 ramdisk SHA256: "+sha(z.ramdisk),
       "- First-stage shell syntax and static safety markers passed.",
       "- "+str(len(tests))+" parameter-policy model tests passed.",
       "- No actual mount or switch_root was executed.",
       "","## Blockers"]+["- "+v for v in result["blockers"]]+["","**DO NOT FLASH.**"]
    (z.out/"U8_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))

if __name__=="__main__":main()
