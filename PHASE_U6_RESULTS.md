# Ubuntu Phase U6 Results — a REAL 2 GiB EXT4 rootfs IMG

**SUCCESS: standalone Ubuntu ARM64 ext4 filesystem image created.**
**NOT BOOTABLE • NOT USERDATA.IMG • DO NOT FLASH TO THE PHONE.**

## Reproducible evidence

- Completed: **2026-10-10**
- [GitHub Actions U6 successful run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047914957) — all steps **success**
- [Download image artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047914957/artifacts/11668457303):
  `shiba-u6-ubuntu-ext4-NOT_BOOTABLE-1`
  - Artifact ZIP: **248,481,441 bytes** (compressed for download)
  - Expires **2026-10-17 11:18 UTC** (~20:18 JST)
  - Contains the real file:
    `ubuntu-26.04-shiba-arm64-rootfs-DATA_ONLY-NOT_BOOTABLE.img`
- [Verification artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047914957/artifacts/11667897855):
  `shiba-u6-img-verification-1`
  - Artifact ZIP: **1,173 bytes**, expires **2026-11-09 11:18 UTC**
  - Contains `U6_REPORT.md`, `U6_SHA256SUMS`, `U6_EXT4_SUPERBLOCK.txt`
- [Builder workflow](.github/workflows/phase-u6-rootfs-ext4.yml)

## Exact image identity

| Metric | Measured value |
| --- | --- |
| Format | **raw ext4 standalone filesystem** |
| Logical image size | **2,147,483,648 bytes (2 GiB)** |
| Filesystem label | `SHIBA_UBUNTU` |
| Base OS | **Ubuntu 26.04 Resolute ARM64**, previously verified in U3 |
| GUI | Phosh/Phoc touch interface and Labwc/Waybar desktop packages |
| Source | Previously verified `ubuntu-26.04-arm64-u3-gui-NOT-BOOTABLE.tar.xz` |
| Input U3 compressed tar | 154,585,148 bytes, SHA256 checked |
| Download artifact ZIP | 248,481,441 bytes |

Raw image SHA256 (verified with `sha256sum -c`):
```
d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e  ubuntu-26.04-shiba-arm64-rootfs-DATA_ONLY-NOT_BOOTABLE.img
```

## Actual CI checks, all passed

1. Downloaded U3 rootfs and verified checksum
   `40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a`.
2. Extracted onto ephemeral GitHub Actions machine, preserving owner numeric IDs and permissions.
3. Created 2 GiB file and populated ext4 using `mkfs.ext4 -d`, **without a mount or loop device**.
4. Checked actual ext4 metadata with `e2fsck -f -n`.
5. Read `/usr/lib/os-release` from the **IMG itself** using `debugfs` and confirmed `VERSION_CODENAME=resolute`.
6. Read `/etc/shiba-u3/session-research.json` and confirmed `bootable_phone_firmware: false`.
7. Read real inode metadata for `/usr/bin/labwc` and `/usr/bin/phoc` within the ext4 image.
8. Computed and verified the **raw IMG** SHA256 with `sha256sum -c`.
9. Uploaded both the compressed download of the real raw IMG and separate verification evidence.

## How small? Why isn't this a 5 GB ISO?

It contains a **minimal ARM64 Ubuntu rootfs and two GUI package sets**, not an Ubuntu Desktop x86_64 live installer, kernel boot-chain, recovery tools, snaps/browser bundle or fully configured desktop.

U5 measured **697,790,708 bytes of regular file payloads** before ext4 metadata.
The U6 ext4 image is **2 GiB including free space**. GitHub's compressed
artifact is around **248.5 MB** thanks to ZIP compression of the filesystem
file. Compression size is not an indicator of installed rootfs footprint.

## What STILL must not be implied

- **Not a flashable bootable Pixel 8 image**; no `boot.img`, `init_boot.img`, `vbmeta.img`, kernel/vendor KMI match or tested initramfs.
- **Not `userdata.img`** and not safe to send to an Android `userdata` partition.
- No Pixel 8 DRM/touch/GPU/external monitor integration was validated.
- Not proof the current Evolution X Android 16 bootloader/firmware can use this rootfs.
- No data on the user's Pixel 8 or ThinkPad was modified.

Next work is a **separate, verified Pixel 8 shiba boot/initramfs integration** and rootfs mount architecture; preserve and document rollback/data recovery before considering any real device use.

**BUILD ONLY • EXT4 DATA IMAGE AVAILABLE • BOOTABLE FIRMWARE NOT AVAILABLE.**
