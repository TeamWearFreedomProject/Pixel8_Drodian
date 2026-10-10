# Phase U14 — real Ubuntu 26.04 ARM64 Labwc GUI startup in QEMU (headless only)

**BUILD AND VIRTUAL-MACHINE TEST ONLY. NO PIXEL 8 FLASHING.**

## Deadline and goal

The project's immediate goal is to launch a real GUI session. A fully
working **Pixel 8 native screen** by 2026-10-11 noon Japan time is **not
established or guaranteed**: the phone's kernel/vendor module ABI, display,
touch, GPU, secure boot and safe on-phone root filesystem are unverified.

The nearest independently testable milestone is for the **real Ubuntu ARM64
userspace installed in U6** to launch **Labwc**, an actual Wayland GUI
compositor, under the same real generic ARM64 QEMU VM kernel that passed U10.

U14 deliberately sets `WLR_BACKENDS=headless`,
`WLR_RENDERER=pixman`, and `WLR_HEADLESS_OUTPUTS=1`; successful startup
would prove only a **headless Wayland session**, NOT rendered pixels on the
Pixel 8 or on an actual virtual video display.

## Existing verified, unchanged inputs

- Original **2 GiB Ubuntu 26.04 ARM64 rootfs from U6**:
  `d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e`.
  Includes actual native ARM64 Labwc 0.9.3, Waybar and Phosh packages,
  although only Labwc is the direct U14 runtime target.
- Guarded **U8 static BusyBox ARM64 initramfs**:
  `dc50919b6a4e89dc8c27d84dee5335105c756573ef3dcf74c3465a414e50372b`.
- **Generic QEMU-only ARM64 Linux kernel** from U9:
  `718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc`.
- All three are fetched from previous successful Actions and independently
  SHA256 checked. Not a Pixel 8 firmware kernel.

## Technical test

1. Copy U6 rootfs to a **disposable virtual-machine ext4 IMG**, never touch
   the U6 source, and inject an isolated `u14-gui.target`,
   `u14-gui.service`, and [GUI test shell](scripts/u14_gui_vm.sh)
   using offline `debugfs` operations.
2. Build a **statically linked ARM64 probe** from
   [u14_wayland_probe.c](scripts/u14_wayland_probe.c) and place it only in
   the disposable QEMU rootfs. It connects to the real Wayland Unix socket,
   issues `wl_display.get_registry` and requires a real
   `wl_registry.global` response from the compositor.
3. Boot genuine AArch64 Linux in `qemu-system-aarch64 -M virt`, with a
   **read-only** virtio Ubuntu disk and U8's exact UUID research gate.
4. Have systemd run `labwc` under a **headless wlroots backend**, with
   `pixman` software rendering; no Android vendor GPU or real hardware
   screen devices are available in this test.
5. The verifier rejects success unless the actual guest serial log shows
   Linux startup, guarded `switch_root`, the systemd GUI service, Labwc's
   Wayland Unix socket, and the **real Wayland protocol registry reply**.
   Merely installing Labwc or creating a socket is insufficient.
6. Save guest serial log and evidence reports as **small GitHub Artifacts**,
   not rootfs firmware, payloads or bootable phone partitions.

## Sources

- [U14 QEMU GUI Action](.github/workflows/phase-u14-wayland-gui-vm.yml)
- [Temporary Ubuntu rootfs preparation](scripts/u14_prepare_gui_vm.py)
- [Actual Labwc startup script](scripts/u14_gui_vm.sh)
- [Independent Wayland protocol probe](scripts/u14_wayland_probe.c)
- [Guest serial evidence auditor](scripts/u14_assert_gui_vm.py)

Even if U14 succeeds, **a headless compositor is not a visible GUI**.
A further test using a QEMU virtual DRM/virtio GPU (and ultimately shiba
hardware) is needed before saying a screen displays anything.

**NO FLASHABLE PIXEL 8 UBUNTU IMAGE. DO NOT FLASH.**
