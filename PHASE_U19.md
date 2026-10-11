# U19 — Pixel 8 CP2A binary module compatibility gate (offline)

**RUNNING RESEARCH. ABSOLUTELY NO DEVICE WRITES.**

## User's known-safe stock baseline

- Pixel 8 shiba running Android 17 `CP2A.260805.005`
- `uname -r`: `6.1.157-android14-11-gbd23337e42e7-ab14791245`

## Real U17 vendor vs U18 GKI evidence

U17 produced the Google shusky family kernel and vendor-module ext4
images from `android-gs-shusky-6.1-android16`. Its **actual**
`Image` identified as `6.1.124-android14-11-g8d713f9e8e7b-ab13202960`.

U18 built a **generic** GKI from Google's exact official
`android14-6.1-2025-12_r9` commit
`bd23337e42e794964a89f47596daf1209a25ee1a`.
That matches the installed CP2A **source Git suffix** but the U18
compiled release string is `6.1.157-android14-11-maybe-dirty` — not
bit-for-bit stock.

**U19 is NOT allowed to rename/repack U17 6.1.124 modules as 6.1.157,
nor to force-load them into U18.** We need matching modules,
symbol/KMI validation, and shiba-specific panel/touch components.

## What the GitHub Actions audit does

- Download known successful [U17 run #4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38099633940)
  and [U18 run #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38101661379)
  artifacts using read-only `actions/download-artifact`.
- SHA256 check the actual kernel and EXT4 module images against the
  corresponding immutable CI reports.
- Read Linux banner strings from actual ARM64 kernel binaries.
- Inspect raw module `vermagic=` metadata in
  `vendor_dlkm.img` and `system_dlkm.img` and compare with U18's
  kernel release (raw string occurrences are **not** count of
  unique modules).
- Report explicit **integration blocked** if source artifacts differ
  in version or cannot be proven compatible; preserve JSON + Markdown
  only, without publishing a boot bundle.

A successful audit is evidence that we correctly detected the
compatibility problem; it is NOT proof a new shiba kernel was built.

## Remaining before a native Pixel boot

- Google shusky driver sources/revisions yielding real *6.1.157*
  module binaries, symbols and shiba boot ordering.
- Exact shiba `goodix_brl_touch.ko` rather than husky's `ftm5.ko`,
  panel/DRM/GPU/USB device-tree and overlays.
- Signed stock CP2A boot-chain provenance and Android Verified Boot
  rollback version; never downgrade bootloader or switch unknown slots.
- Offline Ubuntu 26.04 rootfs / initramfs investigation in **U20**,
  distinctly separate from boot-chain integration.

**REAL DEVICE FLASH PERMISSION: DENY.** Nothing in U19 connects to or
alters the actual phone. Project owner leads the work; ChatGPT assists
with research and CI. Google AOSP and original prior U17/U18 build
sources remain credited.
