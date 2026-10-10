# Phase U7 results — real Android v4 BOOT + INIT_BOOT experimental prototypes

**GITHUB CI SUCCESS — HEADER/CONTENT AUDIT ONLY — NOT BOOTABLE UBUNTU — DO NOT FLASH**

- Date: 2026-10-10
- [Successful GitHub Actions Run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38050847238): status **success**, all steps passed.
- [Research-only boot image artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38050847238/artifacts/11668569767)
  - Name: `shiba-u7-EXPERIMENTAL-boot-init_boot-DO_NOT_FLASH-1`
  - ZIP size **15,818,790 bytes**
  - Expires **2026-10-17 12:09 UTC** (21:09 JST)
  - Contains `boot.img` and `init_boot.img` **for offline structural research only** and `DO_NOT_FLASH.txt`
- [Structure verification artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38050847238/artifacts/11668549843)
  - Name `shiba-u7-boot-structure-reports-1`, **3,142 bytes**
  - Expires **2026-11-09 12:09 UTC**
  - Contains kernel SHA256 provenance, AOSP tool git revision, metadata JSON, CPIO/image audit and warning.

## Actual artifacts

| Image | Android header version | Kernel section | Ramdisk section | Scope |
| --- | ---: | ---: | ---: | --- |
| `boot.img` | 4 | 16,515,476 bytes | 0 | Earlier experimental Google shusky kernel, not current ROM |
| `init_boot.img` | 4 | 0 | 1,436,371 bytes | LZ4 newc ramdisk with static AArch64 BusyBox and inert `/init` |

Raw SHA256 values verified by CI:

```
boot.img      1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa
init_boot.img 66d4c4f5f797d3809dfbe58b7ba2840daf697cf5aa4f54c42de28f52f86dbe6b
ramdisk       19b2df1bcb1859cabd6e1e858927c98fdb63375b2ac736ff0354bd0e49353745
```

Original kernel payload SHA256 matched the new v4 boot image exactly:

`8a3ec09cfc307e1f17b868437201b5e6f87a80840cc21bff8aea85e333db8229`

## Verified on disposable CI runner

1. Previous experimental Google shusky `boot.img` obtained from Phase 1.
2. Extracted v4 compressed kernel and validated its byte-for-byte SHA256 integrity.
3. Verified Ubuntu U1 ARM64 minbase rootfs SHA256, installed official Ubuntu 26.04 `busybox-static`.
4. Checked BusyBox as a **statically linked ELF64 AArch64 binary** (machine 183).
5. Packed `newc` initramfs and LZ4 legacy compression, inspected CPIO entries for `/init` and `/bin/busybox`.
6. Generated two Android header v4 files using official AOSP mkbootimg source.
7. Parsed headers and section sizes; checked ramdisk/kernel hashes and inert `/init` marker.
8. Uploaded labeled research artifacts. **No Pixel 8 hardware actions.**

## Still a research prototype, not a Linux phone ROM

The Ubuntu U6 rootfs ext4 image is **NOT** mounted, copied or referenced by an on-device rootfs UUID in the U7 initramfs. The included `/init` deliberately loops after a diagnostic message rather than loading Ubuntu.

This proves image construction and header checks, **not** that it starts the Linux kernel on the real Pixel 8.

- The source Google shusky kernel is an **older, independent build**; compatibility with the actual installed Android 16 Evolution X kernel, vendor firmware and kernel module KMI is **unknown**.
- No matching shiba `vendor_boot`, `vendor_kernel_boot`, `dtbo`, AVB, partition/slot or power/display driver integration was verified.
- U7 images must NOT be flashed to any partition or booted on hardware at this stage.
- No Ubuntu GUI, touch, GPU, external display, Wi-Fi or fail-safe rollback has been proven.
- The presence of `boot.img` and `init_boot.img` is a **format/build milestone**, not a working operating system.

## Next milestone (U8)

Research a genuine, shiba-specific Ubuntu rootfs mount/handoff from `initramfs`,
confirm matching kernel/vendor modules for the exact current Evolution X release,
and design a reviewed test/rollback plan. Do not claim bootability until an actual
correctly integrated and tested image exists.

**BUILD ONLY • NONBOOTABLE • DO NOT FLASH.**
