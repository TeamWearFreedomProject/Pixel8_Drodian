# U22 — Google Pixel 8 shusky device driver rebuild attempt on CP2A GKI 6.1.157

**EXPERIMENTAL SOURCE BUILD. NOTHING PRODUCED MAY BE FLASHED.**

## Context
- Restored physical `shiba` Pixel 8 runs `CP2A.260805.005`, Linux `6.1.157-android14-11-gbd23337e42e7-ab14791245`.
- U18 built a *generic* ARM64 GKI from Google's official `android14-6.1-2025-12_r9` with source commit `bd23337e42e794964a89f47596daf1209a25ee1a`. Its output release is `6.1.157-android14-11-maybe-dirty`, not stock-signed firmware.
- U17 built Pixel 8-family shusky vendor modules using `6.1.124-android14-11`. U19 confirmed those existing binaries are not proven compatible with `6.1.157`.
- U21 mapped actual Git commits and device-specific DTBO sources but did not claim an exact stock CP2A vendor source release.

## What this stage actually attempts
1. Sync the official Google `android-gs-shusky-6.1-android16` kernel/device driver manifest and toolchain on an isolated GitHub runner.
2. Checkout the exact U18 official Google GKI kernel/common SHA from its pinned r9 tag, rather than relying on whatever 6.1.124 GKI the U17 manifest references.
3. Invoke the upstream `build_shusky.sh` *without modifying arbitrary vendor source files*.
4. Record the real compiler exit status, actual `Image` version, generated `.ko` inventory and their SHA256, or failures with logs. Do not upload potentially mislabeled boot firmware.
5. Keep a **DENY** device flash gate irrespective of compile success. Matching kernel version is not sufficient for KMI CRC, actual CP2A modules, shiba DTBO and display, ROM boot chain, rollback or Ubuntu userspace.

**Important:** This is explicitly an attempt. There is no source-proven guarantee that combining the r9 GKI with the older vendor project revisions will compile. Failure is useful evidence pointing to missing upstream integration work, not something to paper over or “fix” by forging versions or disabling safety checks.

See [U22 workflow](.github/workflows/phase-u22-shusky-gki-bridge.yml), [auditor](scripts/u22_shusky_gki_attempt.py), and [U21 source provenance](PHASE_U21.md).

No Pixel 8, ADB, fastboot, bootloader, partition writes, slot switches or real-device testing. Project owner leads research and ChatGPT assists with CI. Google AOSP is upstream.
