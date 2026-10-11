# U33 — Source-built Linux 6.1.157 GKI module images + full shusky validation

**EXPERIMENTAL CI RESEARCH — REAL PIXEL 8 FLASH / BOOT GATE: DENY**

## Confirmed U32 image-provider root cause

[U32 image dependency investigation, success](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38179472149): With U30's kernel Image alone redirected to source GKI r9 (`6.1.157`), the separate `//common:kernel_aarch64_images` alias still selected the **downloaded GKI provider** associated with `6.1.124`. The source-only alias experiment showed all configured-query results exit 0:

- BEFORE: `kernel_gki_modules` reaches old downloaded `kernel_aarch64_images_download_or_build`.
- AFTER: that configured old provider is no longer reachable; `kernel_gki_modules` reaches source `//aosp:kernel_aarch64_images` and `//aosp:kernel_aarch64`.
- Actual U32 module audit had 1,008 discovered file paths with 512 byte-distinct modules, 58 old `6.1.124` modules and 454 current `6.1.157`, with all 58 old modules copied directly into `out/shusky/dist/`. The prior U32 strict red build is **correct**. These are real stale binary modules, not benign fake warnings.

The prior graph PASS does **not** itself produce new modules or prove those 58 old binary files have disappeared.

## New U33 test

`.github/workflows/phase-u33-source-gki-images-full-verify.yml` runs entirely on disposable GitHub Actions Ubuntu runner: nothing runs on the user's administrator-locked Windows school computer and no hardware or bootloader access takes place.

1. Fetch immutable U30/U31 metadata and U27 provenance, sync/pin official Google shusky and exact GKI Git SHA `bd23337e42e794964a89f47596daf1209a25ee1a`.
2. Reapply the already successful narrow experimental U25/U28/U30 vendor compatibility changes; **trace old images alias BEFORE changing it**.
3. Apply the reviewed guarded **4KiB source `kernel_aarch64_images` alias** (leave 16KiB selection unchanged), reproduce U32 graph verification, and additionally demand that the **full shusky dist dependency** to old image provider is empty before wasting CPU on a compile.
4. Rebuild real GKI source `Image` plus its source `system_dlkm` modules and full shusky dist, with exact Bazel exit codes, verifiable 6.1.157 binary banner and SHA256 checks.
5. Re-run U31 spot-check and **U32 every discovered `.ko` SHA256-deduplicated CRC/vermagic audit**. Any old 6.1.124 vermagic anywhere in the discovery roots means an actual research FAIL; keep file origin diagnostics even when strict audit fails.
6. Publish **bounded source logs, stage exit codes, module names, versions and SHA256 only**, never boot/vender/kernel binary files.

All module-symbol comparisons are relative to the *same experimental GKI*, not real original stock Pixel 8 Android 17 CP2A modules. This does NOT validate 6.1.157 research `Image` vs stock suffix `6.1.157-android14-11-gbd23337e42e7-ab14791245`, real CP2A KMI/CRC, shiba DTBO/physical panel selection, USB/touch/GPU real runtime, AVB/rollback, or safe rootfs boot. The source-based `system_dlkm` may fail build or have changed module contents: only Actions logs will determine the result.

**NEVER INSTALL OR FLASH AN EXPERIMENTAL U33 ARTIFACT ON PIXEL 8.**
