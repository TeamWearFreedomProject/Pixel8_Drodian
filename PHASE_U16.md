# Phase U16 — real QEMU virtual DRM/KMS display via virtio-GPU

**STATUS: EXPERIMENT PENDING. BUILD + QEMU ONLY; NEVER FLASH OR BOOT ON PIXEL 8.**

## Goal

Extend the fully verified [U15](PHASE_U15.md) ARM64 Ubuntu 26.04 Labwc/Pixman
headless Wayland screenshot experiment to a true QEMU virtual display
backed by the guest Linux virtio_gpu DRM/KMS driver.

A passing CI must demonstrate all of the following, not merely a virtual
screen socket:

1. ARM64 Linux 6.6.89 kernel compiled from SHA256-pinned official upstream
   source with CONFIG_DRM_VIRTIO_GPU=y and tested QEMU boot drivers.
2. Real QEMU virtio-gpu-device 2D device recognized as /dev/dri/card0,
   bound to Linux virtio_gpu driver, with a connected DRM connector.
3. Labwc launched with WLR_BACKENDS=drm, WLR_DRM_DEVICES=/dev/dri/card0,
   WLR_RENDERER=pixman; seat handled by disposable VM-only ARM64 seatd.
   Must respond to real Wayland protocol probe. No headless fallback.
4. Waybar paints the compositor; grim captures its actual Wayland output.
5. Independent QEMU HMP screendump captures host-visible virtio-GPU
   scanout via a local Unix monitor socket; both PNG images must have
   nonuniform pixel content and substantial top-vs-lower color difference.
6. Strict assertions check original U6 SHA256 and every guest device,
   protocol, and pixel condition. Missing evidence = not verified.

## Safety and reproducibility

- Reuse SHA256-pinned original U6 Ubuntu 26.04 ARM64 ext4 rootfs UNCHANGED.
  Operate on a disposable copy attached read-only in QEMU.
- Reuse pinned U8 guarded QEMU initramfs with VM-only progress markers.
- Compile generic upstream QEMU-only 6.6.89 with DRM: NOT a shiba kernel.
  Nothing is packaged as an Android boot image.
- VNC binds only 127.0.0.1 on ephemeral GitHub runner; guest has -nic none.
  HMP runs on private local Unix socket. No connection to real phone.
- Guest uses volatile /run and /tmp RAM scratch, not writable phone userdata.
- No Pixel 8, ADB, fastboot, flash, bootloader or user-data changes.
- No claim about Tensor G3, Mali graphics, Pixel panel/touch,
  physical DRM, vendor driver ABI or a bootable Ubuntu phone.

## Implementation

- [U16 workflow](.github/workflows/phase-u16-virtio-gpu-drm-vm.yml)
- [U16 guest](scripts/u16_gui_drm_vm.sh)
- [Disposable guest rootfs builder](scripts/u16_prepare_vm.py)
- [QEMU GPU scanout collector](scripts/u16_hmp_screendump.py)
- [DRM Wayland PNG recovery](scripts/u16_recover_serial_png.py)
- [Strict verifier](scripts/u16_assert_drm.py)

This document triggers the initial U16 branch CI.
**U16 SUCCESS remains UNVERIFIED until actual logs and image artifacts pass.**

## U16 Run #4 — actual QEMU device detection failed

- [Run #4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38091302024) completed the full 6.6.89 DRM kernel build, retrieved ARM64 seatd/grim, prepared a disposable rootfs, and booted Ubuntu 26.04 systemd in QEMU. SHA256 source rootfs stayed unchanged.
- The guest printed `U16_FAIL_DRM_CARD_ABSENT`: there was no /dev/dri/card0 and /sys/class/drm only had `version`. Therefore **virtio-GPU was NOT recognized** and Labwc DRM/PNG capture were never attempted; the final assertion correctly reported `PARTIAL_QEMU_BOOT_ONLY`.
- Retry hypothesis (NOT proven yet): a **PCI virtio-GPU** attachment may be discovered where the earlier virtio-mmio GPU was not. QEMU ARM `virt` documentation explicitly supports `virtio-gpu-pci` with built-in CONFIG_PCI / PCI_HOST_GENERIC / VIRTIO_PCI / DRM_VIRTIO_GPU.
- This change switches **only the QEMU peripheral** to virtio-gpu-pci and captures PCI/virtio sysfs plus expanded kernel probe diagnostics. It **does not claim the PCI path works until the VM logs prove it**.
- No Pixel device, GPU vendor driver, Android boot image, flashing, or data writes.
