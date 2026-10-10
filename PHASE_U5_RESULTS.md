# Phase U5 RESULTS — Ubuntu GUI rootfs and current Evolution X source integration research

**CI SUCCESS — STATIC/OFFLINE VALIDATION ONLY — NOT BOOTABLE — NOT FLASHABLE**

## Evidence

- Date: 2026-10-10
- [U5 successful GitHub Actions run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047047664) — conclusion: **success**.
- [Artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047047664/artifacts/11668555422):
  `shiba-u5-offline-rootfs-design-audit-1`, 4,032 bytes;
  expires **2026-11-09 11:03 UTC**.
- Artifact contains only `U5_REPORT.md`, `U5_AUDIT.json`,
  `U5_INITRAMFS_CONTRACT.json`, `U5_SOURCE_COMMITS.txt`.
  **No firmware, boot, or userdata images.**

## U3 Ubuntu 26.04 ARM64 rootfs verified from actual tarball

| Property | CI-verified value |
| --- | ---: |
| Actual compressed `.tar.xz` bytes | **154,585,148** |
| Sum of unpacked regular-file payloads | **697,790,708** |
| Regular files | **18,760** |
| Directories | **2,710** |
| Symbolic links | **3,276** |
| Required GUI packages installed / matching arm64 architecture | **9 / 9** |

This is why the previous ~155 MB archive seemed small: XZ compression reduced
roughly 698 MB of **regular-file payload data** to 155 MB. This is not an
exact prediction of disk space required for a live filesystem: metadata,
alignment, filesystem journal, free space, caches and extra applications
increase real storage requirements.

The U3 tar SHA256 was reverified in CI:
`40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a`.

## Evolution X Android 16 research evidence

Pinned public `bka` branch source commit revisions:

- [shusky Pixel 8/8 Pro device](https://github.com/Evolution-X-Devices/device_google_shusky/commit/56006ae8162db285e776d85319d9942945b87194):
  `56006ae8162db285e776d85319d9942945b87194`.
- [zuma Tensor G3 device-common](https://github.com/Evolution-X-Devices/device_google_zuma/commit/fba447c6317f23501dbac209b6479e458800c449):
  `fba447c6317f23501dbac209b6479e458800c449`.

Read-only source markers validated:
- shiba kernel target is Google shusky 6.1.
- Shusky declares dependency on `LineageOS/android_device_google_shusky-kernels`,
  branch `lineage-23.2`.
- Vendor kernel ramdisk module selection, including touch-related driver
  module names, exists in the source.
- Zuma Android board source describes A/B boot image partition family,
  Android recovery fstab generator including encryption assumptions,
  and support for ext4/F2FS filesystem builds.

**Critical source limitation:** the pinned development branch is not proof
of the **exact build, kernel, device tree, module KMI, boot image or vendor
partition installed on the user's Pixel 8**. The user reports Android 16
Evolution X; full device software identity remains unknown. Earlier Android
17 vendor images cannot be treated as matching this ROM.

## Inert initramfs contract research

The CI also validated a JSON-only proposed boot integration contract:

- target device is `shiba`, architecture `arm64`;
- Linux rootfs mount would require a **separately verified Linux volume**;
- volume UUID is intentionally **unassigned**;
- overwriting Android `userdata` is **explicitly prohibited** in this
  research contract;
- first mount would require read-only validation and a fail-closed policy;
- bootability, flashability and device testing remain **false**;
- all **6 mock policy/negative tests passed**.

This contract does **not** contain executable initramfs code, actual
mount instructions, a partition map or a bootloader integration.

## Readiness decision

**The Ubuntu port is NOT ready to flash or to boot.** U5 is a research
milestone, not an image production milestone.

Missing:
1. Exact current ROM kernel/vendor KMI identification.
2. Device-matched initramfs and Android/Linux boot handoff.
3. Verified isolated rootfs volume/space layout and mount logic.
4. Pixel 8 DRM/touch, GPU/Bionic bridge, USB-C external monitor and
   power-management integration.
5. Reviewed failure/rollback and data-protection plan.

No physical phone, ADB, fastboot, partition changes, unlocking, and no
flashable image output occurred.

**BUILD ONLY — NOT BOOTABLE — DO NOT FLASH.**
