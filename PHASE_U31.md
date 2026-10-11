# U31 — offline ABI, symbol CRC, and shiba board/package audit

**Status: RESEARCH ONLY — PHYSICAL PIXEL 8 FLASH GATE: DENY.**

## U30 achieved a genuine kernel build

[U30 Actions run #6](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38144121200), the fully source-based Linux **6.1.157** GKI and shusky modules/dist compilation, completed successfully. Its independently recorded experimental kernel `Image` is **35,633,664 bytes** and SHA256 `86c8bd5a89088033bc01dec4e40fb40e37238d567064328b4c49b08dc4d9cdbc`. U30 verified source and distro `Image` digests match, and their banner reports `6.1.157-android14-11`, unlike the former incorrectly selected **6.1.124**.

**This does NOT prove equivalence to the stock Pixel 8 shiba Android17 CP2A.260805.005 kernel** `6.1.157-android14-11-gbd23337e42e7-ab14791245`, whose vendor modules, version details, and AVB/rollback state have not been obtained as trusted references.

## U31 offline test design

The [U31 workflow](.github/workflows/phase-u31-offline-abi-audit.yml) runs solely on a disposable GitHub-hosted Ubuntu 24.04 VM, including when the project's owner only has a school PC without admin rights. It reuses U30's source pins, source-only compiler flags, old RTL8150-only exclusion and narrow reviewed vendor macro adaptations, **without modifying the device**.

1. Fetch the *verified U30 success report artifact* and check it against the complete pinned SHA256, byte length, and real Bazel exit.
2. Repeat source GKI 6.1.157 and full shusky vendor build on GitHub. U30's configured-source dependency and stale-old-prebuilt checks must pass again; a compiler failure stops and preserves logs.
3. Audit real output `Image` byte identity between the direct source GKI and shusky dist (reproducible historical U30 digest is separately reported, not falsely required across different builds).
4. Hash source GKI `Module.symvers`, count exports, inventory actual emitted `.ko` if present; inspect available module `vermagic` and compare imported exported-symbol CRCs against *only the new research GKI*. If modules cannot be found or CRCs aren't present, mark that evidence **missing**, not passed.
5. Record the DTBO container's Android header / number of entries and SHA256, and hash selected kernel, `vendor_dlkm`, `system_dlkm`, and vendor boot output files. No kernel, partition image or flashable binary is uploaded.

## What U31 cannot establish from public research alone

- A source-build `Module.symvers` CRC match against *the same source build* does **not** prove matching the actual stock CP2A vendor binary modules. Trusted stock `Module.symvers`/vendor module input is missing.
- A parseable shusky-family DTBO does **not** prove the **shiba** screen/panel/board overlays match the phone.
- Compiled Mali GPU, Goodix touch, Wi-Fi and USB modules do not prove real-device functionality or clock/power/security operation.
- No verified bootloader/AVB rollback, reliable rescue/recovery process, and safe Linux rootfs storage plan are available. Never guess a slot, filesystem or flash partition.
- This step is not an Ubuntu rootfs deployment or a boot attempt. Any reported `SUCCESS` means CI/research audit complete **only**.

All research tooling in GitHub Actions is independent of Windows administrator rights. Keep U31 as a **Draft PR** until evidence is reviewed; do not merge diagnostic scripts into a production install flow.

**REAL DEVICE FLASH GATE: DENY.**
