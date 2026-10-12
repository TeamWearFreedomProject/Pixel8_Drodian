# U35 — Ubuntu 26.04 ARM64 Base + initramfs + Android boot/header v4 (offline LAB)

**STATUS: RESEARCH PROTOTYPE, NOT A DEPLOYABLE PIXEL 8 IMAGE. REAL DEVICE BOOT / FLASH GATE: DENY.**

## Motivation and device identity

The user is researching native Ubuntu Linux on a **Google Pixel 8, codename shiba (Tensor G3)**. We consulted the [Tensor Linux project](https://github.com/Tenser-Linux/Tensor-Linux), which documents **Pixel 8 Pro, husky** support (HuskyFE compositor, GPU proxy, Wi-Fi etc.). Its publicly linked [V1.0 release](https://github.com/Tenser-Linux/Tensor-Linux/releases/tag/V1.0) distributes husky-specific prebuilt images and a batch flash script. Its README is *not* public verified source for a shiba kernel/bootchain or proof of compatibility with the device. **NO husky artifacts or flashing routines are copied or invoked here.** Reference and original project owners credited.

Google's official AOSP documentation explains the **separated GKI Android v4 boot chain**: on Pixel 8-generation devices, generic `boot.img` contains GKI kernel while `init_boot.img` holds the generic early ramdisk. Pixel 8's vendor partition naming includes `vendor_kernel_boot`; that is not interchangeable with another device's `vendor_boot`. See [AOSP generic boot specification](https://source.android.com/docs/core/architecture/partitions/generic-boot) and [building Pixel kernels](https://source.android.google.cn/docs/setup/build/building-pixel-kernels?hl=ja).

## What is actually built, in one disposable cloud run

The [U35 workflow](.github/workflows/phase-u35-ubuntu-base-initramfs-bootv4-lab.yml) inherits every U33 source pin, old-GKI provider graph check, the successful GKI 6.1.157 compilation, full shusky vendor build and **454 SHA256-distinct module all-versions and research GKI CRC audits**, with **58 old 6.1.124 modules expected to remain absent**. This does **not** mean the output has the stock CP2A kernel release suffix, CP2A external ABI identity, proprietary DTBO panel selection or working GPU/display.

Only after those real source/ABI gates pass:

1. Download **Canonical Ubuntu Base 26.04.1 arm64** from [Ubuntu Base release directory](https://cdimage.ubuntu.com/ubuntu-base/releases/26.04/release/), verify its bytes against official HTTPS `SHA256SUMS`, extract into a separate rootfs staging directory, and make a **lab-only ext4 filesystem image** named `ubuntu-U35-LAB-NOT-USERDATA.img` with volume label `U35_UBUNTU_LAB`. It is **not** a Pixel 8 userdata image and **no Android partition is selected or formatted**. Base alone has no installed desktop/login/supported systemd boot configuration; a valid rootfs image does not imply full Ubuntu.
2. Obtain the official **Ubuntu 26.04 arm64 busybox-static** package from the authenticated Ubuntu package repository. Copy its **AArch64** ELF into a minimal cpio initramfs; install our `scripts/u35_stage0_init.sh` as PID 1. This init only prepares proc/sys/devtmpfs, prints a diagnostic banner and opens a shell. There is **no automatic userdata / block device mount, rootfs discovery, decryption or switch_root**. This is **not** a phone-ready `init` or successful Ubuntu rootfs handoff.
3. Get upstream **AOSP mkbootimg** from public android.googlesource.com Android 16 source tag. Recompress/verify the U33 output GKI `Image.lz4` byte-for-byte against the actual source Image. Produce **experimental research lab** Android header v4 `boot-U35-LAB-NOT-FLASHABLE.img` containing *only* that research GKI kernel, plus separate `init_boot-U35-LAB-NOT-FLASHABLE.img` containing *only* new initramfs.
4. Independently parse both boot v4 headers, expected size, component offset/layout, no signature, no fake version flag, verify embedded GKI and initramfs SHA256 payload identity; attest Ubuntu Base tar and ext4 file hashes, AArch64 BusyBox ELF arch and static stage-0 CPIO member list.
5. GitHub Actions uploads **only text, exit statuses, package/source fingerprints, official tar SHA256, boot header metadata and security blockers**. **NO** `boot.img`, `init_boot.img`, `ubuntu.img`, `dtbo.img`, `vendor_kernel_boot.img`, raw rootfs archive or any usable flashing payload appears in release artifacts.

## What a successful U35 test would and would not prove

**Potentially proved if actual CI passes:** Google-pinned GKI source build, all inspected module vermagic consistency, exact Android boot v4 layout packaging, an independent AArch64 BusyBox stage0 initramfs archive and authentic Ubuntu Base arm64 ext4. Crucially, **Pixel 8 shiba stock CP2A kernel string** `6.1.157-android14-11-gbd23337e42e7-ab14791245` is **NOT** identical to the GKI lab output `6.1.157-android14-11`.

**Not proved:** Android init_boot ramdisk chaining with stock CP2A vendor ramdisk and bootconfig; full signed stock vendor symbol CRCs, AVB and rollback index policy; precise shiba dtbo panel and board revisions; rootfs mounting location or encryption; UFS/FIPS early init and Linux `switch_root`; GUI, touch, modem, sound, GPU, camera; reliable hardware boot or USB rescue.

U34 previously used **a generic QEMU ARM64 virt machine with Ubuntu's generic kernel**, not the Pixel Tensor G3 kernel. U35 does not claim its own lab initramfs was boot-tested on the physical handset. More offline CI and trusted stock CP2A references are prerequisites to any new device trial.

User's school managed PC is due to be reclaimed 2026-10-12 for two weeks. Everything here is **GitHub-hosted** and requires no computer, root on personal hardware, USB phone, or Windows administrator rights. The user can view CI via a web browser later.

**REAL DEVICE BOOT / FLASH GATE: DENY. NEVER FLASH THESE PROTOTYPE FILES.**
