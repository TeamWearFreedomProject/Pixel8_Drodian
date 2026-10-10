# Phase U6 — turn validated Ubuntu 26.04 ARM64 GUI rootfs into a real ext4 IMG

**IMAGE CONTENT ONLY • NOT BOOTABLE • DO NOT FLASH TO PHONE**

## Objective

Create a **real, standalone 2 GiB ext4 filesystem image** from the previously
verified U3 Ubuntu 26.04 ARM64 rootfs with Phosh+Phoc mobile GUI and
Labwc+Waybar desktop packages.

**This is an ext4 filesystem container, not a Pixel 8 ROM, not a partition
table, not a boot image and specifically not a drop-in userdata.img.**

We deliberately generate this before hardware integration as a reversible,
offline artifact for filesystem research. Preserve the Evolution X Android 16
installation and Android userdata without changes.

## Why small?

The upstream U3 archive was 154,585,148 bytes compressed with XZ, but held
697,790,708 bytes of uncompressed regular-file data. It excludes the full
Ubuntu Desktop live ISO, its installer environment, a browser/snap app bundle,
Linux boot integration and many extras. A real ext4 image includes filesystem
metadata plus room for future data, so use 2 GiB (2,147,483,648 bytes) for
this experiment.

## Inputs

[U3 successful run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38042365918),
artifact: `shiba-u3-ubuntu-arm64-gui-NOT-BOOTABLE-3`
(which expires October 17, 2026).

Input tar SHA256 (verified again):
`40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a`.

## Offline creation & validation

[U6 workflow](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u6-rootfs-ext4.yml):

1. Download and verify the genuine U3 tar archive and its SHA256.
2. Extract only to a disposable GitHub-hosted Ubuntu Linux runner.
3. Create a fixed 2 GiB file and use the host `mkfs.ext4 -d` to populate
   that file from the rootfs tree **without mounting or loop devices**.
4. Verify ext4 filesystem integrity using `e2fsck -f -n`; read back
   Ubuntu identity, GUI session metadata and program inode records using
   `debugfs`; record SHA256 and ext4 superblock metadata.
5. Upload a RAW `.img` file inside a GitHub compressed Artifact ZIP.
   A separate small artifact contains the checks and hash.

The raw .img has a **full 2 GiB logical size**, even if the GitHub ZIP
download is dramatically smaller thanks to compression.

## What it does NOT do

- Does not create `boot.img`, `init_boot.img`, `vendor_boot.img`,
  `vendor_kernel_boot.img`, `vbmeta.img`, `userdata.img` or a flashable
  installation package.
- Does not connect a ThinkPad/Pixel, issue ADB/fastboot commands, touch
  partitions or move/replace existing Evolution X data.
- No native display, GPU, touchscreen, external monitor or Linux boot test.
- Does not establish compatibility with current installed Evolution X
  kernel/vendor KMI. Building ext4 does not solve these issues.

A passing U6 workflow confirms **ext4 construction and filesystem checks**,
not phone compatibility. Boot integration and compatible storage mapping still
need careful separate work.

Adding this plan asks the GitHub workflow to run automatically once. It can
also be run manually later while U3 artifacts remain available.

**BUILD ONLY — DATA FILESYSTEM IMG — NOT READY TO FLASH.**
