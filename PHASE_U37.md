# U37 — Publish experimental source-built images as temporary GitHub Actions Artifacts

**Purpose:** Respond to the request to make U35 research binaries downloadable while explicitly **NOT installing or flashing anything**. All operations take place on a disposable cloud Ubuntu GitHub Actions runner with no smartphone/USB access.

## What is published when the run passes

The [U37 workflow](.github/workflows/phase-u37-export-research-images.yml) **rebuilds the full successfully audited U35 pipeline** (U33 6.1.157 source GKI + shusky dist/module CRC audit + official Canonical Ubuntu Base 26.04.1 arm64 + AArch64 static BusyBox stage0 initramfs + Android boot image v4 packing). The previously successful [U35 Run #5](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38196600339) uploaded **reports only**; those ephemeral compiled images cannot be recovered from the old VM. A fresh complete source and image build is therefore required.

Three **time-limited GitHub Actions Artifacts (21 days)** are uploaded if and only if U35 all-build/module/header SHA gates and independent U37 copy checks pass:

1. **Experimental startup research binaries**, exact filenames: `boot.img`, `init_boot.img`, `Image`, `Image.lz4`, `initramfs.cpio.gz`, plus those of `dtbo.img`, `vendor_kernel_boot.img`, `vendor_boot.img`, `system_dlkm.img`, `vendor_dlkm.img` that were **actually output** by the checked source-build dist. Missing optional files are recorded as absent, not invented or downloaded from a different device. Files also include SHA256SUMS, README and manifest identifying each as unverified.
2. **Ubuntu Base rootfs**: `ubuntu.img` — the **raw 1 GiB ext4 laboratory image** that U35 builds using `mkfs.ext4 -d` from Canonical Ubuntu Base 26.04.1 arm64. Actions' ZIP artifact compresses the raw file; when extracted its name is `ubuntu.img`. It is **not** Pixel 8 Android userdata, not a systemd/Wayland desktop and not a working Ubuntu Touch image. Ubuntu binaries are subject to their original upstream licences.
3. **Metadata only**: checksums, exact source hashes, original U35 verification reports, and unverified compatibility status.

**GitHub Actions Artifacts are not GitHub Releases**. They are associated with each run and may require GitHub sign-in to download. They will expire after the configured 21 days, and successful results must be checked in the actual Actions run; a Pull Request by itself does not mean binary uploads succeeded.

## Verification gates and limits

U37 export script independently compares the copied file SHA256 against U35 exact kernel, v4 embedded boot.img, init_boot.img, initramfs and Ubuntu ext4 SHA256 witnesses. It refuses to publish if the U35 internal module/boot gate or explicit DENY is absent. Startup files are sourced only from the same ephemeral CI build, **never** from the husky/Pixel 8 Pro binary distribution, a private Pixel 8 phone, or a Google factory image.

These are **laboratory research artifacts, not installable boot images**. Pixel 8 (shiba) stock CP2A vendor modules/KMI, bootloader/AVB state, exact board panel DTBO, vendor ramdisk and init_boot bootconfig integration, early UFS/storage, partition selection, rootfs mounting/switch_root, desktop GUI, display/USB, and recovery route remain unverified. In fact the exported stage0 initramfs only opens a BusyBox diagnostic shell; it **does not hand over control to Ubuntu**. U36's separately verified QEMU Ubuntu Base `chroot` did **not** execute these Pixel 8 boot images.

**REAL DEVICE BOOT / FLASH GATE: DENY.** Do not use these artifacts with fastboot or write them to an actual device. No flash command, script or device action is included.
