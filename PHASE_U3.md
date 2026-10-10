# Ubuntu Phase U3 — Dual touch/desktop ARM64 userspace

**BUILD ONLY • NOT BOOTABLE • DO NOT FLASH**

## Goal

Build a single authentic Ubuntu 26.04 (Resolute) **arm64** filesystem
containing two **candidate** Wayland GUI environments:

| Context | Candidate software | Status in U3 |
| --- | --- | --- |
| Smartphone's own screen | Phosh shell + Phoc compositor + Stevia on-screen keyboard | Install + metadata checks in CI |
| PC-style desktop | Labwc compositor + Waybar panel + Foot terminal | Install + metadata checks in CI |
| Multiple displays | Kanshi output profile utility | Installed for later investigation; **not** configured for the Pixel 8 |
| Hotplug switching | Detect monitor connection, choose desktop while touch stays usable | **NOT implemented or tested** |

The goal is **native Ubuntu**, not a chroot running under Android or desktop
streamed over VNC. U3 only builds the Ubuntu userspace without hardware support.

## Updated phone context

As of 2026-10-10, the owner says the **actual Pixel 8 (`shiba`) now runs
Android 16 Evolution X**, not the previous Android 17 factory build.

The archived Android 17 `vendor.img`, `CP3A.260905.009`, factory kernel
`6.1.162-android14-11`, and earlier `shusky` CI kernels are **research
references, not proof of matching the current Evolution X firmware**.
The exact current ROM kernel build, vendor interfaces, and module KMI are
unknown. No ADB, fastboot, or device actions are part of U3.

## CI workflow and inputs

Workflow: [Pixel 8 Ubuntu U3 - Touch and desktop ARM64 GUI](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase-u3-ubuntu-gui.yml)

- Reuses the verified [Ubuntu U1 arm64 rootfs](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38033533558) — checksum pinned:
  `ff19b6c8698872f361f75e62a4b71bf979321dcbc59b70d0199721c592c315a1`.
- Uses official Ubuntu 26.04 arm64 `main universe` package archives.
- Runs ARM64 package tools via QEMU user-mode binfmt in a disposable GitHub runner.
- `preflight` mode: checks repository availability for GUI packages.
- `compose` mode: installs the chosen packages with `--no-install-recommends`,
  validates `dpkg` status, ARM64 ELF headers and generates a **manual**
  Labwc session entry and descriptive policy JSON.
- Produces an Ubuntu userspace `.tar.xz` and SHA-256 digest. This tarball is
  **not a Pixel firmware image, installer, or bootable OS**.
- Saves reports separately from the userspace artifact. Reports: 30-day retention;
  GUI rootfs: 7-day retention (GitHub Actions storage dependent).
- An initial `compose` build is requested via GitHub `push` of this plan.
  Manual re-runs offer both modes.

### Success criteria

GitHub Actions must report success with:
1. Valid earlier Ubuntu U1 archive SHA-256.
2. Both mobile and desktop packages actually installed in arm64 rootfs.
3. Validator records ARM64 executable ELF architecture.
4. Actual GUI-userspace tarball checksum `OK` and artifacts uploaded.

If CI fails, it is **not** a completed U3 stage; fix the actual log error, not
a speculative boot/ROM problem.

### Absolutely NOT proven yet

- Pixel 8 bootability, GUI rendering on real GPU, working display/touch,
  touchscreen gestures, automatic monitor hotplug, USB-C video output, audio,
  battery management, suspend/resume, telephony, camera, sensors, Wi-Fi,
  secure boot and driver compatibility.
- `Phosh` and `Labwc` installed together does not automatically switch
  sessions when an external monitor is plugged in.
- A desktop UI package does not create or validate Android KMI-compatible
  hardware support.

## Next hardware research — U4

1. Pin the *current* Evolution X Android 16 kernel/vendor provenance **without
   device operations** when ROM release sources are available.
2. Audit `huskyfe`, `glproxy`, and `vkproxy` assumptions: Mali userspace
   libraries, display stack and Wayland protocol requirements.
3. Work out external monitor support and session handoff architecture from
   Pixel 8 (`shiba`) kernel/DT and USB-C display interfaces; mark anything
   not verifiable without hardware as unknown.

No ROM installation, no actual phone operations and no rootfs-to-boot-image
assembly are authorized at this stage.

References:
- https://packages.ubuntu.com/resolute/arm64/phosh
- https://packages.ubuntu.com/resolute/labwc
- https://packages.ubuntu.com/resolute/phosh-osk-stevia
- https://packages.ubuntu.com/resolute/kanshi

## CI debug note (2026-10-10)

The first automatic U3 run [38041952779](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38041952779) correctly confirmed the pinned U1 tarball hash but failed on the redundant `SHA256SUMS` invocation: U1's manifest retained its original `output/` directory prefix, which is absent after artifact download. Fixed in the U3 workflow by comparing the manifest digest directly after verifying the tarball. The failure did **not** indicate a corrupt Ubuntu base or a broken GUI. This plan update requests a second automatic CI run.
