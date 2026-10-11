# U21 — Google shusky source identification for Pixel 8 CP2A 6.1.157

**Goal:** tie the already verified physical Pixel 8 shiba CP2A kernel baseline to Google's official public source layout, without mistaking a similarly named source branch for an exact production vendor release.

## Known verified device
- Stock factory package: `shiba-cp2a.260805.005` (Android 17).
- ADB-observed `uname -r`: `6.1.157-android14-11-gbd23337e42e7-ab14791245`.
- U18 built Google's official GKI `android14-6.1-2025-12_r9`, commit `bd23337e42e794964a89f47596daf1209a25ee1a`, a matching **upstream GKI source commit**. Rebuilt binary release is `6.1.157-android14-11-maybe-dirty`, not bit-for-bit stock.

## Procedure
The [U21 source-map job](.github/workflows/phase-u21-source-map.yml) reads the U17 and U18 **real successful GitHub Actions archives**, checks the U17 kernel SHA and GKI commit, parses their **resolved full Git manifests**, inventories separate `shiba` and `husky` DTBO/DTS filenames, and probes the public Google manifest branch names.

Use the Google public source-of-truth repository at https://android.googlesource.com/kernel/manifest . U17's source branch is `android-gs-shusky-6.1-android16`. A branch name containing “android16” is **not** disqualified from Android17 userspace automatically; the GKI/KMI family is `android14-6.1` and the Git commit, module compatibility and shiba hardware are what must be verified.

## Success criterion
Successful **source mapping** means the project pinned the actual public Git source SHAs, not that those SHAs necessarily reproduce CP2A's signed vendor binaries.

- U17 shusky generated a **6.1.124** family of vendor modules.
- Stock CP2A uses **6.1.157** GKI. The old modules were **not** validated with 6.1.157.
- Physical `shiba` and `husky` overlays and touch modules differ: do not treat one as interchangeable with the other.
- U22 will try compiling vendor components with exact GKI **on GitHub only**, and record a real compile result or missing upstream integration sources.
- U23 will check offline Linux boot readiness while respecting unresolved KMI, DTBO, USB, AVB and rollback provenance.

**NO PIXEL 8 FLASH/BOOT, NO DEVICE CONNECTION, NO PARTITION/SLOT CHANGES.**
**REAL-DEVICE FLASH GATE: DENY.** This research remains a Draft PR and is not a release. Owner leads research, ChatGPT helps with code and auditing; Google AOSP sources retain attribution.
