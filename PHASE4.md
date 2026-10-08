# Phase 4 — Google shusky kernel adaptation experiment

**BUILD ONLY — EXPERIMENTAL — DO NOT FLASH**

Goal: Determine whether a Pixel 8 **source-built GKI** plus Google's shusky
vendor kernel modules can be compiled with a minimal subset of Droidian's
Halium requirements. This is an experiment, **not** a phone ROM yet.

## Workflow

[Run Phase 4 on GitHub Actions](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase4-halium-kernel.yml)

Select **Run workflow** (no inputs). The workflow:

1. Reuses Phase 2's real compiled baseline kernel `.config`.
2. Fetches the official `android-gs-shusky-6.1-android16` kernel sources.
3. Adds a local, experimental `--defconfig_fragment` targeting
   a Google `--config=pixel_debug_common` source-GKI build.
4. Tries to build `./build_shusky.sh` with `parameters="--kernel_package=@//aosp"`.
5. Compares the resulting `.config` with the baseline, failing on unfulfilled
   requested settings and preserving diagnostics.

The deliberately minimal requested configuration is:

```text
CONFIG_DEVTMPFS=y
CONFIG_VT=y
CONFIG_SYSVIPC=y
CONFIG_PID_NS=y
CONFIG_IPC_NS=y
CONFIG_UTS_NS=y
CONFIG_USER_NS=y
CONFIG_SQUASHFS=y
```

**Caveat:** The Android 6.1 Kconfig dependency graph may not permit all these
settings on the selected GKI branch without additional build changes.
In particular, `CONFIG_USER_NS` has security implications and requires
an explicit review. No SELinux, signature enforcement or boot verification
settings are disabled in the fragment.

Google's source-built Kleaf technique is described by
[Andrey Konovalov's Pixel 8 kernel investigation](https://xairy.io/articles/pixel-kgdb).
That work is a reference; these experiments are not a validated downstream port.

## Expected results

If successful, see `PHASE4_CONFIG_REPORT.md` and the runner's Kconfig logs
under the action artifact. **No boot images are uploaded**: none are yet
validated for the actual Android 17 shiba firmware.

If the build fails, inspect `sync.log`, `build.log` and the build step logs
and fix the root cause. Do not confuse green artifacts upload with successful
compilation or boot compatibility.

## Known blockers before actual testing

- An exact source match for the running Pixel 8 CP3A/CP2A image is not proven.
- Full GKI KMI/module compatibility and SELinux/mount layout remain uncertain.
- The Droidian Android 14 Halium GSI must be assessed against Android 17 vendor.
- A real shiba-specific Droidian rootfs/initramfs/device adaptation is missing.
- Real-device boot validation cannot be done from GitHub Actions; it must only
  be considered after careful review and backups.

**Never flash this experimental kernel or use it as a boot-ready image.**
