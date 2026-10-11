# Phase U18 — Pixel 8 CP2A.260805.005 pinned Google GKI 6.1.157

**STATUS: SOURCE PROVENANCE + ARM64 GKI RESEARCH BUILD. NOT A PIXEL 8 UBUNTU ROM. DO NOT FLASH.**

## Device baseline measured by ADB on the user's restored, normally booting Pixel 8

- Device: Google Pixel 8 **shiba**, not Pixel 8 Pro husky.
- Stock factory / Android 17: `CP2A.260805.005`.
- Build and vendor fingerprint (both independently reported):
  `google/shiba/shiba:17/CP2A.260805.005/15828068:user/release-keys`.
- Stock kernel `uname -r`:
  `6.1.157-android14-11-gbd23337e42e7-ab14791245`.
- Stock Android boots to the home screen; no real-device modifications
  from the U18 project.

## Critical breakthrough: exact *official upstream GKI* commit

Google's Android14-6.1 release index explicitly records:

| Attribute | Pinned source |
| --- | --- |
| Kernel source | https://android.googlesource.com/kernel/common |
| GKI release tag | `android14-6.1-2025-12_r9` |
| Release date | 2026-01-28 |
| Kernel version | `6.1.157` |
| Official commit (full 40 hex) | `bd23337e42e794964a89f47596daf1209a25ee1a` |
| Stock CP2A `uname` Git suffix | `gbd23337e42e7` |

The stock 12-character Git suffix equals the leading 12 characters of this
official commit; therefore this is a **precise match for the upstream GKI
source commit**, not merely the same numeric version.

Official references:

- Google Android14-6.1 GKI release table:
  https://source.android.com/docs/core/architecture/kernel/gki-android14-6_1-release-builds
- Official Gitiles commit:
  https://android.googlesource.com/kernel/common/+log/bd23337e42e794964a89f47596daf1209a25ee1a
- Official AOSP GKI build instructions:
  https://source.android.com/docs/setup/build/building-kernels

**This does not establish bit-for-bit identical Google-signed CP2A
`boot.img`.** Compiler, build configurations, signature and
`-ab14791245` Android build number are distinct from Git source identity.

## Isolated GitHub Actions procedure

[U18 workflow](.github/workflows/phase-u18-cp2a-gki.yml) performs two
separate jobs:

1. **Fast source check**: query the published Google tag through Git;
   dereference the annotated tag, require the **complete SHA40** to match,
   fetch its official `Makefile` through Google Gitiles, validate numeric
   `VERSION/PATCHLEVEL/SUBLEVEL` = 6.1.157, produce JSON + Markdown report.
   No source compile or phone involvement yet.
2. **GKI build attempt**: use official
   `common-android14-6.1-2025-12` kernel manifest, synchronize public
   source/build toolchain, explicitly check out **the pinned r9 tag/commit**
   rather than a moving 2026 branch tip, and attempt the standard Kleaf
   `//common:kernel_aarch64_dist` target. Collect built kernel release,
   image hashes and a resolved source manifest. All generated binaries
   remain labeled **UNVERIFIED / DO-NOT-FLASH**.

If download, source commit, kernel version, or compilation verification
fails, **report failure honestly**; never substitute a convenient newer
release or an earlier 6.1.124 prebuilt. The project protects a usable phone,
not a CI green checkmark.

## Relationship to U17 and native Ubuntu

- U17 succeeded at building Google **shusky** Pixel vendor/kernel-family
  files, but its `Image` banner says `6.1.124-android14-11-...`, older
  than CP2A. This mismatched bundle is *not* CP2A firmware.
- U18 solves **one source-provenance component only**: exact common **GKI**
  commit and a generic aarch64 build. It does **not** automatically rebuild
  Google shusky vendor drivers for this version.
- Still needed: matching shiba Pixel modules and KMI symbol contracts,
  specific `zuma-shiba-mp.dtbo` and display/panel, correct vendor ramdisks,
  proper Android verified boot/rollback trust chain, native Linux
  initramfs/Ubuntu rootfs handoff, and physical display/USB tests.
- U16's working QEMU Ubuntu/Linux DRM+Wayland virtual desktop is
  independent. The generic QEMU kernel and virtio-GPU are not usable as a
  Pixel 8 boot image.
- U18 **does not connect to the Pixel 8** and does not run `adb`,
  `fastboot`, `flash`, `boot`, `set_active`, `-w` or unlock/lock
  procedures. It makes GitHub repository changes and CI-only research
  artifacts; the physical phone remains untouched.

## Explicit release gate

Even if the GKI source, SHA40, compiler and all CI jobs pass:

- **REAL DEVICE FLASH PERMISSION: DENY.**
- No claim that this GKI image is signed or compatible with CP2A's
  bootloader, modules, vendor system, AVB, DTBO, or Ubuntu.
- No bootloader rollback/AVB rollback bypass or slot switching.
- Only a later, separate reviewed device-specific integration stage
  with proven recovery and compatibility may evaluate physical testing.

## Attribution

Pixel 8 Ubuntu port research is led by the repository owner.
ChatGPT assists with source auditing, CI experiments and reports.
Google Android Open Source Project / Android Common Kernel upstream
remains the source of the kernel and build tools; U18 does not claim
Google authored or endorsed this experimental Pixel 8 port.
