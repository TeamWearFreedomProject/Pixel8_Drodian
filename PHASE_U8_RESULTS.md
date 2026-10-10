# Phase U8 results — genuine guarded rootfs mount / switch_root initramfs prototype

**GITHUB CI SUCCESS (STATIC OFFLINE AUDIT) — NOT A VERIFIED BOOTABLE PIXEL8 ROM — DO NOT FLASH**

## GitHub CI evidence

- Date: 2026-10-10
- [Successful U8 GitHub Actions run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38052743722), `conclusion: success`.
- [U8 initramfs-only research artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38052743722/artifacts/11669981815)
  - Name: `shiba-u8-initramfs-RESEARCH-DO_NOT_FLASH-1`
  - Artifact size: **1,139,255 bytes** (GitHub ZIP)
  - Expires **2026-10-17 12:39 UTC** (~21:39 JST)
  - Contains `u8-ubuntu-rootfs-handoff-UNVERIFIED-INITRAMFS_ONLY.cpio.lz4` and warning.
- [U8 evidence artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38052743722/artifacts/11669812025)
  - Size: **2,433 bytes**, expires **2026-11-09 12:39 UTC**.
  - Contains `U8_REPORT.md`, `U8_AUDIT.json`, `U8_INITRAMFS_FILELIST.txt`, SHA256 and warning.
- New ramdisk SHA256 (verified by CI):
  `dc50919b6a4e89dc8c27d84dee5335105c756573ef3dcf74c3465a414e50372b`.

## What was REALLY implemented and verified

1. Implemented real BusyBox `/init` **source code** that requires an explicitly supplied Linux filesystem UUID and explicit research guard token, instead of guessing Android partitions.
2. After such external confirmation, its code is designed to check block device presence, filesystem type ext4 and exact `SHIBA_UBUNTU` volume label; it requests a **read-only, no-journal-replay mount** `ro,noload`.
3. The code checks `ID=ubuntu`, `VERSION_CODENAME=resolute`, `/sbin/init`, then has `switch_root` transfer code.
4. The existing U7 ARM64 static BusyBox was recovered from the pinned original U7 `init_boot.img`, and the updated standalone LZ4 CPIO initramfs was assembled.
5. ARM64 BusyBox was **executed under QEMU user mode** for a basic smoke test; U8 script shell **syntax** was checked through BusyBox and the host shell. This is **not a QEMU kernel boot**.
6. SHA-256 validated the real U6 ext4 image and U7 `init_boot.img`; ext4 rootfs identity was checked using `dumpe2fs` and `debugfs`.
7. The offline U6 ext4 image's filesystem label is `SHIBA_UBUNTU`, and its *offline-image UUID* is `d6b067e7-31e4-4aa3-8edf-d7e70fec0747`. **This is not a verified Pixel 8 storage mapping and must not be used as a device instruction.**
8. `/sbin/init` and `/usr/lib/systemd/systemd` inode entries were found inside the offline image. Existence does **not** prove these executables will function with real devices or all startup dependencies.
9. Five parameter-policy mock tests passed (positive explicit parameters and negative missing/duplicate/bad UUID or missing opt-in); the actual system startup and block-device discovery were **not simulated**.
10. [Official Tensor Linux husky ZIP](https://github.com/Tenser-Linux/Tensor-Linux/releases/tag/V1.0) re-downloaded, SHA-256 verified against `3ef1f4e6675ffef522d939e5bb7dd9fdb06c6da60cde784b4ec7fe14e99dff9f`, and checked for v4 boot/init_boot plus vendor, vendor_kernel_boot, dtbo partition files.

## Important distinction about the previously provided ZIP

The Pixel 8 Pro (husky) ZIP is genuinely used in **U2 and U8 as an upstream reference**. **U7 did NOT repack its husky kernel**, instead using the earlier experimental Google shusky (Pixel 8 family) kernel artifact. U8 uses the ZIP to verify layout while keeping board-specific firmware separate. The older Android 17 `vendor.img` reference also does not prove a match to the user's currently installed Android 16 Evolution X.

## Status and blockers

U8 outputs **only a standalone initramfs CPIO**, not a bootable `init_boot.img`, a complete flashing package or a test of actual boot behavior.

- No boot of the Pixel 8, no working display/touch/graphics or USB-C screen test.
- No actual rootfs mount, no actual `switch_root` or kernel PID1 tested.
- No proven current Evolution X vendor/kernel module KMI, DTBO/AVB/vendor boot compatibility.
- No safe verified Linux rootfs volume or UUID *on the actual Pixel 8*.
- No validated recovery/rollback plan.

Next significant step: emulate the whole first-stage mount/handoff under a Linux kernel on a **disposable test VM**, while researching the precise Pixel 8 vendor+kernel/DTBO integration. Keep all production flash operations disabled until independently reviewed and hardware-safe.

**BUILD ONLY • NOT READY TO FLASH • DO NOT FLASH.**
