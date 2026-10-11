# U23 — Real QEMU ARM64 Ubuntu 26.04 boot with corrected U20 early initramfs

**NO Pixel 8 hardware access, NO Android boot images, NO flash or rollback action.**

## Why U23 matters

U9 previously genuinely booted **generic ARM64 Linux 6.6.89** in the QEMU `virt` machine, used a guarded first-stage initramfs, read-only mounted a real 2 GiB Ubuntu 26.04 ext4 filesystem, and reached Ubuntu `systemd[1]`. But **U20 found an obsolete first-stage script** inside U8's older initramfs and rebuilt it to the reviewed current `scripts/u8_init`, including a statically compiled read-only ext4 UUID/label helper.

U23 therefore tests whether **that newer corrected U20** initramfs still works *as actual Linux first-stage code* rather than trusting static grep/shell syntax alone.

## Workflow

The GitHub Actions job [U23 workflow](.github/workflows/phase-u23-ubuntu-handoff-qemu.yml) uses **exact pinned real artifacts**:

- [U6 Ubuntu 26.04 ARM64 2GiB ext4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38047914957), SHA256 `d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e`.
- [U9 generic QEMU kernel 6.6.89](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38059787754), SHA256 `718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc`.
- [U20 corrected ARM64 BusyBox/initramfs](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38104039752), SHA256 `827ded5bce36ce87238645536a77ce3a464236edbeaaa61cd1bba617d8d72c1c`.
- [U18 *separate* official GKI 6.1.157](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38101661379), used for **provenance checks, not as the QEMU guest's kernel**, SHA256 `384f1aca6a5b040a7f0fe6d3ff5f39b8813256827bf0b2f622126b2eb6d0386c`.

The workflow first verifies hashes and compares U20 packed `/init` against exact reviewed source. It instruments a **throwaway VM-only copy** to emit stage markers, then runs a negative test without the required UUID and a positive test using the **offline U6 rootfs**. The guest sees the ext4 image as a **read-only virtual disk**, never phone partitions. Serial logs must prove the relevant Linux boot, readonly filesystem mount, Ubuntu 26.04 identity, `switch_root` attempt and genuine Ubuntu `systemd[1]` messages. This is a stricter end-to-end test than just checking file hashes.

## Boundary and expected results

If U23's CI passes, it proves **the corrected early userspace design is capable of reaching Ubuntu systemd on generic QEMU ARM64**, not that Google's Tensor G3 drivers work. Even perfect QEMU logs do not establish Pixel 8 CP2A KMI, exact board DTBO/panel/touch, proprietary Android Verified Boot rollback state, physical Ubuntu rootfs storage mapping, screen output, or native Ubuntu startup.

U22 separately attempts an experimental **6.1.157 shusky vendor rebuild**. U23's generic QEMU test does not cancel U22's missing Pixel driver work.

No physical Pixel 8 test and **REAL DEVICE FLASH GATE: DENY**. Stacked draft PR; project owner leads, ChatGPT assists, Ubuntu/Linux/Google AOSP retain upstream attribution.
