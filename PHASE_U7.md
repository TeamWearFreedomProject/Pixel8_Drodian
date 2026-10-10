# Ubuntu Phase U7 — Android v4 boot + init_boot RESEARCH PROTOTYPES

**NO PHONE ACTIONS • NO FLASHING • NOT A BOOTABLE UBUNTU PORT**

## What is being built?

Two new **experimental, non-deployable Android boot header v4 containers**:

- `boot.img`: a freshly assembled header v4 file containing the **same**
  compressed Google shusky Linux kernel extracted from experimental Phase 1.
- `init_boot.img`: a header v4 ramdisk containing **ARM64 static BusyBox**
  from authenticated Ubuntu 26.04 repositories and a deliberately **inert**
  `/init` prototype. It prints a research marker and does **not** mount,
  search for, or attempt to boot any device rootfs.

Both files are deliberately marked **DO NOT FLASH** in the artifact name
and accompanying report.

### Critical limitations

These are not suitable for the user's current Pixel 8 running Evolution X
Android 16. The Phase 1 kernel came from Google
`android-gs-shusky-6.1-android16` and **its real module ABI/KMI match to
the installed phone is unconfirmed**. The image does not carry matching
`vendor_boot`, `vendor_kernel_boot`, `dtbo`, security metadata or a
working Ubuntu handoff. The U6 Ubuntu ext4 image has not been mapped to a
verified safe device or filesystem location.

A structurally valid Android v4 header **does not mean the Pixel 8 will boot
it**. The AOSP scripts and a placeholder ramdisk do not complete porting.

## Sources reused

- [Prior shusky kernel CI run 37721346230](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37721346230)
- [Ubuntu U1 ARM64 base run 38033533558](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38033533558)
- [Ubuntu U6 ext4 rootfs](PHASE_U6_RESULTS.md), **NOT embedded** in these boot images
- [Official Android mkbootimg utility source](https://android.googlesource.com/platform/system/tools/mkbootimg)
- [AOSP boot image format documentation](https://source.android.com/docs/core/architecture/bootloader/boot-image-header)

## CI plan

[U7 GitHub Actions](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u7-research-boot-v4.yml)

1. Fetch previous CI `boot.img` and verify header v4.
2. Extract its compressed kernel **without** touching a Pixel.
3. Fetch checksum-pinned Ubuntu U1 ARM64 rootfs.
4. Get static ARM64 BusyBox from official signed Ubuntu 26.04 apt sources
   in a throwaway QEMU-enabled chroot.
5. Construct a minimal LZ4 ramdisk containing AArch64 BusyBox and an
   intentionally inert `/init` (no rootfs mount, no external volume scan).
6. Generate version 4 `boot.img` and `init_boot.img` with AOSP
   `mkbootimg.py`, documenting upstream tool commit.
7. Strictly parse and verify both headers; compare copied kernel SHA256;
   decompress ramdisk, list its CPIO entries and validate AArch64 ELF.
8. Save research report plus explicitly **DO_NOT_FLASH** artifact.
9. Do **not** access devices, use Android tools to write partitions, change
   AVB settings, or claim any hardware success.

Existing Android `boot`, `init_boot`, `vendor_boot`, `vendor_kernel_boot`,
`dtbo`, `userdata` and other partitions on the user's phone remain untouched.

## What is next?

Before an actual Ubuntu boot attempt, the project still needs:
- Proven compatible `shiba` Linux kernel + full vendor module set for the
  actual Evolution X Android 16 firmware.
- Real rootfs location and verified filesystem device identification.
- Safe reviewed initramfs root mount and transition into Ubuntu init.
- Correct shiba DRM/touchscreen initialization and GPU/vendor components.
- A defensible rollback/recovery plan.

**Completing U7 means two header test images were assembled, not that a
flashable Ubuntu ROM exists.**

This plan is the trigger for the first GitHub Actions CI attempt.
