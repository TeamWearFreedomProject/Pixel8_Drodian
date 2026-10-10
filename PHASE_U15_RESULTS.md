# Phase U15 RESULTS — real GUI pixel screenshot generated inside Ubuntu ARM64/QEMU

**U15 SUCCESS: genuine 1280×720 Labwc/Waybar Wayland screenshot captured and independently verified.**

**NOT A PIXEL 8 DISPLAY. NOT VIRTIO-GPU/DRM OUTPUT. NOT FLASHABLE.**

## Successful run and exact evidence

- **2026-10-11 (JST):** [U15 GitHub Actions run #4 — SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38088180037)
- [Artifact ZIP with the ACTUAL `U15_wayland_screen.png`, console output and validation JSON](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38088180037/artifacts/11683090528)
  - Name: `shiba-u15-arm64-wayland-pixel-evidence-4`
  - ZIP size: **23,567 bytes**
  - Expires: **2026-11-09 21:37 UTC**
- [Workflow](.github/workflows/phase-u15-wayland-pixels-vm.yml) |
  [Guest compositor/capture](scripts/u15_gui_capture_vm.sh) |
  [Offline-only rootfs preparation](scripts/u15_prepare_gui_vm.py) |
  [Host PNG decoder](scripts/u15_recover_serial_png.py) |
  [Strict pixel validator](scripts/u15_assert_pixels.py).

## What actually happened

1. Used original SHA256-pinned U6 Ubuntu 26.04 AArch64 ext4 rootfs,
   Linux 6.6.89 **generic QEMU virt** kernel and guarded U8 initramfs.
   The U6 rootfs remained **read-only and unchanged**.
2. Prepared a disposable QEMU-only rootfs copy containing the ARM64
   `grim` Wayland screencopy client and an actual Waybar bar with
   high-contrast colored CSS. The original rootfs was not modified.
3. Booted a real ARM64 QEMU Linux guest. Ubuntu systemd started Labwc
   with wlroots **headless** backend and Pixman software rendering.
   The Wayland protocol probe received a real registry reply.
4. Ran actual ARM64 Waybar against the compositor, then the real ARM64
   `grim` process used the Wayland screenshot protocol. The resulting
   guest PNG was stored in /run RAM and encoded over QEMU serial.
5. The host reconstructed PNG from explicit bounded markers and verified
   format, dimensions, color distribution and screenshot SHA256.

## Actual QEMU screenshot measured in SUCCESS run

| Check | Observed |
| --- | --- |
| Screenshot file | `U15_wayland_screen.png` |
| PNG dimensions | **1280 × 720** |
| PNG bytes recovered via serial | **9,951** |
| Screenshot SHA256 | `4277bc767675f2fcb55b07411e3bccba59a87a5759dddc4028d0be1cae48ada8` |
| Distinct pixel colors in downsampled frame | **263** |
| Top panel vs lower frame summed mean RGB difference | **318.9** (required over 28) |
| Linux AArch64 kernel started | **PASS** |
| U8 switch-root completed | **PASS** |
| Labwc Wayland registry protocol response | **PASS** |
| Wayland PNG capture and exact data reconstruction | **PASS** |
| Screenshot is not a blank/uniform canvas | **PASS** |
| All CI validation checks | **PASS — GitHub Actions success** |

This is stronger than U14's headless compositor connection:
**authentic compositor pixel data has been recovered as a PNG**, and the
colored Waybar panel makes the visual output nonuniform.

## Correct interpretation and limitations

This remains a **headless screenshot from a Wayland compositor**, even
though it contains colored UI pixels. QEMU still ran with
`-display none`; there was **no virtio-GPU virtual display, DRM/KMS
connector, frame buffer passed to a monitor, or real phone screen**.
A visible QEMU GPU/VNC output would be a separate experiment.

There is NO proof of running Phosh as a phone interface, real Pixel 8
bootloader/kernel/vendor matching, board-specific DTBO, display or
touchscreen drivers, Tensor G3/Mali GPU, USB-C display or a safe phone
rootfs partition. U13 download of the exact official Evolution X binary
was blocked by CDN HTTP 403, so matching installed kernel/vendor module
pairing is still unresolved.

U15 does **not** provide a flashable Pixel 8 Ubuntu image.

## Retries and meaningful fixes

1. [Run #1 failed](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38087630867):
   default x86 apt source was mistakenly queried for ARM64 package
   indexes; ARM64 Ubuntu ports source isolation resolved it.
2. [Run #2 failed](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38087724563):
   Labwc/Wayland worked, but separate virtual screenshot disk was
   unexpectedly mounted read-only, so `grim` could not save a PNG.
3. [Run #3 screenshot succeeded but CI failed](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38087983960):
   genuine nonuniform 1280×720 Wayland PNG recovered from guest serial.
   Validator still required the old scratch-disk success marker instead
   of the new serial transport markers.
4. **[Run #4 PASS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38088180037)**:
   require new actual screenshot start/end serialization markers plus
   PNG decode and independent pixel checks. All passed.

## Next engineering gate

The natural U16 milestone is a genuinely **visible virtual GPU/DRM
display capture** under QEMU, distinct from headless screencopy. It will
likely require a dedicated QEMU kernel with `virtio-gpu` DRM built in,
and a compositor running on that DRM backend. Even a successful
virtual GPU test does **not** make this Ubuntu build bootable on Pixel 8.

**PIXEL 8 HARDWARE BOOT/GUI: NOT TESTED. DO NOT FLASH.**
