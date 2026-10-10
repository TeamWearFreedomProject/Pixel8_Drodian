# Phase U8 — Ubuntu rootfs read-only mount and guarded initramfs handoff research

**BUILD ONLY • NOT BOOTABLE • NO PHONE / NO FASTBOOT / DO NOT FLASH**

## Question: was the earlier ZIP actually used?

Yes for research, **not** as the directly copied kernel or a flashed firmware.

- User-provided Pixel 8 Pro `husky-boot-images.zip` was compared in U2.
  The independently fetched official [Tensor Linux V1.0 release](https://github.com/Tenser-Linux/Tensor-Linux/releases/tag/V1.0)
  matched the prior ZIP's pinned SHA256:
  `3ef1f4e6675ffef522d939e5bb7dd9fdb06c6da60cde784b4ec7fe14e99dff9f`.
- U7 `boot.img` uses an earlier **experimental Pixel 8 shiba Google shusky CI
  kernel**, not the husky Tensor Linux `boot_a.img`.
- U7 `init_boot.img` contains an ARM64 static BusyBox from official Ubuntu
  26.04 sources and an inert ramdisk, **not** a copied husky ramdisk.
- U8 separately re-downloads and verifies Tensor Linux's exact matching ZIP
  and inspects the **header layout only**. Never substitute husky firmware for
  the shiba firmware or claim module/DTBO compatibility.

## U8 implementation

- [Guarded early init script](scripts/u8_init): actual BusyBox shell script
  that checks for exactly one explicitly specified Linux rootfs UUID and
  a deliberately explicit research opt-in token in kernel cmdline.
- It checks Linux ext4 filesystem type and `SHIBA_UBUNTU` label before any
  optional mount, uses `ro,noload` to avoid journal replay, validates
  `ID=ubuntu` and `VERSION_CODENAME=resolute`, checks that a PID1
  executable exists and has a `switch_root` handoff path.
- On errors it **fails closed** without formatting or overwriting storage.
  There is no automatic Android userdata discovery or fallback mounting.
- The actual Pixel 8's Linux rootfs filesystem UUID is not identified.
  Any offline U6 image UUID is **only the ID inside that image**, not
  evidence of a working phone-side block mapping.
- The U6 rootfs' PID1 and bootable system integration have not been
  established; the script's presence is **NOT** a demonstrated boot.
- [U8 offline audit script](scripts/u8_verify.py) cross-checks the 2 GiB
  U6 ext4 image (SHA256 pinned), U7 init_boot (SHA256 pinned), official
  husky ZIP and initramfs shell structure. Model tests are not boot tests.
- [U8 GitHub Actions workflow](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u8-rootfs-handoff.yml)
  extracts static ARM64 BusyBox from the hash-verified U7 research artifact,
  replaces its inert `/init` with the guarded script, verifies BusyBox shell
  syntax under QEMU user mode and builds a standalone LZ4 cpio initramfs.
- Outputs a `.cpio.lz4` only, with JSON/Markdown evidence.
  **U8 does NOT build new boot.img/init_boot.img or flashable firmware.**

## Unresolved before any genuine phone test

1. Actual installed Evolution X Android16 kernel/vendor/DT/KMI match.
2. Pixel8 first-stage module dependency and vendor ramdisk merge ordering.
3. Safe, independently identified Linux rootfs storage (no reuse of active
   Android userdata by guessing its path).
4. Confirmed functional Ubuntu PID1, boot services and rootfs write policy.
5. Hardware-specific DRM, touchscreen, Mali GPU, USB-C monitor output and
   power management.
6. Tested rollback/rescue strategy and explicit hardware review.

**U8 CI success will mean the ramdisk assembled and static safety checks
passed. Actual rootfs mount, switch_root and device boot remain UNTESTED.**

Plan addition requests the first CI run automatically.
