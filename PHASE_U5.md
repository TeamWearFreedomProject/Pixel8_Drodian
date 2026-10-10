# Ubuntu Phase U5 — Pixel 8 shiba boot integration contract (OFFLINE BUILD ONLY)

**No flashable artifact. No ADB/fastboot, no device access or partition writes.**

## Scope

Native Ubuntu 26.04 ARM64, with Phosh for smartphone touch UI and Labwc
for a proposed external-monitor desktop. Research target is Google Pixel 8
(shiba, Tensor G3 / zuma).

The user's current ROM is **Evolution X Android 16** (reported 2026-10-10).
The exact installed build fingerprint, boot kernel build, vendor image and
module KMI have NOT been supplied or matched. Historical Android 17 Pixel 8
artifacts are **not interchangeable evidence**.

## Available real evidence

- U1: genuine Ubuntu 26.04 ARM64 minimal rootfs build.
- U2: static comparisons of released Pixel 8 Pro Tensor Linux boot images
  versus shiba kernel artifact and separately uploaded older Android 17 images.
  Shared driver names do not prove ABI compatibility.
- U3: real Ubuntu ARM64 GUI userspace tar.xz containing Phosh, Phoc, Stevia,
  Labwc, Waybar, Foot and Kanshi. [Successful U3 CI](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38042365918).
- U4: source-level DRM, evdev multitouch and Android Mali proxy checks.
  [Successful U4 CI](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38045860598).
- Current public Android16 Evolution X [shusky bka device tree](https://github.com/Evolution-X-Devices/device_google_shusky/tree/bka)
  and [zuma bka board tree](https://github.com/Evolution-X-Devices/device_google_zuma/tree/bka).
  **These are not guaranteed to be the installed ROM's exact sources.**

### Current bka tree findings

- Device shiba targets kernel 6.1.
- Evolution X shusky declares a dependency on
  `LineageOS/android_device_google_shusky-kernels`, branch
  `lineage-23.2`.
- Google zuma board source distinguishes boot, init_boot, vendor_boot,
  vendor_kernel_boot, dtbo and related A/B system components.
- The Android recovery fstab generation is specific to an Android
  encrypted-device arrangement. Reusing `userdata` as a generic Linux
  ext4 volume is **NOT justified** by this evidence.
- Google's [Pixel kernel documentation](https://source.android.com/docs/setup/build/building-pixel-kernels)
  associates shiba/husky with `android-gs-shusky-6.1-android16`,
  but that branch name alone cannot prove module compatibility.

## U5 experiment

[U5 GitHub Actions workflow](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u5-integration-readiness.yml)
and [read-only rootfs/source auditor](scripts/phase_u5_integration_audit.py):

1. Download the **actual U3 rootfs tarball** from the prior CI run.
2. Verify its pinned SHA-256:
   `40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a`.
3. Inspect the compressed archive in memory (no extraction) for Ubuntu
   release metadata, installed ARM64 GUI packages and session files.
   Report the real compressed size and sum of uncompressed regular-file
   payloads (a useful lower bound for storage requirements).
4. Clone current upstream Evolution X Android16 bka shusky/zuma trees,
   pin exact commit SHAs, and check device/kernel/Android fstab references.
5. Emit a **JSON DESIGN CONTRACT**, not an executable initramfs.
   Unassigned independent Linux volume ID, no Android userdata overwrite,
   and explicit stop conditions pending hardware investigation.
6. Negative-test the design policy against wrong model, invented volume
   ID, userdata replacement and false flashable status.
7. Save text/JSON report artifacts only; do not produce a boot, init_boot,
   vendor_kernel_boot, vbmeta, userdata, ext4 or recovery image.

## Actual boot architecture remains hypothetical

Kernel with **shiba-matched modules** -> validated Linux first-stage initramfs
-> verified independent filesystem -> Ubuntu rootfs -> session manager ->
Phosh on phone / Labwc on validated external display.

Every arrow beyond the archive is a **required design and testing item**,
not an implementation or a boot success. A separate mountable volume is a
research candidate, not an instruction to repartition a phone.

**U5 pass means offline analysis success. It never means ready to flash.**

## Next steps / non-negotiable readiness gates

- Exact Evolution X Android16 installed kernel and corresponding vendor
  driver build provenance; source repo branch alone is insufficient.
- Device-specific, reviewed first-stage Linux boot and rootfs integration.
- Panel, touchscreen, Mali vendor ABI, USB-C external display, power and
  failure handling verification on the right software combination.
- Safe recovery and data preservation design reviewed before any hardware
  test is even considered.

This plan intentionally retains Android Evolution X and the user's data
untouched, including the Android userdata partition.

**BUILD ONLY — NOT BOOTABLE — NOT FLASHABLE.**
