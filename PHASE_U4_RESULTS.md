# Ubuntu Phase U4 results — Pixel 8 native display/GPU/touch source audit

**SUCCESS: reproducible static source audit; NOT BOOTABLE, NOT FLASHABLE, no device operations.**

- Completed: **2026-10-10**.
- [GitHub Actions U4 run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38045860598) — `success`.
- [U4 report artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38045860598/artifacts/11667394102)
  - `shiba-u4-static-source-audit-1`: **5,096 bytes**.
  - Expires **2026-11-09 10:43 UTC**.
  - Contains `U4_REPORT.md`, `U4_AUDIT.json` and `U4_SOURCES.txt` only.
- Script: [`scripts/phase_u4_source_audit.py`](scripts/phase_u4_source_audit.py).
- Source snapshots pinned to exact upstream GitHub commit SHAs (verified in CI):
  - [Tenser-Linux/huskyfe](https://github.com/Tenser-Linux/huskyfe/commit/be5ea37b183a2ab1f4a8f00278d515de281a5928)
  - [Tenser-Linux/glproxy](https://github.com/Tenser-Linux/glproxy/commit/67be2bd259500b5d65a1e6e28d7110282800f522)
  - [Tenser-Linux/vkproxy](https://github.com/Tenser-Linux/vkproxy/commit/155a11982a271b237e6b1dc4118ff3d5229fce88)
  - [Evolution X historical shusky device source, February 2024](https://github.com/Evolution-XYZ-Devices/device_google_shusky/commit/78c56e881b7e88b7f027445b10cf4bbb0faa5a6a) — **NOT current Android 16 Evolution X sources**.

## Nine verified static code patterns

1. HuskyFE directly accesses **`/dev/dri/card0` DRM/KMS** resources and modesetting functions.
2. Its startup code takes the **first connected DRM connector** in the inspected selection path; dual display/hotplug management is not demonstrated.
3. Touch input is probed through **raw Linux evdev** `/dev/input/event*`, requiring ABS multitouch X/Y capabilities.
4. glproxy loads **`/vendor/lib64/egl/libGLES_mali.so`** on its Android/Bionic-facing service side.
5. vkproxy also loads a vendor Mali library and uses the hwvulkan HAL interface.
6. Historical shiba board config has `TARGET_BOOTLOADER_BOARD_NAME := shiba`, `TARGET_SCREEN_DENSITY := 420` and `exynos_drm.load_sequential=1`.
7. Historical husky config has `TARGET_BOOTLOADER_BOARD_NAME := husky`, `TARGET_SCREEN_DENSITY := 480` and shared DRM module config.
8. Historical shiba source contains `persist.vendor.usb.displayport.enabled=1` — this is **not current-ROM proof** or Ubuntu DisplayPort confirmation.
9. Historical shiba device file lists distinct panel configuration blobs, including `google-bigsurf` and `google-shoreline`.

The CI report includes file references, source-line marker locations and SHA-256 hashes.

## Verified external hardware context

Google's [June 2024 Pixel Feature Drop announcement](https://blog.google/intl/ja-jp/products/devices-services/pixel-feature-drop-june-2024/) confirms wired USB-C display output on Pixel 8/8a/8 Pro **under Android**. This makes the external display goal hardware-plausible, not working under Ubuntu.

## Current prerequisites and blockers

| Requirement | U4 conclusion |
| --- | --- |
| Authentic ARM64 Ubuntu with two GUI package sets | **Available** from U3, but unbootable |
| Pixel 8 (`shiba`) kernel/vendor ABI matching | **Unverified** |
| Ubuntu boot/initramfs and rootfs mounting | **Not implemented** |
| Native DRM panel + touchscreen initialization | **Unverified** |
| Android Mali GPU library bridge matching current vendor | **Unverified** |
| USB-C display in native Ubuntu | **Unverified** |
| Touch-to-desktop mode switching | **Not implemented** |
| Safe flashable images | **None** |

Actual phone software (user-reported): **Evolution X Android 16**. The separately analyzed older Android 17 firmware and the 2024 Evolution device-tree branch do not establish compatibility with the phone's current kernel/vendor build.

## Decision and next research

**U4 audit succeeded but the OS is NOT READY TO FLASH.**

A `tar.xz` Ubuntu rootfs is an archive of files, not a userdata partition image. A matching boot path, trusted initramfs, filesystem layout, shiba-specific DRM/touch input initialization, power controls and graphics interface require separately verifiable design and testing.

Recommended U5 (build-only): source-level study of the exact current shiba Android16 kernel/vendor provenance and a safe, reviewable Ubuntu initramfs/system integration plan, plus offline compositor/monitor session design. No phone actions.

**NO ADB • NO FASTBOOT • NO DEVICE ACCESS • NO FLASHING • NO ROM IMAGES.**
