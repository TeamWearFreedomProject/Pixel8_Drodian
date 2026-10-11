# U30 — Trace exact Pixel 8 shiba CP2A GKI 6.1.157 provider

**Real Pixel 8 boot is NOT approved. FLASH GATE: DENY.**

## Why U28 green is not a production Pixel 8 kernel

In [U28 Run #10](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38134737015), Google Bazel **really passed all 439/439 actions**, compiled vendor modules, and assembled experimental shusky-family kernel/dist images.

However, the actual `Image` binary in that build advertises:

```text
6.1.124-android14-11-g8d713f9e8e7b-ab13202960
```

The currently running Pixel 8 **shiba** stock firmware `CP2A.260805.005` uses:

```text
6.1.157-android14-11-gbd23337e42e7-ab14791245
```

In the same successful U28 build, Bazel emitted:

```text
ERROR: KMI or sublevel mismatch before running make modules_install:
  @//private/devices/google/shusky:kernel: 6.1.157-android14-11
  @//aosp:kernel_aarch64_download_or_build: 6.1.124-android14-11
```

The former was **nonfatal for compilation, not proof of ABI compatibility**. Both the Linux version and binary provenance must agree before any proposed production install or physical boot.

## The U30 experiment

The [U30 source-provider trace workflow](.github/workflows/phase-u30-provider-trace.yml) takes the **last successful U28 JSON artifact**, not an imagined kernel version. It syncs pinned Google `android-gs-shusky-6.1-android16` public sources and checks out GKI r9 `bd23337e42e794964a89f47596daf1209a25ee1a` (actual `aosp/Makefile` Linux 6.1.157).

Using the **exact U28 Bazel flags** (`--config=use_source_tree_aosp --use_prebuilt_gki=false --use_signed_prebuilts=false --download_prebuilt_gki_fips140=false`), it executes five read-only Bazel configured-target queries:

1. `//aosp:kernel_aarch64_download_or_build`: actual `label_kind`.
2. `//aosp:kernel_aarch64`: source kernel target.
3. Former target's `--output=build`: resolved configuration/implementation.
4. `//private/devices/google/shusky:kernel`: device target.
5. `somepath(//private/devices/google/shusky:kernel, //aosp:kernel_aarch64_download_or_build)`: dependence edge if present.

Query logs, exact Git SHA40, Google source manifest, evidence hashes and source-rule references go into a research-only artifact. Any missing essential query fails the trace rather than inventing a fixed provider.

Official [Google Bazelrc at pinned source](https://android.googlesource.com/kernel/devices/google/common/+/397babd94c06783d8430c838475955f0b6ff63c2/device.bazelrc) defaults to the old GKI build number `13202960` and prebuilts on, but offers `use_source_tree_aosp` overrides. That configuration **does not, by itself, prove** which binary `shusky:dist` ultimately packaged. U30's job is to locate the actual selected target/version without a risky physical test.

## U30 first-boot checkpoint

U30 no longer promises first Pixel 8 Ubuntu boot by a numbered deadline. The former [U29 physical safety NO-GO](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/pull/14) remains intact: no verified **CP2A-native** vendor module ABI/KMI/CRC compatibility, shiba panel+DTBO and touch/GPU runtime, exact AVB/rollback and backup/recovery, safe Ubuntu rootfs storage mapping, or reliable hardware logs.

The complete path is **identify real GKI provider → build genuinely matching 6.1.157 → verify vendor KMI and board configuration → independently assess on-device safety → only then consider a user-approved reversible experiment**.

**No phone connected, no bootloader/slots/partition writes, and no flashable image released by U30.** The project owner leads; ChatGPT provides public-source research and CI instrumentation.
