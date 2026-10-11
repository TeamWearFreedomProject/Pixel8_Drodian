# U25 — Pixel 8 shiba GKI 6.1.157 source-only kernel and vendor research rebuild

**EXPERIMENTAL. NO FLASH. NO BOOT. NEVER CONSIDER THE CI IMAGE STOCK FIRMWARE.**

## Purpose
U24 demonstrated that Google's Pixel device Bazel defaults to **signed 6.1.124 GKI build 13202960** despite `kernel/common` being checked out at the official 6.1.157 commit. U22 therefore mixed the wrong KMI provider. An unrelated older external RTL8150 USB Ethernet dongle driver was expressly approved for exclusion, but Pixel 8's real internal DWC3 USB driver is essential and **may not be dropped** to chase a green compile.

## Real source-only experiment
U25 isolates all changes to a **disposable GitHub Actions runner**:
- Sync Google's public `android-gs-shusky-6.1-android16` manifest and retain actual vendor project source revisions.
- Checkout GKI `android14-6.1-2025-12_r9`, commit `bd23337e42e794964a89f47596daf1209a25ee1a`, matching the stock CP2A source Git suffix.
- Keep KMI/modpost checking and `-Werror` **enabled**. Call Bazel with `--config=use_source_tree_aosp --use_prebuilt_gki=false --use_signed_prebuilts=false --download_prebuilt_gki_fips140=false` so that old Google signed prebuilts cannot be accidentally mixed into the new kernel.
- Exclude **only** optional `CONFIG_USB_RTL8150` after verifying its exact Kconfig structure.
- Address the **name-only collision** between old SoC vendor constant `DWC3_LLUCTL = 0xd024` and new upstream indexed `DWC3_LLUCTL(n) = 0xd024 + n*0x80`: rename just the vendor constant and its same-project uses, **keeping the DWC3 controller driver enabled and the register address unchanged**. If the upstream symbol API differs from this exact expected form, fail closed, do not invent a workaround.
- Run the real Google shusky Bazel target in CI. Check actual build return code, kernel banner, and hash generated outputs without publishing a flash package. Preserve build logs and all temporary source changes as reviewable diffs.

**Any upstream failure is preserved and reported as a real U25 build failure.** Passing compilation cannot prove that Google CP2A production vendor `.ko` binaries or symbol CRCs match this experimental tree, nor device DTBO, AVB, USB runtime, Mali/DRM or actual Ubuntu handoff.

## Links
- [U24 official source-provider audit](PHASE_U24.md)
- [U25 workflow](.github/workflows/phase-u25-source-only-shusky.yml)
- [U25 fail-closed source patch and build report](scripts/u25_source_only_shusky.py)

Phone stays normally booting **Android 17 CP2A.260805.005** with `6.1.157-android14-11-gbd23337e42e7-ab14791245`. **REAL DEVICE FLASH GATE: DENY**. No partition/slot writes, no bootloader downgrade, no Android Verified Boot bypass.
