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

## Initial QEMU run and first corrected retry

- [U9 run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38054721534) **failed** final boot assertion; generic Linux 6.6.89 **did compile**, and both QEMU guests booted the Linux kernel and U8 first-stage. The negative no-UUID guest correctly halted.
- The positive guest enumerated a QEMU-only virtio block disk as `/dev/vda`, then halted with `U8 HALT: verified Linux root volume not found`, before any ext4 mount. This is **not** a Pixel hardware failure.
- Root cause identified in the U8 first-stage script: `busybox blkid` provides a minimal applet, but the script used util-linux-specific `blkid -t UUID=... -o device` and `blkid -s TYPE -o value` options, causing silent empty lookups.
- **Correction:** U8 script now parses only explicit UUID/TYPE/LABEL fields from the plain, read-only BusyBox `blkid` listing. UUID and opt-in checks, ext4-only, read-only mount and fail-closed behavior remain.
- The revised U9 workflow prints a *QEMU-only* block-ID diagnostic and caches the generic QEMU kernel as a reusable CI build artifact. The initial build took approximately 15 minutes; caching avoids needless recompilation on subsequent retries after the cache is created.
- The first repair rerun is **requested by this documentation update**. Its outcome must be checked separately. Do not claim systemd startup until the positive guest log actually shows it.

## Retry #3 — direct device probing after failed default BusyBox enumeration

- [Retry #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38057945071) also failed at the same UUID gate. The generic ARM64 Linux guest kernel compiled and both QEMU instances ran; the second positive serial log printed `U9_BLKID_SCAN_BEGIN/END` with **no listed block device**, then `U8 HALT: verified Linux root volume not found`.
- Earlier boot logs confirmed the guest Linux kernel enumerated QEMU's virtio-blk disk as `/dev/vda`. Therefore, the next hypothesis is BusyBox's **no-argument blkid enumeration** does not discover it; this remains a hypothesis until explicit probes are logged.
- Fix in `scripts/u8_init`: when `busybox blkid` returns no listing, enumerate only `/sys/class/block/*` advertised by Linux, and run `busybox blkid <device>` **read-only** on existing block nodes; require an **exact UUID match**, ext4 type and expected `SHIBA_UBUNTU` label. Never format or write partitions; the explicit opt-in gate remains mandatory.
- Add QEMU-only diagnostic logs for `/proc/partitions`, `/dev/vda` existence and direct `blkid /dev/vda`; these **are test instrumentation, not a path hard-coded into a Pixel 8 initramfs**.
- Retry #2 saved a 14 MB generic QEMU AArch64 kernel as a GitHub Actions cache, so retry #3 should re-use it without recompiling the whole kernel if cache restore succeeds.
- **No actual mount or Ubuntu boot success is claimed until this retry's guest console proves it.**

## Retry #4 — confirmed missing BusyBox applet, independent ext4 superblock probe

- [Retry #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059080376) failed at rootfs UUID detection. Its serial console **proved the root cause**: `blkid: applet not found` despite the Linux kernel reporting `/dev/vda` for the 2 GiB virtio disk. The earlier BusyBox fallback could never succeed.
- `scripts/u9_rootfs_probe.c` now contains a small read-only ext4 filesystem metadata checker compiled as a **statically linked ARM64 ELF**. It searches Linux-advertised block devices for **exactly one** matching ext4 magic, requested UUID and `SHIBA_UBUNTU` label; it never formats, mounts or writes.
- The U8 `/init` source has been updated to call the static binary after requiring the exact boot parameters. The action builds a host variant and a guest AArch64 binary, checking them against the SHA256-pinned U6 `.img` both positively and with an invalid UUID **before starting QEMU**.
- Retry #4 was launched by this documentation commit. A CI pass still requires actual QEMU guest serial proof of rootfs mount and systemd PID1. The emulator is QEMU `virt`, NOT Pixel 8 hardware.

## Retry #5 — cross-compilation toolchain correction

- [Retry #4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059495501) failed BEFORE guest execution while compiling `scripts/u9_rootfs_probe.c`: `fatal error: bits/wordsize.h: No such file or directory`.
- The generic QEMU kernel cache was again restored correctly; the native ARM64 C probe needs cross architecture libc development headers in addition to the cross-GCC executable.
- The workflow now explicitly installs `libc6-dev-arm64-cross` and `linux-libc-dev-arm64-cross` before compiling. The host and AArch64 probe binaries still must pass offline U6 ext4 positive and wrong-UUID negative tests before the QEMU boot.
- **No actual Ubuntu boot success is claimed**. Retry #5 is triggered by this documentation update and must be judged by the new CI logs.
