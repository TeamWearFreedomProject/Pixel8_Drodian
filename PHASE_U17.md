# Phase U17 — Pixel 8 (shiba) native image research

**STATUS: BUILD EXPERIMENT IN PROGRESS; NO VERIFIED FLASHABLE SHIBA UBUNTU IMAGE.**

## Why a separate project stage?

The user has a **Pixel 8 (shiba)**, and confirmed that they experimentally
flashed multiple **Pixel 8 Pro (husky)** boot components plus an Ubuntu 26.04
sparse userdata image. The screen is dark, but USB presents VID:PID 0525:a4a2
(Linux RNDIS Gadget); the Windows 11 host reports Code 10. This is evidence
of *some* USB gadget enumeration, not proof of a complete Ubuntu boot.

The user identified the third-party boot package as
[Tensor Linux V1.0](https://github.com/Tenser-Linux/Tensor-Linux/releases/tag/V1.0),
whose project README supports **Pixel 8 Pro (husky)** only. They uploaded
nine husky boot-side images for read-only SHA and format checks, and the
Ubuntu `tensor-ubuntu-resolute-arm64.v5-gtk4.sparse.img` is linked by that
release but was **not** uploaded or inspected. These husky images are NOT
a supported shiba boot chain. See PR #2 provenance comment.

Existing [U16](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38096822658)
successfully started Ubuntu 26.04 ARM64 with **generic QEMU virtio-GPU DRM**,
Labwc Wayland, and two independent image captures. This **is not** a Pixel 8
Tensor G3 kernel, Mali driver, Google panel/touch driver, or native boot.

## Official public Google source reference

- Pixel kernel build documentation:
  https://source.android.com/docs/setup/build/building-pixel-kernels
- Android 16 Pixel 8 + 8 Pro kernel manifest branch:
  `android-gs-shusky-6.1-android16`
- Kernel manifest URL:
  https://android.googlesource.com/kernel/manifest
- Google shusky device kernel tree:
  https://android.googlesource.com/kernel/devices/google/shusky/
- Pixel 8 code name: **shiba**.
- Pixel 8 Pro code name: **husky**.
- **shusky** is a shared source family and must not be confused with proof
  that a resulting DTBO or display configuration is correct for shiba.

## U17 first build: kernel image inventory (GitHub Actions only)

[U17 workflow](.github/workflows/phase-u17-shiba-native-images.yml) resolves
the Google source manifest, syncs public shusky sources, and invokes the
upstream `build_shusky.sh` vendor-kernel component build on a disposable
GitHub Linux runner. This is an **Android 16 kernel-side research build**,
not yet an Ubuntu ROM. A separate Python
[image auditor](scripts/u17_shiba_image_audit.py) records file presence,
bytes, magic-format hints, and SHA256; it may include selected built outputs
under `research-images-UNVERIFIED/` with prominent non-flash labeling.

Possible kernel-source outputs (only if the actual build creates them):

- `Image`, `boot.img`
- `dtbo.img`
- `vendor_kernel_boot.img`
- `vendor_dlkm.img`, `system_dlkm.img`

**Do not invent, pad, relabel or copy husky parts as shiba parts.** Files
absent from the actual build must remain explicitly absent.

## Remaining integration / hardware blockers

The following components **cannot be declared ready** based solely on this
source-kernel build:

| Component | Requirement |
| --- | --- |
| `boot.img` | Exact kernel/GKI provenance and platform compatibility |
| `dtbo.img` | shiba-specific board, panel, touchscreen and overlay validation |
| `vendor_kernel_boot.img` | Compatible DTB/kernel-module ABI with selected ROM |
| `vendor_boot.img` | Device and ROM version-matched vendor ramdisks |
| `init_boot.img` | Reviewed native Ubuntu first-stage init and boot handoff |
| `vendor_dlkm.img`, `system_dlkm.img` | Correct kernel KMI and module dependencies |
| `vbmeta*.img`, `pvmfw.img` | Device-specific verified sources and boot-chain policy |
| `userdata.img` | Boot-tested physical rootfs device naming, mount, power, graphics |
| SSH / USB RNDIS | Tested gadget + network setup on actual shiba hardware |
| Panel output | Native DRM driver + shiba panel with verified framebuffer/display |

Previously available official Evolution X 16.0 shiba release metadata was
verified during U12, but the full 3GB OTA binary was unavailable in GitHub
Actions due to official CDN 403 (U13). The device was subsequently
modified by a husky port, then the user reported restoring the Google
**shiba-cp2a.260805.005** factory image. **Confirmed official version:
Android 17.0.0 (August 2026)**, not Android 16. Current successful Android
boot, exact active slot, verified partition coherence and bootloader lock
status have **not yet been independently checked**. Do not infer vendor ABI
from release names alone.

## Actual device baseline changed — 2026-10-11

User reports flashing the **Google Pixel 8 shiba factory package
`shiba-cp2a.260805.005`** after the husky Tensor Linux experiment.
Official Google factory listing identifies this precise build as
**Pixel 8 / shiba Android 17, August 2026**, with whole-factory-archive
SHA256 `26ca3017652d5df8d5002a449ef079637061165de02396634514387602aad177`.
Source: https://developers.google.cn/android/images?hl=ja
(Pixel 8 / shiba row, CP2A.260805.005).

**CRITICAL VERSION MISMATCH:** The U17 CI already running on
`android-gs-shusky-6.1-android16` is an **Android 16 research build**.
Even if it passes and produces kernel components, **DO NOT MIX**
those artifacts with the reported **Android 17 CP2A stock** vendor/system,
and do not label them CP2A compatible. A future investigation must resolve
the exact public Android 17 shusky kernel source manifest, matching
KMI/module ABI, shiba DTBO/panel components, and verified stock image
provenance before any integration. Continue treating this existing CI run
as independent, non-deployable source inventory only.

The reported factory flash does NOT by itself establish successful normal
boot or relocked bootloader; request explicit confirmation before assuming
stock is fully operational. No new flashing or slot changes are necessary
for this documentation update.

## Safety scope and criteria to advance

- GitHub branch: `research/u17-shiba-native-images`.
- All writes are to source files in GitHub and temporary GitHub runner disk.
- No connection to the user's Pixel, no ADB / fastboot / OTA write / slot
  switch / boot / format / erase operations.
- No automatic merge to main; all outputs remain research-only.
- **A green CI source-build is not evidence of working Ubuntu on the phone.**
- First validate a real shiba-compatible boot chain, module KMI, and
  recovery strategy; only then review any future real-device test.
- Do not recommend flashing this U17 experimental bundle.

## Credits

The Pixel 8 Ubuntu hardware-port research project is led by the repository
owner, with ChatGPT assisting with experimental CI configuration, source
cross-checks and audit scripts. The upstream Google source, Android Open
Source Project kernel documentation, and the prior project's dependencies
must remain attributed. This research does not claim a released, working
Pixel 8 Ubuntu port.
