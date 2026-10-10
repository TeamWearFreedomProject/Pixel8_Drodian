#!/usr/bin/env python3
"""U10: assert a systemd service actually ran in QEMU, not just a PID1 banner."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    for key in ("log","u6","guest_rootfs","kernel","initramfs","out"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    data=args.log.read_text(errors="replace")
    seen={
        "linux_kernel_started":"Linux version 6.6.89" in data,
        "u8_first_stage_started":"U10_INIT_STARTED" in data,
        "u8_switch_root_reached":"U10_REACHED_SWITCH_ROOT" in data,
        "ubuntu_systemd_appeared":"systemd[1]" in data or "Welcome to Ubuntu" in data,
        "guest_systemd_unit_executed":"U10_SYSTEMD_VM_SERVICE_EXECUTED" in data,
        "ubuntu_login_prompt_observed":"login:" in data,
    }
    required=tuple(k for k in seen if k!="ubuntu_login_prompt_observed")
    status="SUCCESS" if all(seen[k] for k in required) else "INCOMPLETE"
    result={
        "status":status,
        "systemd_unit_is_real_guest_execution":bool(seen["guest_systemd_unit_executed"]),
        "checks":seen,
        "u6_source_sha256":sha(args.u6),
        "disposable_guest_rootfs_sha256":sha(args.guest_rootfs),
        "generic_qemu_kernel_sha256":sha(args.kernel),
        "guest_repacked_initramfs_sha256":sha(args.initramfs),
        "actual_pixel8_hardware_boot":False,
        "flashable_firmware":False,
        "user_installed_evolutionx_kernel_vendor_kmi":"UNKNOWN",
        "native_phone_screen_touch_gpu":"NOT TESTED",
    }
    (args.out/"U10_ASSERT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# U10 — Ubuntu userspace integration under QEMU ARM64",
           "",
           f"**{status}: VM boot and isolated systemd service check; NOT PIXEL8 HARDWARE.**",
           "",
           "## Observed VM serial stages"]
    for k,v in seen.items():
        lines.append(f"- {k.replace('_',' ')}: {v}")
    lines.extend(["","## Source integrity",
       "- Untouched U6 source rootfs SHA256: "+result["u6_source_sha256"],
       "- Disposable QEMU rootfs copy SHA256: "+result["disposable_guest_rootfs_sha256"],
       "- Generic QEMU kernel SHA256: "+result["generic_qemu_kernel_sha256"],
       "- Repacked VM initramfs SHA256: "+result["guest_repacked_initramfs_sha256"],
       "",
       "## Unresolved Pixel 8 integration barriers",
       "- Exact running Evolution X Android16 kernel/vendor KMI not verified.",
       "- Correct shiba DTBO, boot/vendor_boot/vendor_kernel_boot and AVB handoff not integrated.",
       "- No safe, identified Pixel 8 Linux rootfs partition exists.",
       "- No panel/touch/Mali bridge/USB-C display/power test.",
       "- QEMU-only unit is not a phone boot service and is not included in original U6.",
       "- No Pixel 8 image suitable for flashing was produced.",
       "","**BUILD ONLY — DO NOT FLASH.**"])
    (args.out/"U10_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    if status!="SUCCESS": raise SystemExit("U10 VM service marker not observed; refusing success claim")

if __name__=="__main__": main()
