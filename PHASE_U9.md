# Phase U9 — real ARM64 QEMU Linux kernel → U8 initramfs → U6 Ubuntu rootfs

**VM ONLY • NO PIXEL HARDWARE • NOT FLASHABLE**

## Scope

U1–U8 yielded a genuine Ubuntu 26.04 ARM64 filesystem (including Phosh and
Labwc) and an offline-checked guarded first-stage `/init`, but did **not**
actually execute a Linux kernel boot, ext4 mount, or `switch_root`.

**U9 changes that testing gap** by running a disposable QEMU AArch64 virtual
machine using a generic Linux kernel deliberately built with built-in virtual
hardware drivers. This test does **not** run the Pixel 8 shusky kernel and
does **not** validate compatibility with Evolution X Android16, Tensor G3,
Pixel graphics or firmware partitions.

## Sources / reproducibility

- Real, SHA256-pinned [U6 ext4 IMG](PHASE_U6_RESULTS.md):
  `d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e`.
- Real, SHA256-pinned [U8 guarded initramfs](PHASE_U8_RESULTS.md):
  `dc50919b6a4e89dc8c27d84dee5335105c756573ef3dcf74c3465a414e50372b`.
- Generic upstream stable Linux **6.6.89** from `cdn.kernel.org`;
  kernel tarball SHA256 recorded in Actions log (not vendor firmware).
- Builds guest-only `arm64` kernel `Image` with built-in
  `virtio-blk`, `virtio-mmio`, `ext4`, `devtmpfs`,
  `proc`, `sysfs` and initramfs LZ4 support.
- The kernel is **generic QEMU virt**, not shiba. No kernel/Image from this
  phase should be flashed or used in Android boot partitions.
- The U8 initramfs is instrumented with QEMU test markers only and repacked
  as a guest-only `cpio.lz4`; it is **not** packaged as `init_boot.img`.

## Two controlled virtual-machine tests

1. **Negative:** Boot QEMU AArch64 without a rootfs UUID and confirm
   `U8 HALT: requires exactly one u8.rootuuid`. No mounting attempted.
2. **Positive:** Attach the exact U6 ext4 IMG as **read-only QEMU virtio disk**.
   Pass its offline filesystem UUID with the research token in the **VM-only**
   kernel command line. Verify guest console markers for:
   - kernel and first-stage `/init` startup,
   - Linux ext4 rootfs mounted `ro,noload`,
   - Ubuntu 26.04 identity verified,
   - `switch_root` path reached and systemd PID 1 logs observed.

The QEMU test asserts these markers against the actual VM serial logs.
A successful CI job would prove **generic ARM64 Linux kernel/userspace
integration inside an emulator**. A failed job will publish available logs and
blockers instead of claiming success.

## Explicitly NOT part of U9

- No connection to the user's ThinkPad or Pixel 8; no ADB, fastboot, flash,
  Android bootloader, verified boot/AVB, partition changes or ROM installation.
- No claim that Google Tensor G3 drivers, shiba Device Tree, current Evolution X
  vendor modules, native display, touch, GPU, Wi-Fi or USB-C external display
  work under Ubuntu.
- No creation of deployable boot.img or init_boot.img; all outputs are
  QEMU logs, a source kernel config and audit reports.
- Even systemd messages in QEMU do not prove the Pixel 8 can boot.

## Implementation

- [U9 kernel compile + QEMU GitHub Action](.github/workflows/phase-u9-qemu-boot.yml)
- [QEMU negative/positive guest launcher](scripts/u9_vm_run.sh)
- [Boot-stage log assertions](scripts/u9_vm_assert.py)

Initial build is triggered by creating this plan. Fix any errors using
actual Actions logs, not speculative device diagnosis.

**DO NOT FLASH. THE U9 KERNEL IS FOR QEMU ONLY.**
