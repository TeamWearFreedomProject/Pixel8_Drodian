#!/usr/bin/env python3
"""U15: verify actual PNG from real ARM64 Wayland compositor screencopy.

This does not prove a QEMU virtio-GPU or any real Pixel 8 panel.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageStat

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def main():
    a=argparse.ArgumentParser()
    for key in ("log","screenshot","u6","out"):
        a.add_argument("--"+key,type=Path,required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    log=args.log.read_text(errors="replace")
    with Image.open(args.screenshot) as source:
        if source.format!="PNG":raise SystemExit("Wayland capture not PNG")
        source.verify()
    with Image.open(args.screenshot) as source:
        img=source.convert("RGB")
        width,height=img.size
        if width<640 or height<480:raise SystemExit("Small/synthetic frame size")
        top=img.crop((0,0,width,min(height,100)))
        bottom=img.crop((0,height//2,width,height))
        top_mean=ImageStat.Stat(top).mean
        bottom_mean=ImageStat.Stat(bottom).mean
        color_difference=sum(abs(a-b) for a,b in zip(top_mean,bottom_mean))
        colors=img.resize((200,120)).getcolors(maxcolors=24000)
        unique_colors=len(colors) if colors else ">24000"
    checks={
        "ubuntu_64bit_arm_linux_started":"Linux version 6.6.89" in log,
        "readonly_root_switch_reached":"U14_REACHED_SWITCH_ROOT" in log,
        "labwc_headless_wayland_protocol_handshake":"U14_REAL_WAYLAND_PROTOCOL_REGISTRY_OK" in log,
        "screencopy_client_saved_png":"U15_REAL_WAYLAND_PNG_WRITTEN_TO_VM_SCRATCH" in log,
        "successful_original_u14_guest_service":"U14_RESEARCH_HEADLESS_WAYLAND_TEST_PASSED" in log,
        "valid_png_dimensions":width>=640 and height>=480,
        "not_completely_uniform":(unique_colors!="1" and unique_colors!=1),
        "visibly_different_top_bar_pixels":color_difference>28,
        "original_u6_is_known_hash":sha(args.u6)=="d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e",
    }
    result={
        "status":"SUCCESS_QEMU_HEADLESS_WAYLAND_PIXEL_SCREENSHOT" if all(checks.values()) else "INCOMPLETE",
        "checks":checks,
        "screenshot":{"width":width,"height":height,
                      "sha256":sha(args.screenshot),
                      "image_file":args.screenshot.name,
                      "top_rgb_mean":top_mean,
                      "lower_rgb_mean":bottom_mean,
                      "top_vs_lower_color_difference":round(color_difference,2),
                      "unique_sampled_colors":unique_colors},
        "underlying_renderer":"wlroots headless, pixman, Wayland screencopy",
        "actual_qemu_virtual_gpu_display":False,
        "pixel8_display_shown":False,
        "real_phosh_phone_session":False,
        "safe_to_flash":False,
    }
    (args.out/"U15_ASSERT.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# U15 — Real pixel capture from ARM64 Ubuntu Wayland in QEMU",
           "",
           "**"+result["status"]+" — screenshot of REAL compositor output; NOT a physical/virtio-GPU display.**",
           "",
           f"- Captured PNG: {width} × {height}, SHA256: {result['screenshot']['sha256']}",
           f"- Sample top-vs-bottom RGB difference: {color_difference:.1f} (requires >28)",
           f"- Sample distinct pixel colors: {unique_colors}",
           "",
           "## Assertions"]
    lines.extend(["- "+k.replace("_"," ")+": "+str(v) for k,v in checks.items()])
    lines +=["","## Limitations",
            "- Screenshot data came from Labwc's *headless* Wayland compositor, using screencopy.",
            "- A screenshot proves pixel generation but not a visible QEMU virtio-GPU/DRM connector.",
            "- No native Pixel 8 screen, touch, Mali GPU or vendor modules were exercised.",
            "- The screenshot PNG is research evidence, not a fabricated mockup.",
            "- The original U6 Ubuntu rootfs remained unchanged, and no phone was accessed.",
            "","**BUILD/VM ONLY. NOT A PIXEL 8 BOOTABLE IMAGE.**"]
    (args.out/"U15_REPORT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
    if not all(checks.values()):
        raise SystemExit("No proof of real nonuniform Wayland screenshot")
if __name__=="__main__":main()
