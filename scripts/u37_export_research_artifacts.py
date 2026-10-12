#!/usr/bin/env python3
"""U37: fail-closed publishing of verified research images to Actions artifacts.
No ADB, fastboot, real devices, firmware flashing or user data access.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

EXPECTED="EXPERIMENTAL_BOOT_INITBOOT_AND_UBUNTU_BASE_PACKAGING_OFFLINE_PASS"
OPTIONAL=("dtbo.img","vendor_kernel_boot.img","vendor_boot.img","vendor_dlkm.img","system_dlkm.img")

def deny(message):
    raise SystemExit("U37 EXPORT GATE DENIED: "+message)

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def export(src, dest, note, manifest):
    if not src.is_file() or src.is_symlink():
        deny("required regular file unavailable: "+str(src))
    if src.stat().st_size==0:
        deny("empty research image: "+str(src))
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dest)
    if sha256(src)!=sha256(dest):
        deny("export checksum mismatch: "+dest.name)
    manifest.append({
        "file":dest.name,
        "bytes":dest.stat().st_size,
        "sha256":sha256(dest),
        "source":str(src),
        "note":note,
        "flash_tested":False,
        "stock_CP2A_verified":False
    })

def main():
    p=argparse.ArgumentParser()
    for name in ("report","lab","dist","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    audit=json.loads(a.report.read_text())
    if audit.get("phase")!="U35" or audit.get("status")!=EXPECTED:
        deny("U35 source-based, full build and header-validation PASS missing")
    if audit.get("physical_Pixel8_flash_gate")!="DENY":
        deny("prior physical flash-denial gate absent")
    if audit.get("kernel_release")!="6.1.157-android14-11":
        deny("source GKI kernel release unexpected")
    if audit.get("hardware_boot_verified") or audit.get("boot_or_flash_safe"):
        deny("unexpected real hardware success claim")
    for typ in ("boot_img_lab","init_boot_img_lab"):
        if audit.get(typ,{}).get("header_version")!=4:
            deny("experimental Android header v4 proof missing")

    startup=a.out/"startup-images"
    rootfs=a.out/"ubuntu-rootfs"
    report=a.out/"reports"
    for d in (startup,rootfs,report):
        d.mkdir(parents=True,exist_ok=True)
    items=[]
    export(a.lab/"boot-U35-LAB-NOT-FLASHABLE.img",startup/"boot.img",
           "experimental Android v4 GKI kernel ONLY, not Pixel8 boot approved",items)
    export(a.lab/"init_boot-U35-LAB-NOT-FLASHABLE.img",startup/"init_boot.img",
           "experimental Android v4 BusyBox diagnostic initramfs ONLY",items)
    export(a.lab/"U35-ARM64-STAGE0-initramfs.cpio.gz",startup/"initramfs.cpio.gz",
           "AArch64 diagnostic initramfs without Ubuntu handoff",items)
    export(a.dist/"Image",startup/"Image",
           "source-built research 6.1.157 kernel",items)
    packed=a.dist/"Image.lz4"
    if not packed.is_file():
        packed=a.lab/"U35_FROM_VERIFIED_SOURCE_GKI_Image.lz4"
    export(packed,startup/"Image.lz4",
           "research kernel compressed from source Image",items)
    published=[]
    absent=[]
    for name in OPTIONAL:
        src=a.dist/name
        if src.is_file() and not src.is_symlink():
            export(src,startup/name,
                   "OPTIONAL research shusky dist output; stock CP2A compatibility unproven",items)
            published.append(name)
        else:
            absent.append(name)
    export(a.lab/"ubuntu-U35-LAB-NOT-USERDATA.img",rootfs/"ubuntu.img",
           "Ubuntu Base 26.04.1 arm64 ext4 1GiB, NOT Pixel8 userdata.img",items)
    item={i["file"]:i for i in items}
    for name, expected in (
        ("boot.img",audit["boot_img_lab"]["file_sha256"]),
        ("init_boot.img",audit["init_boot_img_lab"]["file_sha256"]),
        ("initramfs.cpio.gz",audit["init_boot_img_lab"]["ramdisk_sha256"]),
        ("Image",audit["raw_research_GKI_Image_sha256"]),
        ("Image.lz4",audit["compressed_research_GKI_Image_lz4_sha256"]),
        ("ubuntu.img",audit["Ubuntu_Base_ext4_lab_image_sha256"])
    ):
        if item[name]["sha256"]!=expected:
            deny("byte-level U35 certified output mismatch: "+name)

    metadata={
        "phase":"U37",
        "status":"RESEARCH_BINARY_ARTIFACT_EXPORT_CHECKSUM_PASS",
        "published_to":"temporary GitHub Actions artifact, not a Release",
        "research_platform":"Google Pixel 8 shiba research only; no hardware tested",
        "ubuntu":"Ubuntu Base 26.04.1 ARM64, no graphical desktop",
        "real_device_flash_gate":"DENY",
        "stock_CP2A_module_CRCs_verified":False,
        "stock_device_dtbo_panel_verified":False,
        "AVB_rollback_verified":False,
        "Ubuntu_switch_root_or_GUI_implemented":False,
        "actual_Pixel8_boot_tested":False,
        "files":items,
        "optional_dist_published":published,
        "optional_dist_absent":absent
    }
    notice=(
       "# U37 Research files only — NOT FOR FLASHING\n\n"
       "These are experimental, incomplete boot/Ubuntu images, NOT an "
       "installable Pixel 8 Ubuntu ROM. NO real phone was used.\n\n"
       "boot.img has only a source GKI kernel; init_boot.img has only "
       "a diagnostic BusyBox shell, with NO functional handoff to Ubuntu.\n"
       "ubuntu.img is a generic 1 GiB ext4 Ubuntu Base ARM64 filesystem, "
       "NOT an Android userdata partition image, desktop, or installer.\n"
       "Optional compiled DTBO and vendor images have NOT been matched to "
       "Pixel 8 stock CP2A vendor CRCs, board panel, Android AVB, or recovery.\n"
       "No Tensor Linux Pixel 8 Pro husky binaries were used.\n\n"
       "These images MUST NOT be installed or written to a Pixel 8. "
       "Hardware-boot/flash safety gate: DENY.\n"
    )
    for d in (startup,rootfs):
        (d/"READ_ME_FIRST_NOT_FLASHABLE.md").write_text(notice)
        selected=[i for i in items if (d/i["file"]).is_file()]
        (d/"SHA256SUMS.txt").write_text(
            "".join(i["sha256"]+"  "+i["file"]+"\n" for i in selected))
        (d/"U37_MANIFEST.json").write_text(json.dumps(metadata,indent=2)+"\n")
    (report/"U37_REPORT.json").write_text(json.dumps(metadata,indent=2)+"\n")
    (report/"U37_REPORT.md").write_text(
        "# U37 research artifact export\n\n"
        "Source build U35 and SHA256 of every published image verified.\n\n"
        "Published optional dist images: "+(", ".join(published) or "none")+"\n\n"
        "Absent optional dist images: "+(", ".join(absent) or "none")+"\n\n"
        "Experimental files are NOT installable. **REAL DEVICE FLASH GATE: DENY.**\n")
    print("U37 research artifact export PASS:", len(items),"SHA256-verified binaries")
    print("Published optional dist:",published)
    print("Absent optional dist:",absent)
    print("REAL DEVICE FLASH GATE: DENY")

if __name__=="__main__":
    main()
