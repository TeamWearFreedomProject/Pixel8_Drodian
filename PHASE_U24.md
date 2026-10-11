# U24 — Why the CP2A 6.1.157 / shusky 6.1.124 hybrid failed

**REAL DEVICE FLASH GATE: DENY. SOURCE PROVENANCE / FAILURE DIAGNOSIS ONLY.**

## Pin exact official Google sources
- Exact r9 GKI common source: `bd23337e42e794964a89f47596daf1209a25ee1a`, matching the source suffix of the working Pixel 8 shiba `CP2A.260805.005` kernel.
- Google Pixel common Bazelrc commit: `397babd94c06783d8430c838475955f0b6ff63c2`.
- Google Zuma SoC driver sources: `057ab18a9cc0e318538b419eafc565a7fbe1d320`.
- Real prior [U22 diagnostic Run #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38108299006) resolved manifest and compiler failure output are verified before drawing conclusions.

## Root cause #1 — Bazel silently prefers legacy prebuilts
The official pinned Google `device.bazelrc` contains:
```text
build --action_env=KLEAF_DOWNLOAD_BUILD_NUMBER_MAP="gki_prebuilts=13202960,gki_prebuilts_aarch64_16k=13202960"
build --use_prebuilt_gki=true
build --use_signed_prebuilts=true
```
That build number corresponds to the **old 6.1.124 GKI** while the manually switched source is **6.1.157**. This is exactly why U22's mixed build emitted:
```text
KMI or sublevel mismatch before running make modules_install:
  shusky kernel: 6.1.157-android14-11
  base GKI provider: 6.1.124-android14-11
```
The official Google Bazelrc also provides `--config=use_source_tree_aosp`, which switches `--use_prebuilt_gki=false` and `--use_signed_prebuilts=false`, and the underlying Bazel flags can be explicitly overridden. U25 will test a **source-only** provider — never substitute an older prebuilt or suppress the KMI check.

Official revision reference:
https://android.googlesource.com/kernel/devices/google/common/+/397babd94c06783d8430c838475955f0b6ff63c2/device.bazelrc

## Root cause #2 — Internal USB driver API collision
The Google Zuma kernel module header defines the `DWC3_LLUCTL` hardware register constant as `0xd024`. Newer upstream GKI uses a function-like macro indexed by lane:
```c
#define DWC3_LLUCTL(n) (0xd024 + ((n) * 0x80))
```
U22 compiler stopped under `-Werror,-Wmacro-redefined`, specifically in the **SoC integrated USB DWC3**, not in the optional external USB RTL8150 Ethernet driver.

U25 will investigate a **targeted research-only** driver-local name/API adaptation instead of switching off essential USB functionality or weakening `-Werror`. Vendor symbol CRC and runtime compatibility remain unknown even when compilation succeeds.

## U24 CI
Read-only [workflow](.github/workflows/phase-u24-provider-audit.yml) downloads exact Gitiles revisions, confirms SHA40 provenance with U22 manifest and compiler log, audits both DWC3 header definitions, emits JSON and Markdown. No code patched or binaries built in this phase.

**Successful U24 source audit is NOT a working Pixel Linux kernel or a boot image. No phone accessed.**
