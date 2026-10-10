# Phase U11 RESULTS — Pixel 8 shiba kernel and vendor module audit

**GITHUB ACTIONS SUCCESS — STATIC COMPATIBILITY AUDIT, NOT NATIVE BOOT PROOF**
**NO FLASHABLE ROM, NO PHONE ACCESS, NO PARTITION CHANGES.**

## Verified run and artifacts

- Date: **2026-10-10**
- [U11 GitHub Actions run #1 — SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38061539878)
- [U11 audit artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38061539878/artifacts/11673560827)
  - Name `shiba-u11-kernel-vendor-module-audit-1`
  - Artifact ZIP size **7,594 bytes**
  - Expires **2026-11-09 14:55 UTC**
  - Contents: `U11_REPORT.md`, `U11_AUDIT.json`, `U11_MODULE_INVENTORY.csv`.
- [U11 GitHub Actions workflow](.github/workflows/phase-u11-module-compat.yml)
  and [offline verification code](scripts/u11_module_compat_audit.py).

## What exact source was inspected?

Pinned public repositories:

- [Evolution X shusky Android 16 device tree](https://github.com/Evolution-X-Devices/device_google_shusky/tree/bka):
  `56006ae8162db285e776d85319d9942945b87194`.
- [Evolution X zuma Android 16 device-common tree](https://github.com/Evolution-X-Devices/device_google_zuma/tree/bka):
  `fba447c6317f23501dbac209b6479e458800c449`.
- [LineageOS device_google_shusky-kernels module metadata, lineage-23.2](https://github.com/LineageOS/android_device_google_shusky-kernels/tree/lineage-23.2):
  `9bba989e7dba6f33258049b113adcb33c89054e8`.

The current public device source declares **Linux 6.1** for Pixel 8 and
references the LineageOS module *manifest repository*. Critically, the
version pinned above contains **ZERO actual .ko driver binaries or .img
firmware**, just module lists and startup configurations. Consequently no
module binary SHA256, module `vermagic`, symbol CRCs or KMI pairing can be
established from these sources.

These public revisions are NOT known to be the exact installed
Evolution X Android 16 release currently on the user's Pixel 8.

## Concrete module-list findings

| Public list | Module file path entries |
| --- | ---: |
| Common `modules.load` | **209** |
| `vendor_kernel_boot.modules.load` | **209** |
| `vendor_dlkm.modules.load` | **62** |
| `system_dlkm.modules.load` | **59** |

The two 209-entry lists are **identical and in identical order**. Counts
refer to listed module paths, *not* the number of verified real installed
drivers; list contents overlap and are not all independent modules.

### shiba vs husky important difference

Board-specific init lists each name five module loads and differ at:

- **Pixel 8 `shiba`:** `goodix_brl_touch.ko`
- **Pixel 8 Pro `husky`:** `ftm5.ko`

Both board-specific lists also include `bcmdhd4398.ko`,
`snd-soc-cs35l41-i2c.ko`, `cs40l26-i2c.ko`, and
`snd-soc-cs40l26.ko`.

All five shiba startup module basenames were referenced somewhere in the
public module manifests. Four shiba startup names were not present in the
separate *recovery* module list; **this alone is not an error**, since recovery
and normal boot intentionally have different module selections.

Using Pixel 8 Pro-specific DTBO, boot or touch integration on the Pixel 8
cannot be justified by family resemblance.

## U7 research boot reverified

U11 re-downloaded the old [U7 experimental boot](PHASE_U7_RESULTS.md) and
confirmed:

- Android boot header version **4**
- Experimental compressed shusky kernel payload **16,515,476 bytes**
- U7 boot image SHA256:
  `1a1f78da7e77457afb406e9cbcffa395c09ffb5120c02fd9f6d3005041651ffa`
- Kernel payload SHA256:
  `8a3ec09cfc307e1f17b868437201b5e6f87a80840cc21bff8aea85e333db8229`

These hashes prove identity of the U7 research image, **not** that the
experimental kernel matches Evolution X's currently installed vendor modules,
device tree or Android Verified Boot chain.

## Readiness status

**Not ready to flash or boot Ubuntu on actual Pixel 8.** The blockers are:

1. Exact installed Evolution X Android16 build fingerprint and kernel build
   release (currently unknown).
2. Binary-matched vendor module set, module `vermagic` and full KMI proof.
3. Compatible shiba-specific DTBO, vendor boot/kernel boot ramdisks, display,
   touchscreen, GPU/Mali, Wi-Fi, USB-C display, power and security integration.
4. Verified physical Linux rootfs volume mapping plus reviewed rollback.
5. Actual phone hardware boot/test evidence — none yet.

The [successful U10 Ubuntu systemd execution](PHASE_U10_RESULTS.md) was
on a **generic QEMU ARM64 virtual machine** using Linux 6.6.89, not Tensor G3.

No bootable image was built by U11; no device connection, adb, fastboot or
flash occurred.

**U11 STATUS: SOURCE MANIFEST COMPARISON SUCCESS / PHONE FLASH READINESS FALSE.**
