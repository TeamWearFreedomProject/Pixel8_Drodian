# Pixel 8 Droidian experiment — Build-only Phase 1

**UNVERIFIED • BUILD ONLY • DO NOT FLASH**

Pixel 8 codename: `shiba`; Google Pixel 8 / 8 Pro kernel family: `shusky`.

This first workflow compiles Google's **shusky kernel**, not Droidian itself.
There is **no ADB, fastboot, device connection, bootloader operation, or flashing**.

## Running (browser-only)

1. Open **Actions** in this repository.
2. Choose **Pixel 8 shusky - BUILD ONLY**.
3. Click **Run workflow**, choose **preflight**, then start it.
4. Once preflight succeeds, run again with **vendor**.
5. Try **full-gki** only when you need a source-built GKI and the previous build works.

Modes:
- `preflight`: fetch the official Google manifest metadata only; quick environment check.
- `vendor`: sync source and invoke Google's shusky production build (with prebuilt GKI where supported).
- `full-gki`: set `BUILD_AOSP_KERNEL=1` to build GKI from source as well.

**Artifacts** expire after seven days. Compilation may fail due to storage
requirements, source changes, or upstream build dependencies. A successful
build never proves that any generated image is safe to use on hardware.

Source branch: `android-gs-shusky-6.1-android16` (not verified to match the
factory reference `CP3A.260905.009` / kernel `6.1.162-android14-11`).

## Roadmap

Google kernel build → verify kernel source/compatibility → investigate
Halium/Droidian adaptation → rootfs packaging. Real-device testing is excluded.

References:
- https://source.android.com/docs/setup/build/building-pixel-kernels
- https://android.googlesource.com/kernel/manifest/
