# Build status — Pixel 8 Droidian experiments

## Phase 1: Google shusky kernel vendor build — PASSED

- Date (UTC): 2026-10-08
- GitHub Actions run: [#2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37721346230)
- Workflow: `Pixel 8 shusky - BUILD ONLY`
- Mode: `vendor`
- Result: `success`
- Source manifest branch: `android-gs-shusky-6.1-android16`
- Duration: approximately 16 minutes
- GitHub artifacts: `shiba-shusky-UNVERIFIED-BUILD-ONLY-2` and `shiba-diagnostics-2`
- Artifact expiry: 2026-10-15 (per GitHub; download or retain elsewhere if needed)

The GitHub job log confirms output in `out/shusky/dist`, including:

| File | Size from CI report |
| --- | ---: |
| `Image` | 35,359,232 bytes |
| `Image.gz` | 14,018,083 bytes |
| `Image.lz4` | 16,515,476 bytes |
| `boot.img` | 53,477,376 bytes |
| `dtb.img` | 1,542,204 bytes |
| `dtbo.img` | 2,131,921 bytes |

Other outputs include `vendor_kernel_boot.img`, `vendor_dlkm.img`,
`system_dlkm.img` and many kernel modules (`.ko`).
Some output files were omitted from the artifact ZIP to keep its size manageable;
see `shiba-diagnostics-2` for a full manifest and SHA-256 report.

**Important limits**

1. This is a successful build of Google's Pixel 8/8 Pro shusky kernel tree, **not** a Droidian / Halium build.
2. The `vendor` mode may use a **prebuilt GKI**, so it does not prove the GKI core was compiled from source. For that, use `full-gki` in a separate run.
3. The source branch has **not** been proven to exactly match the supplied Pixel 8 factory reference `CP3A.260905.009`, kernel `6.1.162-android14-11-g2ec90535fa34-ab15810641`.
4. Nothing here is validated for booting on the device.

## Next phase: Droidian adaptation research

- Inspect Halium/Droidian Android 14 / GKI 6.1 integration requirements.
- Identify the actual Pixel 8 shiba adaptation package/patch set needed.
- Keep build-only experiments separate from runnable firmware.
- Never flash, boot, or otherwise touch the physical phone as part of this project stage.

**UNVERIFIED — BUILD ONLY — DO NOT FLASH**
