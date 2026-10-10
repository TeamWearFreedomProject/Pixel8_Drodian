# Phase U3 results — native Ubuntu 26.04 ARM64 with mobile + desktop GUI packages

**SUCCESS — REAL ARM64 GUI USERSPACE ARTIFACT — NOT BOOTABLE — NO PHONE ACCESS**

- Date: 2026-10-10
- Workflow: [Ubuntu U3 successful Actions run #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38042365918)
- Result: **success** (all GitHub Actions steps succeeded).
- GUI userspace artifact: [`shiba-u3-ubuntu-arm64-gui-NOT-BOOTABLE-3`](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38042365918/artifacts/11666513724)
  - GitHub artifact ZIP size: **154,585,352 bytes** (~154.6 MB).
  - Expires **2026-10-17 09:55 UTC** (~18:55 JST).
- Audit report artifact: [`shiba-u3-audit-3`](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38042365918/artifacts/11666124230)
  - GitHub artifact ZIP size **26,328 bytes**.
  - Expires **2026-11-09 09:55 UTC**.
- Tar archive: `ubuntu-26.04-arm64-u3-gui-NOT-BOOTABLE.tar.xz`
- Verified tar SHA256:
  `40944e9e9f9a75d2ce7bb447f3405c6704c26b372cdd85894f2b71572179bd7a`
- CI checksum command returned **`ubuntu-26.04-arm64-u3-gui-NOT-BOOTABLE.tar.xz: OK`**.

## What was actually verified in disposable GitHub Actions CI

- Authenticated, previously built Ubuntu 26.04 ARM64 U1 base filesystem by its pinned SHA256.
- Installed both GUI package families from the official Ubuntu 26.04 `main/universe` repositories via ARM64 QEMU binfmt chroot.
- Inspected `dpkg` package status: **`install ok installed`** for all required packages.
- Confirmed five directly inspected executables have native AArch64 ELF headers (machine 183).
- `phosh` was checked through installed `arm64` package metadata rather than assuming its executable lives at `/usr/bin/phosh`.
- Added a manual **Labwc** Wayland session entry and research-only JSON session policy.
- Saved package inventory, installation log, validator report, tarball and SHA256 as separate artifacts.
- **Never** generated boot/firmware partitions or touched an actual Pixel 8.

## Installed package versions

| Role | Package | Version |
| --- | --- | --- |
| Touch-oriented phone shell | `phosh` | `0.54.0-1` |
| Phone Wayland compositor | `phoc` | `0.54.0-1` |
| On-screen keyboard | `phosh-osk-stevia` | `0.53.0-1` |
| Window-stacking desktop compositor | `labwc` | `0.9.3-1` |
| Desktop panel | `waybar` | `0.15.0-1` |
| Terminal | `foot` | `1.25.0-1` |
| Output profile utility | `kanshi` | `1.9.0-1` |
| X11 compatibility | `xwayland` | `2:24.1.10-1` |
| User session D-Bus | `dbus-user-session` | `1.16.2-2ubuntu4` |

## Important boundaries

This is a **real Ubuntu ARM64 rootfs containing GUI userspace software**,
but it is not a bootable Pixel 8 operating system or working screen output.

- No display, touchscreen, GPU, camera, audio, Wi-Fi, USB-C DisplayPort Alt Mode, power management or radio hardware access was tested.
- Compositors were **not** launched on a real display in CI.
- Installing two GUI environments does **not** automatically transition between them.
- `kanshi` is installed for future output profile research, but no shiba-specific hotplug, monitor identification or automatic session switch works in U3.
- Current user-reported phone ROM is **Evolution X Android 16**; previously uploaded Android 17 factory vendor/kernel metadata are a separate, older reference, not known to match the current phone.
- No KMI/ABI compatibility with the current Evolution X installation has been checked.
- No ADB, fastboot, phone connection, firmware images or flashing at any point.

## Lessons from CI attempts

1. First run failed only because the old U1 checksum manifest named `output/` paths that are absent after downloading as an artifact; corrected by verifying against its pinned hash.
2. Second run installed the GUI packages successfully but the validator incorrectly required an ARM64 ELF at `/usr/bin/phosh`; corrected by using ARM64 package metadata for Phosh.
3. **Run #3** passed installation, validator, archiving and artifact upload.

## Next possible work: Phase U4 (research only)

- Inspect Tensor Linux `huskyfe`, `glproxy`, `vkproxy` and the limits of Android Mali driver integration on Tensor G3.
- Research Pixel 8 shiba native display and touchscreen paths plus external USB-C display capability from Google kernel source / DT and ROM metadata.
- Assess future session mode-selection design without claiming working automatic plug-and-play.
- Record Android16 Evolution X vendor/kernel compatibility only when its exact upstream software provenance is verifiable; do not guess from the older Android17 factory images.

**BUILD ONLY • NOT A ROM • DO NOT FLASH • NO PHONE OPERATIONS**
