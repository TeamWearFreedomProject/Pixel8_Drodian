#!/usr/bin/env python3
"""U4 static source audit. Reads pinned code; creates text reports only."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SOURCES = {
    "huskyfe": ("Tenser-Linux/huskyfe", "be5ea37b183a2ab1f4a8f00278d515de281a5928"),
    "glproxy": ("Tenser-Linux/glproxy", "67be2bd259500b5d65a1e6e28d7110282800f522"),
    "vkproxy": ("Tenser-Linux/vkproxy", "155a11982a271b237e6b1dc4118ff3d5229fce88"),
    "shusky_legacy": ("Evolution-XYZ-Devices/device_google_shusky",
                      "78c56e881b7e88b7f027445b10cf4bbb0faa5a6a"),
}

TESTS = [
    ("DRM/KMS", "huskyfe", "src/main.cpp",
     ["/dev/dri/card0", "drmModeGetResources", "drmModeGetConnector", "drmModeSetCrtc"],
     "Direct DRM/KMS output design; not shiba compatibility."),
    ("Single connector at startup", "huskyfe", "src/main.cpp",
     ["res->count_connectors", "DRM_MODE_CONNECTED", "conn = c; break;"],
     "Selects first connected output on startup; no verified dynamic multi-monitor switching."),
    ("Evdev touch", "huskyfe", "src/Input.cpp",
     ["/dev/input/event%d", "ABS_MT_POSITION_X", "ABS_MT_POSITION_Y", "EVIOCGBIT"],
     "Probes raw Linux multitouch events; device/permissions are unknown on shiba."),
    ("OpenGL Mali dependency", "glproxy", "server/egl_init.c",
     ["/vendor/lib64/egl/libGLES_mali.so", "dlopen(MALI_PATH"],
     "Calls Android-side Mali blob via Bionic proxy, not a native Linux DRM GPU driver."),
    ("Vulkan Mali dependency", "vkproxy", "server/vk_init.c",
     ["/vendor/lib64/egl/libGLES_mali.so", "dlopen(DRIVER_PATH", "hwvulkan"],
     "Loads vendor Mali/HAL support; vendor ABI unverified."),
    ("Shiba board", "shusky_legacy", "shiba/BoardConfig.mk",
     ["TARGET_BOOTLOADER_BOARD_NAME := shiba", "TARGET_SCREEN_DENSITY := 420",
      "exynos_drm.load_sequential=1"],
     "Shiba-specific Android identity, density and shared DRM module; tree from 2024."),
    ("Husky board", "shusky_legacy", "husky/BoardConfig.mk",
     ["TARGET_BOOTLOADER_BOARD_NAME := husky", "TARGET_SCREEN_DENSITY := 480",
      "exynos_drm.load_sequential=1"],
     "Husky identity/density differ; shared DRM config does not imply image compatibility."),
    ("Legacy DisplayPort property", "shusky_legacy", "device-shiba.mk",
     ["persist.vendor.usb.displayport.enabled=1"],
     "Historical device-property example, NOT proof of native Ubuntu external display."),
    ("Shiba panel data", "shusky_legacy", "device-shiba.mk",
     ["panel_config_google-bigsurf_cal0.pb",
      "panel_config_google-shoreline_cal0.pb"],
     "Legacy shiba panel configuration files; native DRM/DT pairing still unresolved."),
]

BLOCKERS = [
    "No Pixel 8 shiba-specific, tested Ubuntu boot/initramfs or rootfs-mount implementation.",
    "Current Evolution X Android 16 kernel and matching vendor modules/KMI not identified.",
    "No shiba DRM panel, input-event or GPU device-node initialization demonstrated.",
    "Mali Bionic proxy cannot be assumed compatible with the current vendor environment.",
    "USB-C external display on stock Android is real, but native Linux hotplug unverified.",
    "Neither Phosh nor Labwc has a validated automatic touch-to-PC session switch.",
    "Only static CI experiments; no validated bootable or flashable image.",
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    arg = p.parse_args()
    arg.out.mkdir(parents=True, exist_ok=True)
    revisions = {}
    for key, (repo, expected) in SOURCES.items():
        folder = arg.sources / key
        got = subprocess.check_output(
            ["git", "-C", str(folder), "rev-parse", "HEAD"], text=True).strip()
        if got != expected:
            raise SystemExit("Pinned upstream source changed: " + key)
        revisions[key] = {"sha": got, "url": "https://github.com/" + repo}
    findings = []
    for title, repo_key, file, needles, interpretation in TESTS:
        path = arg.sources / repo_key / file
        if not path.is_file():
            raise SystemExit("Missing source file: " + str(path))
        content = path.read_text(encoding="utf-8", errors="replace")
        evidence = []
        for needle in needles:
            where = next((n for n, line in enumerate(content.splitlines(), 1)
                          if needle in line), None)
            if where is None:
                raise SystemExit("Required source marker missing: " + str((repo_key, file, needle)))
            evidence.append({"line": where, "text_marker": needle})
        remote, sha = SOURCES[repo_key]
        findings.append({
            "title": title, "source_repo": repo_key, "path": file,
            "url": "https://github.com/" + remote + "/blob/" + sha + "/" + file,
            "source_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "evidence": evidence, "interpretation": interpretation,
            "status": "SOURCE_MARKERS_CONFIRMED; NOT TESTED ON DEVICE"
        })
    audit = {
        "status": "SOURCE_AUDIT_SUCCESS_NO_HARDWARE",
        "target": "Google Pixel 8 shiba native Ubuntu 26.04 ARM64",
        "current_rom_user_report": "Android 16 Evolution X",
        "historical_references_are_not_current_rom": True,
        "hardware_tests": 0, "bootable": False, "flashable": False,
        "u3_userspace_tarball_sha256": "40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a",
        "revisions": revisions, "findings": findings, "blockers": BLOCKERS,
        "pixel_usb_c_external_output": (
            "Google June 2024 official Pixel Feature Drop confirms Pixel8/8a/8Pro "
            "wired USB-C display support under Android; Ubuntu unsupported/unverified.")
    }
    (arg.out / "U4_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    lines = [
        "# Pixel 8 Ubuntu U4 static display/input/GPU readiness audit",
        "",
        "**PASS: pinned source markers checked. NOT A BOOTABLE PORT. NO DEVICE OPERATIONS.**",
        "",
        "## Exact upstream revisions",
    ]
    for name, rec in revisions.items():
        lines.append("- " + name + ": [" + rec["sha"] + "](" + rec["url"] + "/commit/" + rec["sha"] + ")")
    lines.extend(["", "## Source findings"])
    for finding in findings:
        marks = ", ".join(x["text_marker"] + " (line " + str(x["line"]) + ")"
                          for x in finding["evidence"])
        lines.extend(["", "### " + finding["title"],
                      "- [" + finding["source_repo"] + "/" + finding["path"] + "](" + finding["url"] + ")",
                      "- Markers found: " + marks,
                      "- Interpretation: " + finding["interpretation"]])
    lines.extend([
        "", "## Verified external context",
        "- Google officially enabled Pixel 8/8a/8 Pro USB-C wired external displays in the June 2024 Pixel Feature Drop.",
        "- https://blog.google/intl/ja-jp/products/devices-services/pixel-feature-drop-june-2024/",
        "- The Android feature does NOT imply a Linux display driver, dual display, or desktop switching works.",
        "", "## Blockers"
    ])
    lines.extend("- " + blocker for blocker in BLOCKERS)
    lines.extend([
        "", "## Readiness decision",
        "- Ubuntu U3 .tar.xz remains a compressed userspace archive, NOT userdata.img.",
        "- No working shiba-specific Ubuntu bootloader handoff, initramfs, panel/DT, GPU or vendor KMI has been tested.",
        "- FAIL readiness for flashing: do NOT make or use flashable files based on U3/U4.",
        "- Next (research only): determine matching kernel/vendor source provenance and evaluate a safe initramfs/GUI architecture.",
        "", "**BUILD ONLY — NO ADB/FASTBOOT/PHONE/FLASH.**"
    ])
    (arg.out / "U4_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
