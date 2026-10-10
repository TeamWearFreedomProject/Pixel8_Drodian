# Ubuntu Phase U2 — Pixel 8 Pro (husky) to Pixel 8 (shiba) static audit

**BUILD ONLY — DO NOT FLASH — NOT A BOOTABLE LINUX PORT**

## Purpose

Compare real upstream Pixel 8 Pro Tensor Linux release metadata against the
previously built experimental Google Pixel 8 shusky kernel artifacts.

- Source A: [Tensor Linux V1.0](https://github.com/Tenser-Linux/Tensor-Linux/releases/tag/V1.0),
  `husky-boot-images.zip` (**45,005,170 bytes**), pinned to GitHub release SHA-256:
  `3ef1f4e6675ffef522d939e5bb7dd9fdb06c6da60cde784b4ec7fe14e99dff9f`.
- Source B: [Phase 1 Google shusky vendor build](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37721346230),
  artifact `shiba-shusky-UNVERIFIED-BUILD-ONLY-2`.
- Source B was built from Google manifest `android-gs-shusky-6.1-android16`,
  **not verified to match** Android 17 build `CP3A.260905.009` and factory kernel
  `6.1.162-android14-11-g2ec90535fa34-ab15810641`.
- The upstream `husky` release is **not evidence of functional `shiba` compatibility**.

## Automated read-only analysis

The workflow `.github/workflows/phase-u2-static-audit.yml` runs
`scripts/phase_u2_static_compare.py` and writes only text/JSON evidence:

1. Fetch upstream husky ZIP and compare SHA256 to published release digest.
2. Download previous shiba experimental CI artifact; no new large kernel build.
3. Decode Android boot/vendor-boot header fields, identify embedded Linux version
   banners where decompressible.
4. Parse DTBO table and overlay SHA256s, compare any bit-identical DTBO entries.
5. Attempt to read vendor-kernel-boot ramdisk module paths and `vermagic`.
   Current parser is conservative and **does not fully decode all v4 fragmented
   vendor ramdisks**. A zero count is **not** evidence of missing modules.
6. Export `U2_REPORT.md` and `U2_METADATA.json` as GitHub Actions artifact.
7. Store **NO** boot/kernel/firmware image files in the output artifact.

No ADB, fastboot, Pixel device, recovery, bootloader, flashing, partition change,
or unsigned boot images. All processing is on the disposable GitHub runner.

## Running / limitations

[U2 Actions](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u2-static-audit.yml)

- Initial run is configured to start on the creation of this plan (GitHub push
  event), if the GitHub App push event is eligible. If no run starts, use
  **Run workflow** manually.
- Source B's original CI artifact currently expires **2026-10-15 03:24 UTC**.
  Run before expiry. A later repeat requires a fresh compatible input.
- Upstream downloads depend on network availability. Signature-free SHA256 checks
  verify bytes **against GitHub-provided metadata**, not the developer's identity.
- Kernel version differences, module-name matches or DTBO similarity can support
  research decisions, but **cannot establish bootability, firmware compatibility,
  hardware safety, GPU/display usability or external-monitor support**.
- Ubuntu U1 rootfs is complete as a CI build, but still lacks all hardware
  integration; U2 is strictly comparative research.

## Criteria for completion

- A successful U2 CI run with readable SHA256-verified provenance and
  comparison report.
- Explicitly distinguish decoded module counts vs parsing limitations.
- List concrete discrepancies and unresolved tasks for **Phase U3** (touch and
  external-display desktop, GPU/Wayland, shiba-specific hardware adaptation).

**The final goal remains phone touch UI + external PC desktop on native Ubuntu.
No physical-device testing in this phase.**
