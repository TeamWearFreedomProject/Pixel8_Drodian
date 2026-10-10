# Ubuntu Phase U1 — Pixel 8 (shiba) ARM64 rootfs

**BUILD ONLY — UNVERIFIED — NOT BOOTABLE — DO NOT FLASH**

## Goal
Build an authentic Ubuntu 26.04 LTS (Resolute Raccoon) **arm64** minimal root filesystem as a reproducible GitHub Actions artifact. This is a new research track; retain all Droidian workflows/results unchanged.

Target device for **future** research: Google Pixel 8 (`shiba`), Tensor G3 (`zuma`).

Intended eventual interaction modes:
- Phone display: touch-friendly Linux interface.
- External display: full desktop interface and keyboard/mouse.

**Neither interface, GPU, hardware video, USB-C display-out, audio, sensors, Wi-Fi nor touchscreen are implemented in U1.** Device support is not validated.

## Reuse from the earlier Droidian work
- Phase 5: successful `mmdebstrap` arm64 Debian filesystem with QEMU binfmt and `dpkg` verification.
- Phase 4: experimental source-built shusky kernel; no verified device/vendor KMI pairing.
- Phase 8 research: user-observed Pixel 8 vendor Android 17, SDK 37, build CP3A.260905.009. Hardware compatibility remains unverified.
- Tensor Linux Pixel 8 Pro (`husky`) is useful source material but its images are not verified on `shiba`.

## CI recipe
GitHub workflow: `.github/workflows/phase-u1-ubuntu-rootfs.yml`

1. **preflight**: verify Ubuntu repository's Resolute arm64 metadata and that an Ubuntu archive signing keyring is available.
2. **bootstrap**: install `mmdebstrap`, `ubuntu-keyring`, `qemu-user-static`; bootstrap a minimal Ubuntu 26.04 rootfs from the official archive with cryptographic repository signature checking.
3. Validate that the disposable chroot reports architecture `arm64`, codename `resolute` and installed packages.
4. Generate an `.tar.xz` filesystem, SHA-256 checksum, installed package list, build log and status report.
5. Upload artifacts only to GitHub Actions; retention seven days. **No boot.img, initramfs, Android flashing commands, fastboot, adb, or physical-device activity.**

Ubuntu 26.04 serves arm64 on **https://archive.ubuntu.com/ubuntu**, not the old ARM ports-only path.
The package index is moving over time, so the result is not bit-for-bit reproducible unless upstream packages are later pinned/snapshotted; hashes and a package/version inventory preserve traceability.

## Manual run (browser only)
1. Open [repository Actions](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions).
2. Select **Pixel 8 Ubuntu U1 - ARM64 base rootfs (BUILD ONLY)**.
3. Choose `preflight`, then **Run workflow**.
4. If it passes, repeat with `bootstrap`.
5. Download the `shiba-ubuntu-u1-bootstrap-...` artifact from its successful run and retain the checksum.

The workflow is not executed merely by adding this file. A passing GitHub Actions run is the evidence that an Ubuntu rootfs was actually built.

## Later research stages (not part of U1)
- **U2**: static diff of husky vs shiba kernel/DTBO/vendor module KMI, no hardware operations.
- **U3**: GUI candidates (touch UI and desktop), Wayland/compositor, optional glproxy audit and GPU driver ABI.
- **U4**: evaluate boot integration architecture, display, input, power and external monitor feasibility from verified sources. No device work unless expressly reconsidered separately.

### References
- https://discourse.ubuntu.com/t/ubuntu-on-arm-summer-26-update/84872
- https://archive.ubuntu.com/ubuntu/dists/resolute/
- https://manpages.ubuntu.com/manpages/resolute/man1/mmdebstrap.1.html
- https://github.com/Tenser-Linux/Tensor-Linux
