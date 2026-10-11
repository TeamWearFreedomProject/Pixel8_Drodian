# U28 — Real shiba kernel/drivers build: pinned 6.1.157 + watchdog and USB fixes

**Research-only Linux kernel build. Never boot or flash the resulting images.**

## U27 inputs validated
- Official CP2A-related upstream GKI `android14-6.1-2025-12_r9` source commit `bd23337e42e794964a89f47596daf1209a25ee1a`.
- Official Google Zuma SoC source `057ab18a9cc0e318538b419eafc565a7fbe1d320`.
- [U27 SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38113084815), checked real U25 failed compiler log against upstream watchdog C source SHA256.
- **U25 FAIL:** Google Zuma watchdog `char buf[max(NR_CPUS, PRINT_CPUS_LIMIT)]` was diagnosed as VLA under `-Werror,-Wvla`. Legacy 6.1.124 base-provider KMI warning appeared despite explicit source-only flags. U25's DWC3 name conflict was no longer present.

## Run U28 on a disposable GitHub Linux runner

1. Fetch official shusky public Android16 family sources, then checkout the *exact r9 6.1.157 GKI common commit*.
2. Reapply U25's narrow CI-only USB changes: exclude the user-approved obsolete **external** RTL8150 USB LAN driver; rename only the conflicting old **vendor DWC3 register constant** within the Google SoC project, without disabling internal USB or changing its register address.
3. Independently require U27 source SHA and replace **one exact expression only** in the Google watchdog file, preserving watchdog functionality and `-Werror`:
   ```c
   char buf[(NR_CPUS > PRINT_CPUS_LIMIT) ? NR_CPUS : PRINT_CPUS_LIMIT];
   ```
4. Invoke an independent Bazel `cquery` for the old `kernel_aarch64_download_or_build` target using the requested source-tree flags. Capture the result even when the provider cannot resolve. **Do not call a compile success or a mere cquery success KMI proof**.
5. Re-attempt the real Google shusky kernel/module Bazel build with prebuilt-GKI and signed-prebuilts explicitly disabled. Preserve true compiler exit; report version, kernel file SHA256, recurring KMI warning, USB and watchdog compiler errors. Upload **no flashable boot image**.

All source changes happen on ephemeral GitHub Actions workspace only; review source diffs and report in artifacts. A successful U28 compiler job is still **not** a CP2A stock-signed image nor evidence of compatible shiba DTBO, display/touch, device USB logging, vendor ABI symbol CRCs or Ubuntu rootfs startup on Tensor G3.

## What is actually required for U30 real device first boot
Matching vendor and exact 6.1.157 GKI KMI, correct shiba panel and DTBO, validated USB diagnostics, physical bootloader/AVB rollback and recovery, safe storage mapping with backups, complete reviewed boot chain. U29 will summarize actual evidence as a **non-deployable preflight report**.

**REAL DEVICE FLASH GATE: DENY.** No ADB, fastboot, flash, boot or partition action occurs in U28. The user still has working original CP2A Android 17.
