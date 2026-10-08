# Phase 2 results — Droidian/Halium readiness

## RESULT: SUCCESS

- Date: 2026-10-08
- [GitHub Actions run #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37724909814)
- Mode: `config-build`
- Job conclusion: **success**
- Google shusky build step: **success**
- Droidian/Halium comparison step: **success**
- Artifact: `halium-readiness-config-build-2` (expires October 15, 2026 UTC)

### Configuration audit result

| Category | Count |
|---|---:|
| Exact matches | 15 |
| Differences | 44 |
| Unknown | 0 |

The comparison checks the upstream Droidian `halium.config`,
`droidian.config` and `container.config` fragments (59 total options)
against Google's **compiled** shusky `.config`.

### Important differences observed

| Option | Droidian upstream | Google shusky | Notes |
|---|---|---|---|
| `CONFIG_PID_NS` | `y` | `n` | Halium process namespace requirement |
| `CONFIG_USER_NS` | `y` | `n` | Namespace support |
| `CONFIG_SYSVIPC` | `y` | `n` | IPC compatibility |
| `CONFIG_DEVTMPFS` | `y` | `n` | Device node management |
| `CONFIG_VT` | `y` | `n` | Virtual terminal support |
| `CONFIG_SQUASHFS` | `y` | `n` | Root filesystem packaging requirement |
| `CONFIG_INITRAMFS_SOURCE` | Embedded Droidian archive | Empty | Boot/initramfs packaging design required |
| `CONFIG_BT` | `y` | `m` | Compiled module ≠ missing feature |

**Do not interpret 44 differences as 44 required patches.**
Some are optional container features; others are no longer present in modern
kernel versions. A `y` versus `m` difference can be valid depending on
when modules can load. Settings affecting verified boot, module signing, or
SELinux should **not** be disabled as a shortcut.

### Version compatibility note

- Google Pixel 8 factory reference: `CP3A.260905.009`, Linux `6.1.162-android14-11`.
- Droidian generic 6.1-android14 kernel package reports version `6.1.174`.
- The Google kernel source branch used for this CI is
  `android-gs-shusky-6.1-android16` and is **not proven** to match the supplied factory image.

Successful compilation does not demonstrate boot compatibility, and there is
no confirmed finished Pixel 8 Droidian port yet.

## Proposed Phase 3 (still BUILD ONLY)

1. Triage the 44 differences as required/optional/legacy or module-vs-built-in.
2. Determine which changes are possible while maintaining the Google GKI
   and Pixel vendor module ABI and security requirements.
3. Check Droidian Android 14 userspace compatibility with Android 17 vendor.
4. Produce a candidate configuration/patch *report* with no flashing or device operations.
5. Only later investigate rootfs and Halium packaging.

**BUILD ONLY — NOT BOOT-VALIDATED — DO NOT FLASH**
