# U20 — Ubuntu 26.04 rootfs + guarded first stage + CP2A GKI offline integrity integration

**OFFLINE ONLY. NO PIXEL 8 BOOT OR FLASH IMAGE. NO DEVICE WRITES.**

## Reuse the already built, hash-pinned genuine artifacts

| Component | Parent phase | Purpose |
| --- | --- | --- |
| Ubuntu 26.04 arm64 raw ext4 data image (2 GiB) | U6 | Ubuntu root filesystem, systemd, GUI research |
| ARM64 static BusyBox + `/init` in legacy LZ4 CPIO | U8 | Guarded read-only rootfs/UUID probe and `switch_root` *design* |
| Exact-source `android14-6.1-2025-12_r9` GKI Image | U18 | Generic AArch64 kernel 6.1.157 build evidence |
| Actual U17 vendor .ko ABI incompatibility analysis | U19 | Blocks mixing old 6.1.124 modules with current CP2A |

Existing immutably identified GitHub Actions runs:
- [U6 rootfs build](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047914957)
- [U8 initramfs](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38052743722)
- [U18 GKI success](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38101661379)
- [U19 vendor ABI audit](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38103774760)

U20 downloads the ACTUAL artifacts and compares their full bytes to
previously recorded SHA256 hashes. It validates Ubuntu 26.04 identity
and expected GUI/systemd inodes by using **read-only debugfs** on the
original 2 GiB ext4 image, checks the full U8 gated ARM64 initramfs,
and verifies the U18 Image's kernel banner. No loop mount, format,
device access, partition selection, fastboot or ADB is performed.
Reports are uploaded; it does not duplicate or repackage the huge raw
rootfs and does not publish a boot or userdata flash image.

## Why this stage is not a running native Ubuntu phone

This phase binds the three RESEARCH PARTS by identity, not a validated
boot chain. We have not proven that the generic U18 kernel boots
Google's Pixel 8 hardware, that U8 `/init` really `switch_root`s
after block discovery, nor that the U6 userspace functions with the
device's DRM/Mali, power, Wi-Fi and touch drivers. Root UUID
recorded in the U6 **offline** ext4 image does NOT establish any
physical Pixel 8 partition mapping.

- Earlier **U16** successfully booted Ubuntu ARM64 + Wayland/DRM in
  **generic QEMU**, not in Tensor G3 hardware.
- **U19** reported that existing Pixel vendor module binaries were
  compiled against an older kernel; they cannot simply be relabeled.
- **U18** GKI source commit matches CP2A's Git suffix but the
  generated `uname` says `maybe-dirty`, not stock's signed
  build number.
- GKI Image + rootfs.ext4 + standalone initramfs CPIO is **NOT**
  a usable stock Android `boot.img` or `init_boot.img`.

## Exit criteria and next work

U20 CI may succeed if it proves the offline hashes, structure,
first-stage policy and existing U19 DENY gate; this does **not**
turn the separate parts into a native Pixel Linux distribution.
The next real blockers are matching 6.1.157 shiba vendor binaries,
kernel symbols/KMI, DTBO/panel, secure boot/rollback policy and
physical-disk boot design verified *before* any device test.

**REAL DEVICE FLASH GATE: DENY**.

The Pixel 8 remains on factory `CP2A.260805.005`.
User leads their Pixel 8 Ubuntu research; ChatGPT helps create
read-only CI verification, respecting Google AOSP and earlier
upstream Ubuntu and module contributors.
