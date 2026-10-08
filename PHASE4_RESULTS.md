# Phase 4 results — source-built Pixel 8 Halium kernel experiment

**SUCCESS: 8/8 requested configuration entries verified in compiled output**

- Date: October 8, 2026
- Workflow: [Phase 4 Actions Run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37728429488)
- Result: **success** after approximately **32 min 42 s**
- Manifest: `android-gs-shusky-6.1-android16`
- Build mode: Google shusky Kleaf with source GKI / `pixel_debug_common` fragment
- Artifact: `shiba-phase4-kernel-diagnostics-1` (GitHub reported expiry 2026-10-15 05:10 UTC)

## Confirmed kernel config changes

| Symbol | Phase 2 baseline | Phase 4 compiled candidate | Requested |
| --- | --- | --- | --- |
| `CONFIG_DEVTMPFS` | `n` | `y` | `y` |
| `CONFIG_IPC_NS` | absent | `y` | `y` |
| `CONFIG_PID_NS` | `n` | `y` | `y` |
| `CONFIG_SQUASHFS` | `n` | `y` | `y` |
| `CONFIG_SYSVIPC` | `n` | `y` | `y` |
| `CONFIG_USER_NS` | `n` | `y` | `y` |
| `CONFIG_UTS_NS` | `y` | `y` | `y` |
| `CONFIG_VT` | `n` | `y` | `y` |

- Requested: **8**
- Matched compiled `.config`: **8**
- Unmet: **0**
- `CONFIG_MODULE_SIG_PROTECT` remained `y`; `CONFIG_MODULE_SIG_FORCE` remained `n`.
- No phone commands, flashing, or boot image distribution were performed.

## Limitations

A successful Kconfig experiment and Google kernel compilation do **not** prove:
- The modified kernel can boot on the user's Pixel 8.
- ABI/KMI compatibility with the factory vendor modules.
- Compatibility of the Android 14 Halium GSI with Android 17 vendor services.
- Correct split-boot / init_boot / vendor_boot / vendor_kernel_boot image layout.
- Functioning Droidian userspace, graphical session, modem, wireless, camera or power management.

**Phase 5 target:** source-check Droidian/UBports Halium initramfs packaging and kernel ABI expectations, pin exact compatible Android vendor build sources, and attempt a build-only rootfs or adaptation package when justified. Avoid writing images or changing the device.

**UNVERIFIED — BUILD ONLY — DO NOT FLASH.**
