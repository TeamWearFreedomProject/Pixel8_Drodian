# U27 — Pin down the real U25 watchdog VLA and kernel base-provider mismatch

**OFFLINE SOURCE/LOG AUDIT. NO PIXEL DEVICE. FLASH GATE: DENY.**

## The first actual U25 build was not successful

U25 [CI Run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38112313451) attempted to build shusky after selecting official CP2A common GKI commit `bd23337e42e794964a89f47596daf1209a25ee1a`, excluding user-approved optional external `CONFIG_USB_RTL8150`, and renaming only the legacy DWC3 register constant **inside** the vendor SoC code. The real `-Werror` compiler advanced beyond the USB error but failed on Google's Zuma watchdog source:

```text
private/google-modules/soc/gs/drivers/watchdog/s3c2410_wdt.c:723
error: variable length array used [-Werror,-Wvla]
char buf[max(NR_CPUS, PRINT_CPUS_LIMIT)];
```

It additionally emitted a **6.1.157 vs 6.1.124 base kernel provider mismatch**. Google's Kleaf implementations differ: some emit the mismatch as a warning and continue, some abort. Therefore **the presence of this message alone cannot prove which binary provider the build used**, and merely supplying `--use_prebuilt_gki=false` cannot be equated with full KMI agreement.

## Exact-source audit

The [U27 source audit CI](.github/workflows/phase-u27-kmi-watchdog.yml) fetches:

- U25 original failed compiler log, immutable source patches and exit result.
- U24 verified Git SHA40 for GKI, Google Pixel Bazelrc and Zuma SoC.
- The **actual** official watchdog source `057ab18a9cc0e318538b419eafc565a7fbe1d320`, by Google Gitiles.

It asserts the offending `char buf[max(NR_CPUS, PRINT_CPUS_LIMIT)];` **exists exactly once** at the matching revision before proposing any edit. The Linux `max()` macro may use a GNU statement expression and trigger VLA when used in a local array bound. The proposed U28 research-only repair is a compile-time conditional expression:

```c
char buf[(NR_CPUS > PRINT_CPUS_LIMIT ? NR_CPUS : PRINT_CPUS_LIMIT)];
```

This preserves the original maximum-sized buffer using the same constants, without disabling the critical watchdog, relaxing `-Werror`, bypassing module ABI checking, or modifying production firmware. The actual U28 build must prove whether it compiles; **this stage only verifies evidence**.

## Hard line

U27 PASS means source mapping and compiler-failure diagnosis PASS, **not** that the Pixel 8's vendor modules are 6.1.157-compatible. Need symbol/KMI checks, correct shiba DTBO/panel, physical read-only boot log plan, safe rootfs mapping and Android Verified Boot rollback evaluation, before any U30 on-device experiment.

**Real-device flash gate: DENY**. The physical Pixel 8 stays on original CP2A. The project owner leads, ChatGPT assists with public source verification and CI.
