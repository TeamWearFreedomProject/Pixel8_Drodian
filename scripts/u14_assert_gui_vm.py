#!/usr/bin/env python3
"""U14 strict guest serial evidence, never confuse headless with phone display."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    for a in ("log","u6","guest_rootfs","kernel","initramfs","out"):
        p.add_argument("--"+a.replace("_","-"),type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    s=args.log.read_text(errors="replace")
    tests={
        "generic_arm64_linux_kernel_booted":"Linux version 6.6.89" in s,
        "u8_initramfs_executed":"U14_FIRST_STAGE_STARTED" in s,
        "readonly_ubuntu_root_handoff_reached":"U14_REACHED_SWITCH_ROOT" in s,
        "systemd_started_gui_service":"U14_GUEST_LABWC_TEST_STARTED" in s,
        "labwc_process_was_attempted":"U14_STARTING_REAL_LABWC_HEADLESS_BACKEND" in s,
        "wayland_socket_created":"U14_REAL_WAYLAND_SOCKET_FOUND" in s,
        "real_wayland_registry_protocol_response":"U14_REAL_WAYLAND_PROTOCOL_REGISTRY_OK" in s,
        "labwc_and_handshake_succeeded":"U14_GUI_HEADLESS_COMPOSITOR_AND_WAYLAND_OK" in s,
        "headless_smoke_service_passed":"U14_RESEARCH_HEADLESS_WAYLAND_TEST_PASSED" in s,
        "gui_failed_marker_absent":"U14_GUI_HEADLESS_COMPOSITOR_FAILED" not in s,
    }
    passed=all(tests.values())
    results={
        "status":"SUCCESS_HEADLESS_ARM64_LABWC_AND_WAYLAND" if passed else "INCOMPLETE",
        "checks":tests,
        "source_ubuntu_u6_sha256":sha(args.u6),
        "temporary_qemu_rootfs_sha256":sha(args.guest_rootfs),
        "generic_qemu_arm64_kernel_sha256":sha(args.kernel),
        "qemu_initramfs_sha256":sha(args.initramfs),
        "test_backend":"wlroots headless output, pixman, Unix Wayland protocol",
        "a_visible_framebuffer_was_shown":False,
        "a_phosh_shell_was_launched":False,
        "native_pixel8_display_touch_gpu_tested":False,
        "pixel8_linux_boot_success":False,
        "safe_to_flash":False,
        "no_phone_actions":True,
    }
    (args.out/"U14_ASSERT.json").write_text(json.dumps(results,indent=2)+"\n")
    lines=[
        "# U14 — real Ubuntu ARM64 Labwc GUI compositor smoke test under QEMU",
        "",
        "**"+results["status"]+" — VIRTUAL HEADLESS WAYLAND ONLY; NOT PIXEL 8 SCREEN OUTPUT.**",
        "",
        "## Guest-serial assertions",
    ]
    lines.extend(["- "+name.replace("_"," ")+": "+str(value) for name,value in tests.items()])
    lines += [
        "",
        "## SHA256 provenance",
        "- Original untouched U6 rootfs: "+results["source_ubuntu_u6_sha256"],
        "- Disposable U14 rootfs copy: "+results["temporary_qemu_rootfs_sha256"],
        "- Generic ARM64 QEMU kernel: "+results["generic_qemu_arm64_kernel_sha256"],
        "- VM-only guarded initramfs: "+results["qemu_initramfs_sha256"],
        "",
        "## What this DOES NOT prove",
        "- No pixels rendered to a real device/display, no native DRM connector or framebuffer verified.",
        "- No Phosh phone interface proved; Labwc uses wlroots *headless* backend.",
        "- No Google Tensor G3 kernel/vendor module or Pixel 8 display/touch proof.",
        "- No physical phone boot, no OTA firmware modification, no flashable image.",
        "",
        "**PIXEL 8 BOOTABLE GUI IS STILL NOT VERIFIED.**",
    ]
    (args.out/"U14_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    if not passed:
        raise SystemExit("QEMU GUI process / Wayland protocol milestone not proven")

if __name__=="__main__":main()
