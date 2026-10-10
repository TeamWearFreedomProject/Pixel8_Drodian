#!/usr/bin/env python3
"""Strict evidence levels for U16 QEMU-only virtio-gpu DRM and Labwc proof.
Success never implies a real Pixel 8 Linux boot, GPU driver, or display.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageStat

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(4*1024*1024), b""): h.update(data)
    return h.hexdigest()

def check_png(path):
    if not path.is_file():
        return {"present": False}
    with Image.open(path) as im:
        if im.format != "PNG":
            return {"present": False, "error": "not PNG"}
        rgb = im.convert("RGB")
        width, height = rgb.size
        colors = rgb.resize((200, 120)).getcolors(maxcolors=24000)
        color_count = len(colors) if colors is not None else 24001
        upper = ImageStat.Stat(rgb.crop((0, 0, width, min(100, height)))).mean
        lower = ImageStat.Stat(rgb.crop((0, height//2, width, height))).mean
        difference = sum(abs(a-b) for a,b in zip(upper,lower))
        return {"present": True, "width": width, "height": height,
                "sampled_colors": color_count, "top_bottom_rgb_delta": round(difference,2),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "meaningful_content": width >= 640 and height >= 480 and color_count > 8 and difference > 28}

def main():
    p=argparse.ArgumentParser()
    for name in ("log","guest_png","host_png","u6","report_dir"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    a.report_dir.mkdir(parents=True,exist_ok=True)
    log=a.log.read_text(errors="replace") if a.log.exists() else ""
    guest=check_png(a.guest_png)
    host=check_png(a.host_png)
    checks={
        "qemu_linux_kernel_booted": "Linux version 6.6.89" in log,
        "guarded_ubuntu_rootfs_handoff": "U14_REACHED_SWITCH_ROOT" in log,
        "virtio_gpu_kernel_device": "U16_DRM_CARD_PRESENT" in log and "U16_VIRTIO_GPU_DRIVER_VERIFIED" in log,
        "drm_connector_connected": "U16_DRM_CONNECTOR_CONNECTED" in log,
        "seatd_session_ready": "U16_SEATD_READY" in log,
        "drm_backend_requested": "U16_LABWC_DRM_ATTEMPT" in log,
        "labwc_wayland_client_handshake": "U16_DRM_WAYLAND_PROTOCOL_OK" in log,
        "guest_drm_wayland_png": guest.get("meaningful_content",False) and "U16_DRM_WAYLAND_PNG_SERIALIZED" in log,
        "host_virtual_display_png": host.get("meaningful_content",False),
        "original_u6_sha256_unchanged": a.u6.is_file() and sha256_file(a.u6)=="d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e",
    }
    if all(checks.values()):
        status="PASS_QEMU_VIRTIO_DRM_LABWC_AND_VIRTUAL_DISPLAY"
    elif checks["virtio_gpu_kernel_device"] and checks["drm_connector_connected"]:
        status="PARTIAL_DRM_KERNEL_ONLY"
    elif checks["qemu_linux_kernel_booted"]:
        status="PARTIAL_QEMU_BOOT_ONLY"
    else:
        status="NOT_VERIFIED"
    summary={
      "status":status, "checks":checks,
      "guest_wayland_frame":guest,"host_qemu_display_frame":host,
      "qemu_virtual_gpu_type":"virtio-gpu 2D (NOT Google Tensor GPU)",
      "pixman_software_renderer":True,
      "phone_display_verified":False,"phone_touched":False,"safe_to_flash":False,
    }
    (a.report_dir/"U16_ASSERT.json").write_text(json.dumps(summary,indent=2)+"\n")
    report=["# U16 — QEMU virtual DRM display experiment","",
            "**"+status+"**","","## Independent checks"]
    report += ["- "+("PASS" if v else "UNPROVEN")+" — "+k for k,v in checks.items()]
    report += ["","## Scope / limitations",
               "- DRM connected connector and distinct client PNG + QEMU display PNG required for full result.",
               "- A Wayland socket alone is insufficient; host QEMU screenshot must show nonuniform rendered pixels.",
               "- This test uses a **generic QEMU ARM64 kernel**, **virtio-gpu 2D**, **Labwc/Pixman**.",
               "- Pixel 8 Tensor G3 GPU/display/touch/Android partitions were never tested or modified.",
               "- VM-only artifacts; **NOT FLASHABLE**.",""]
    (a.report_dir/"U16_REPORT.md").write_text("\n".join(report))
    print("\n".join(report))
    if status!="PASS_QEMU_VIRTIO_DRM_LABWC_AND_VIRTUAL_DISPLAY":
        raise SystemExit(1)

if __name__=="__main__":
    main()
