# U32 — complete discoverable research-module CRC coverage (GitHub Actions only)

**Research status: PENDING CI evidence. REAL Pixel 8 boot/flash gate: DENY.**

## Why this is next

U30 [run #6](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38144121200) built genuine Linux **6.1.157** GKI from source and the full shusky dist successfully, unlike the earlier U28 old-prebuilt 6.1.124 build. U31 [run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38147914456) found **8,669** source GKI exports, **1,008 accessible `.ko` file paths**, but examined only **180**; those yielded **11,258** imported CRC comparisons with **0** discrepancies.

U31's first 180 are **NOT** evidence of whole-output compatibility, and even 100% agreement against the research GKI is **NOT** a trusted stock CP2A KMI/ABI comparison.

## U32 goal

[U32 source-only workflow](.github/workflows/phase-u32-complete-module-crc.yml) takes **immutable successful U31 metadata** (not copied binary modules), reproduces the U30/31 pinned-GKI 6.1.157 source build, shusky vendor build and provider-selection gates on an **ephemeral GitHub runner**, and performs an additional audit:

1. Enumerate **all** accessible `.ko` paths within the previous U31 scanning roots. Count them, compare with U31's old 1,008-path baseline, and group **byte-identical files by SHA256**. Content repetitions in different Bazel output paths are not presented as distinct binaries.
2. Independently query `modinfo` vermagic and `modprobe --show-modversions` for **each unique-content research module**; compare the imported symbol CRCs whose names occur in the **same isolated source GKI's** `Module.symvers`. Fail the new CI audit when a matching symbol's CRC disagrees, a module's vermagic prefix is invalid, a parser fails, or some discovered module cannot be read.
3. Count imported symbols absent from **base GKI** exports separately. These may be **vendor-to-vendor symbols** and are NOT automatically CRC discrepancies or stock CP2A compatibility proofs. This audit does not claim to inspect modules compressed inside proprietary vendor partition image containers.
4. Emit text/JSON only: complete unique-content module inventory, source GKI export counts, parsed imported-CRC counts, real mismatches, unresolved vendor imports, duplicate paths, and a **manifest of missing true stock CP2A reference inputs**. No `.ko` bytes, boot.img, DTBO, vendor images or flashable kernel are uploaded.

## Physical gate remains DENY

The actual Pixel 8 `shiba` stock CP2A kernel reports `6.1.157-android14-11-gbd23337e42e7-ab14791245`. The experimental research build advertises `6.1.157-android14-11` and contains deliberate source modifications. There is **no stock CP2A kernel symbol ABI/CRC reference**, trusted stock vendor module data, selected shiba panel DTBO validation, AVB/rollback/recovery validation, or verified Ubuntu rootfs + device boot. U32 cannot replace that missing input by examining its own modules harder.

**Managed Windows school PC:** no admin permissions, no local build/install or USB usage required. GitHub Actions runs on isolated cloud Ubuntu.

**NEVER FLASH OR BOOT THE EXPERIMENTAL RESEARCH KERNEL ON A REAL PIXEL 8.**
