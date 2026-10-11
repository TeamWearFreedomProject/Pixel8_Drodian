# U29 — Pixel 8 shiba CP2A / Linux 6.1.157 initial-boot NO-GO preflight

**THIS STAGE DOES NOT AUTHORIZE A PIXEL 8 BOOT, REFLASH OR BOOTLOADER CHANGE.**

## Objective
The target **U30** is the first genuine Pixel 8 Ubuntu/Linux shell boot, if and only if the engineering and recovery prerequisites are proven. U29 consolidates existing evidence so a successful generic CI/QEMU build cannot be mistaken for physical Tensor G3 safety.

The [U29 workflow](.github/workflows/phase-u29-firstboot-no-go.yml) downloads genuine reports from **successful** U18 (official CP2A matching GKI Git SHA), U19 (old 6.1.124 vendor `.ko` mismatch), U20 (offline Ubuntu 26.04 ext4 and corrected guarded initramfs), U23 (real QEMU Linux-to-Ubuntu systemd boot), U24 (Google old GKI provider + DWC3 header conflict), U26 (four actual QEMU first-stage fail-closed cases), and U27 (Google source-pinned watchdog VLA failure). It queries the **actual GitHub API status** of [U28 real shiba source-only rebuild](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38113211356); it does NOT assume that a draft U28 source file means the build passed.

U28 may be queued or in progress when U29 starts. If so, U29 explicitly records `in_progress`, preserving an unchanged **NO-GO** verdict. Re-run the U29 workflow or update its source only after U28 finishes, to include a completed compiler status. In any case, a green source build is not signed stock Android boot firmware or permission to use images on hardware.

## U30 preflight conditions still unproven
- Exact working CP2A Pixel 8 **shiba** compatible device kernel, vendor module KMI/symbol CRC and ABI.
- Exact board DTBO selected correctly for shiba, not husky; touch/display/GPU/power drivers.
- Reliable early USB/serial logs and demonstrated safe kernel diagnostics.
- Actual phone's bootloader state, AVB/signature and rollback indexes, **read only** checks and expert review.
- Full backups and verified way to return to the same or newer working **CP2A**, without downgrading bootloader/rollback metadata.
- Rootfs path proven not to conflict with Android userdata or any active partitions.
- Explicit user approval of a reviewed and reversible test method; no unknown firmware flashing.

U29's job has **no device connection** and creates only JSON and Markdown reports. There are no flashable `boot.img`, `init_boot.img`, `vendor_boot.img` or `userdata.img` packages. We never apply unknown Pixel 8 Pro husky firmware or blindly change slots.

**REAL DEVICE FLASH GATE: DENY.** No actual Pixel 8 hardware Linux boot has been observed; U30 remains a *goal*, not a safety deadline. Research led by project owner, with ChatGPT providing tools/scripts and upstream credits to Android/Google, Ubuntu, Linux and QEMU.
