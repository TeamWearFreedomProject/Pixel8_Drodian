# Ubuntu Phase U4 — shiba DRM, touch, GPU and external-monitor feasibility

**BUILD ONLY — STATIC SOURCE ANALYSIS — NOT BOOTABLE — NOT FLASHABLE**

## Context

Target: Google Pixel 8 (`shiba`) running native Ubuntu 26.04 ARM64,
with a touch-oriented Phosh session on the phone and a Labwc PC desktop
on a future external monitor.

As of 2026-10-10 the user reports **Android 16 Evolution X** currently on
the Pixel 8. Earlier factory Android 17 `CP3A.260905.009` firmware
and kernel `6.1.162-android14-11` were separately inspected but must
**not** be assumed to match the current ROM's kernel, vendor API or KMI.

## Important: there is no image ready for device operations

- [U1](PHASE_U1_RESULTS.md) built a small Ubuntu arm64 **minbase tarball**.
- [U2](PHASE_U2_RESULTS.md) compared old husky Tensor Linux and Google
  experimental shiba boot images; did not establish image compatibility.
- [U3](PHASE_U3_RESULTS.md) built a genuine Ubuntu arm64 userspace
  **tar.xz** with Phosh/Phoc/Stevia and Labwc/Waybar/Foot/Kanshi.
- **Compressed tar.xz is not a userdata.img file.** A Linux filesystem
  partition layout, actual mountable filesystem image, matching kernel,
  initramfs, hardware initialization and boot path would need to be
  independently designed and verified. This project does NOT supply them.

## Source-based findings

1. **Wired external-display hardware support is real under Android.**
   Google announced USB-C wired display support on Pixel 8/8a/8 Pro
   with the June 2024 Pixel Feature Drop.
   [Google's Japanese announcement](https://blog.google/intl/ja-jp/products/devices-services/pixel-feature-drop-june-2024/).
   This **does not** prove DRM/DisplayPort Alt Mode works from Ubuntu.
2. **Tensor Linux HuskyFE uses direct DRM/KMS** via `/dev/dri/card0`,
   `drmModeGetResources` and `drmModeGetConnector`. Its initial code
   picks the first connected connector then breaks the loop. An
   automatic two-display laptop-style arrangement is **not** established.
   [Upstream source](https://github.com/Tenser-Linux/huskyfe/blob/be5ea37b183a2ab1f4a8f00278d515de281a5928/src/main.cpp).
3. **HuskyFE touch probing uses raw Linux evdev input**, inspecting
   `/dev/input/event*`, `EVIOCGBIT` and multitouch ABS positions.
   This is not by itself proof that shiba Linux exports the expected
   touchscreen events. [Input.cpp](https://github.com/Tenser-Linux/huskyfe/blob/be5ea37b183a2ab1f4a8f00278d515de281a5928/src/Input.cpp).
4. **OpenGL/Vulkan proxy depends on Android Mali vendor userspace.**
   `glproxy` and `vkproxy` source loads
   `/vendor/lib64/egl/libGLES_mali.so` on the Bionic-facing side.
   No current Evolution X ABI match was tested.
   [glproxy egl_init.c](https://github.com/Tenser-Linux/glproxy/blob/67be2bd259500b5d65a1e6e28d7110282800f522/server/egl_init.c) /
   [vkproxy vk_init.c](https://github.com/Tenser-Linux/vkproxy/blob/155a11982a271b237e6b1dc4118ff3d5229fce88/server/vk_init.c).
5. **Board config is not identical between husky and shiba**.
   An older 2024 Evolution X device tree has different bootloader
   board names and density values (shiba=420; husky=480), plus
   `exynos_drm.load_sequential=1`. Its old shiba product file has
   `persist.vendor.usb.displayport.enabled=1`; this is merely an
   obsolete source-level clue, not validated current Android16 firmware.
   [2024 shiba tree](https://github.com/Evolution-XYZ-Devices/device_google_shusky/tree/udc/shiba)
   / [2024 husky tree](https://github.com/Evolution-XYZ-Devices/device_google_shusky/tree/udc/husky).

## CI audit

[U4 GitHub Action](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u4-source-audit.yml)
uses [Python source auditor](scripts/phase_u4_source_audit.py) to
verify exact pinned GitHub source commits, check representative source
patterns and output `U4_AUDIT.json` and `U4_REPORT.md`.

This is **static code inspection**, not compilation or testing of
actual GPU/display hardware. Source snippets are attributed to
their respective upstream authors; do not assert this repository
implemented the original Tensor Linux driver/GUI.

A one-time run is requested by this plan's addition; otherwise
use GitHub Actions **Run workflow**.

## Readiness gates for a future U5 (still build-only)

- Identify the **matching** native boot/vendor kernel/modules, especially
  if using current Evolution X Android16 firmware as a reference.
- Describe a recoverable kernel → initramfs → mountable Ubuntu rootfs path,
  without producing unverified flashable images.
- Confirm shiba panel and touchscreen initialization support by suitable
  source-based evidence.
- Validate the exact Mali Bionic library and graphics/display integration,
  not just that `glproxy` compiles for husky.
- Design genuine two-display behavior: outputs, compositor selection,
  session continuity, pointer/keyboard vs touchscreen.
- Obtain review of hardware-facing assumptions before any device trial.

**No ADB, fastboot, bootloader, partitions, flash operations or Pixel
hardware tests are authorized in U4.**
