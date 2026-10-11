# U26 — Ubuntu first-stage fail-closed QEMU boot controls and Pixel 8 U30 safety gate

**REAL DEVICE FLASH GATE: DENY. NO DEVICE BOOT AND NO BOOT PARTITION IMAGES.**

## Objective
Extend the genuine U23 ARM64 **QEMU-only** kernel → guarded U20 initramfs → Ubuntu 26.04 ext4 → systemd test with **negative cases** that exercise the actual `/init` and real generic QEMU guest, rather than source-code grep or bare host mock commands.

The first-boot guard expects a unique explicit `u8.rootuuid=...` and `u8.research_gate=I_UNDERSTAND_THIS_IS_UNVERIFIED`, and examines the filesystem itself using a dedicated **read-only** ARM64 ext4 UUID-and-label probe. It never guesses the physical Pixel's Android partitions. Existing boot state remains pure Android17 CP2A.

## Four real negative guest boots
Using the hash-verified old U9 generic ARM64 6.6.89 kernel and the **new U20** corrected ARM64 first-stage, run real QEMU virtual machines with the original 2 GiB U6 Ubuntu 26.04 rootfs supplied as `format=raw,readonly=on`:

1. Correct offline rootfs UUID but no opt-in research gate → first-stage must stop without launching Ubuntu.
2. Invalid UUID syntax with opt-in → must stop.
3. Two `u8.rootuuid` parameters with opt-in → must stop.
4. Well-formed but nonmatching UUID with opt-in → must stop rather than silently select another partition.

Each case must show its actual `U8 HALT` line and must **not** show Ubuntu `systemd[1]`. Source artifacts are checked by SHA256 both before and after the VM runs.

## Cross-phase preflight
CI also loads actual prior official verification artifacts:

- U18 [exact GKI 6.1.157 source commit](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38101661379)
- U19 [6.1.124 legacy driver ABI incompatibility](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38103774760)
- U20 [new guarded static ARM64 first stage + Ubuntu rootfs](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38104039752)
- U23 [real QEMU systemd PID 1 handoff](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38107883009)
- U24 [Google Bazel prebuilt default 6.1.124 and DWC3 header collision source audit](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38112137454)

**U25** separately attempts a source-only shiba 6.1.157 build and remains an open device-kernel ABI investigation. U26's generic VM is **not** evidence for U25 kernel bootability. The U26 gate must remain **DENY** even if all QEMU negative tests succeed.

## Definition of success and limitations
Success means four genuine QEMU guest abnormal-input tests safely fail closed and the positive Ubuntu systemd test from U23 remains independently validated. It does **not** mean that real Pixel 8 shiba will boot, that storage layout is known, that Mali/DRM/touch/USB works, or that Android Verified Boot's signature/anti-rollback requirements have been satisfied.

Before a physical first boot around the aspirational U30 milestone, the project still needs verified CP2A-compatible shiba kernel+vendor modules with KMI/CRC, correct shiba DTBO and panel, no loss of USB diagnostics, safe rootfs location, backup and recovery plan, and externally reviewed AVB/rollback chain.

U26 creates JSON/Markdown failure-injection reports and generic VM serial logs **only**. Never outputs, flashes, or even requests device-specific `boot.img`, `init_boot.img` or `userdata.img`. Project owner leads; ChatGPT assists with source verification and virtual testing, credit to upstream Google AOSP, Ubuntu and Linux/QEMU projects.
