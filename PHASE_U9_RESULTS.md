# Phase U9 RESULTS — real QEMU AArch64 kernel → Ubuntu rootfs → systemd

**SUCCESS: genuine generic-ARM64 virtual-machine boot, including ext4 mount and systemd PID1.**
**NOT PIXEL 8 HARDWARE BOOTABLE • NOT FLASHABLE • NO DEVICE ACTIONS.**

## Verified run

- **2026-10-10:** [GitHub Actions U9 run #6 — SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059787754).
- [Full QEMU serial output and validation reports](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059787754/artifacts/11673230569):
  `shiba-u9-qemu-boot-test-evidence-6`, **71,259 bytes ZIP**, expires **2026-11-09 14:32 UTC**.
- [Generic QEMU-only AArch64 kernel artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059787754/artifacts/11673265439):
  **14,258,833 bytes ZIP**, expires **2026-10-17 14:32 UTC**. **Not a Pixel 8 kernel.**
- [Live workflow](.github/workflows/phase-u9-qemu-boot.yml) |
  [Guest QEMU runner](scripts/u9_vm_run.sh) |
  [U8 early init](scripts/u8_init) |
  [New ext4 read-only probe](scripts/u9_rootfs_probe.c) |
  [Assertions](scripts/u9_vm_assert.py).

## Actual QEMU guest observations

| Check | Result |
| --- | --- |
| Generic ARM64 Linux 6.6.89 kernel boots | **PASS** |
| U8 initramfs `/init` starts | **PASS** |
| Negative control rejects missing rootfs UUID | **PASS** |
| Correct U6 ext4 UUID/label detected in virtual guest | **PASS** |
| Original 2 GiB U6 Ubuntu rootfs mounted read-only | **PASS** |
| Rootfs `Ubuntu 26.04 Resolute` identity verified | **PASS** |
| `switch_root` path reached | **PASS** |
| Real `systemd[1]`/Ubuntu startup logs observed | **PASS** |
| Interactive Ubuntu login prompt | **NOT OBSERVED** |
| Phosh / Labwc working graphical session | **NOT TESTED** |
| Pixel 8 shiba device running Linux | **NOT TESTED** |

**Important interpretation:** The QEMU guest demonstrably progressed into
Ubuntu systemd PID1, which is far stronger than U8's earlier shell syntax-only
check. The runner forcibly stopped the positive guest after its allotted time
(115 seconds); some startup jobs were still waiting, including
`dev-ttyAMA0.device/start`. **Do not claim a complete boot, login shell,
usable desktop or GUI yet.**

## Failed attempts and root cause (documenting all retries)

1. [Run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38054721534):
   generic ARM64 kernel compile and initial `/init` boot succeeded, but the
   `blkid` UUID search stopped without finding rootfs.
2. [Run #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38057945071):
   `busybox blkid` was still empty; saved the reusable generic QEMU kernel
   to the GitHub Actions cache to avoid more lengthy kernel builds.
3. [Run #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059080376):
   explicit guest diagnostics proved `/dev/vda` existed, but
   **`blkid: applet not found`** in Ubuntu's static BusyBox.
   No UUID scan using the BusyBox applet could work.
4. [Run #4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059495501):
   initial static AArch64 C probe could not compile due to missing cross
   architecture glibc development headers.
5. [Run #5](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059627853):
   installed those headers, but had not yet created the build output directory
   `ramdisk/bin`.
6. **Run #6 succeeded** after creating the directory. A statically linked
   ARM64 C helper uses Linux `/sys/class/block` to find exactly one ext4
   filesystem matching the explicitly requested UUID and exact
   `SHIBA_UBUNTU` label. It reads ext4 superblock metadata only and
   cannot format, mount, or write storage itself. The test verifies a correct
   and deliberately wrong UUID against the real U6 IMG before booting QEMU.

## SHA256 integrity from successful run

```text
Generic Linux 6.6.89 QEMU ARM64 kernel:
718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc

Instrumented ARM64 QEMU guest initramfs:
29b754f662eca8df9cc17762d61e645a16b38f70cdcaa860458cb9af3bb556be

Real Ubuntu U6 ext4 rootfs image:
d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e
```

## Remaining Pixel 8 port blockers

- QEMU `virt` plus virtio block are **not** Google Tensor G3 / Pixel 8 hardware.
- The installed Android 16 Evolution X build's matching kernel, vendor modules,
  board DTBO/DTB, GPU/display/touch drivers, AVB and firmware handoff are
  **not independently established**.
- The U6 ext4 filesystem has **no known, safe on-device location**.
- No complete usable login session or GUI in QEMU, much less on Pixel 8.
- No reviewed physical-device recovery, backup and rollback procedure.

**U9 achieved the kernel → initramfs → real Ubuntu systemd milestone inside
a generic ARM64 virtual machine, NOT a flashable Ubuntu phone ROM.**
