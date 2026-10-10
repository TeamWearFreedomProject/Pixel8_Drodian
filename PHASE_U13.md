# Phase U13 — real binary analysis of exact Evolution X 16.0 / 20260915 / shiba / 11.11

**BUILD & OFFLINE RESEARCH ONLY · NO PIXEL HARDWARE · NO FLASH**

## Why U13?

GitHub web uploads limit individual files to 25 MB, while the confirmed
official Evolution X ZIP is **3,033,648,565 bytes**, nearly entirely an
embedded **3,033,640,593-byte `payload.bin`**. The user cannot reasonably
upload it via the normal GitHub editor. Instead the workflow downloads the
official full ZIP DIRECTLY on an ephemeral GitHub Actions runner and **keeps
large files out of the Git repository**.

The user's supplied `payload_properties.txt` reports:

```
FILE_SIZE=3033640593
FILE_HASH=kZO/l+sj+c97aUxtyKJUd/LhIqtTuT063uwfWZJwKQ0=
METADATA_SIZE=189195
METADATA_HASH=dFOED5c5AxRBN3gV+1TqYyTOcGLKrHiVYp+t8pkklqo=
```

These are from a user-supplied sidecar, **not yet proof** that the remote
official ROM download matches the user-provided properties. The workflow
checks the actual ZIP's payload entry size and SHA256 of its declared payload
metadata. The full ZIP SHA256 is the decisive official integrity test.

## Exact ROM identity from prior successful U12

- ROM `EvolutionX-16.0-20260915-shiba-11.11-Official.zip`
- Google Pixel 8 **shiba**, Android 16, Evolution X 11.11
- Source: [official Evolution X OTA shiba JSON](https://github.com/Evolution-X/OTA/blob/bka/builds/shiba.json)
- Full ZIP bytes: `3033648565`
- Official SHA256: `41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0`
- Official download: https://cdn.evolution-x.org/shiba/16/EvolutionX-16.0-20260915-shiba-11.11-Official.zip/download
- Previous separate U7 experimental boot SHA256:
  `1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa`

## Workflow

- [U13 binary verification GitHub Action](.github/workflows/phase-u13-exact-rom-binaries.yml)
- [U13 exact ROM / kernel / vendor forensic audit](scripts/u13_official_rom_audit.py)

Steps:

1. Prepare disposable GitHub Ubuntu runner workspace.
2. Download and SHA256-verify the U7 research-only reference `boot.img`.
3. Build the public `payload-dumper-go` tool from **pinned**
   source commit `c3a50ba8d784764c06143c1f82971cd81a77f9d6`
   and obtain its declared Go toolchain.
4. Download the **whole exact 3.03 GB ROM** from the official Evolution X
   CDN. Verify full **byte size and SHA256** and stop if incorrect.
5. Selectively extract **boot, init_boot, dtbo, vendor_boot,
   vendor_kernel_boot, vendor_dlkm, system_dlkm** into temporary workspace.
   Source is the verified ZIP, never a similarly named Android 17 / husky image.
6. Compute per-partition SHA256, inspect Android header versions and the
   **official** boot kernel's SHA256. Compare actual kernel payload bytes
   against the separately pinned experimental U7 kernel hash.
7. Inspect filesystem type; where ext4/EROFS supports safe offline extraction,
   sample `.ko` modules and their `vermagic`. Missing/unreadable .ko modules
   must remain **unknown**, never reported as compatible.
8. Upload only **U13_REPORT.md** and **U13_AUDIT.json** — small evidence
   files. Do not publish the 3GB ZIP, extracted firmware, module binaries or
   deployable images in GitHub artifacts.
9. No ADB/fastboot/partition operations, no hardware boot, no flash.

This is a real multi-GB GitHub Actions job. The workflow can fail because
the official CDN is unavailable, download times out, Go toolchain isn't
available, or payload extraction fails. In that event, inspect the logs and
do not claim verification succeeded. No silent fallback to an older ROM.

### Final decision criterion

Official ZIP verified + official kernel hash and vendor binaries measured
means we can finally **investigate the correct vendor pairing**. It does not
establish that Ubuntu's display, touchscreen, GPU, power, memory, boot
chain or security will work on the actual Pixel 8.

**No bootable Pixel 8 Ubuntu firmware is produced by U13. DO NOT FLASH.**

## U13 run #1 diagnostic and fix

- [Initial U13 CI run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38063861509) failed **before** downloading the 3.03 GB official ZIP, during the pinned `payload-dumper-go` build: `fatal error: lzma.h: No such file or directory`.
- The repo, U7 boot and pinned source/toolchain stages passed. Missing Ubuntu host dependency was identified as `liblzma-dev`, needed by the Go XZ CGo package.
- Added `liblzma-dev` to the host dependencies, and this documentation edit launches **U13 retry #2**. No ROM download, flashable image or device operation happened in run #1.
