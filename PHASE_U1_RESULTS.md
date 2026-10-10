# Phase U1 results — native Ubuntu arm64 foundation for Pixel 8

**SUCCESS — CI rootfs built, not bootable, no phone actions.**

- Date: 2026-10-10
- [GitHub Actions run #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38033533558)
- [Artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38033533558/artifacts/11662413495): `shiba-ubuntu-u1-bootstrap-2`
- Artifact ZIP size: **28,494,050 bytes**
- Artifact expiry: **2026-10-17 07:14 UTC** (about 16:14 JST)
- Full upload artifact ZIP SHA256 (CI upload record): `81b38655374dd32b1fd4956800f8cbf7094f3f89ccfe8c9afea6879bc931ddf6`
- Rootfs TAR.XZ SHA256 (verified in CI): `ff19b6c8698872f361f75e62a4b71bf979321dcbc59b70d0199721c592c315a1`

## Verified
1. Official Ubuntu 26.04 (Resolute) `InRelease` repository metadata verified by `gpgv` against installed Ubuntu archive keyring.
2. Metadata advertised `arm64` support and `Codename: resolute`.
3. `mmdebstrap --architectures=arm64 --variant=minbase --components=main` completed using `https://archive.ubuntu.com/ubuntu`.
4. ARM64 execution happened in a disposable GitHub Actions runner using QEMU user-mode binfmt emulation.
5. `chroot dpkg --print-architecture` returned `arm64`.
6. `/etc/os-release` contained `VERSION_CODENAME=resolute`.
7. Package inventory, filesystem tarball, SHA256SUMS, and full bootstrap logs were produced.
8. `sha256sum -c` reported `ubuntu-26.04-resolute-arm64-minbase-UNVERIFIED.tar.xz: OK`.
9. GitHub Actions artifact was uploaded successfully. The actual compressed tarball was about 28 MiB; the enclosing uploaded artifact is about 28.5 MB.

## Boundaries
- **This is an authentic Ubuntu ARM64 minimal root filesystem, not a fully bootable Pixel 8 OS or desktop.**
- No kernel, working initramfs, GPU/Wayland desktop, USB-C monitor output, Wi-Fi, sound, touchscreen integration, vendor compatibility, or physical hardware test.
- No ADB/fastboot, no bootloader commands, and no image flashing or device operations.
- CI reported non-fatal runner tool warnings (binfmt already enabled, Node.js 20 depreciation); the job and bootstrap completed successfully.
- It is only reproducible against moving repositories at the *package list* level until exact package revisions/snapshots are pinned.

## Next research phase
- **U2**: Research-only static comparison between Pixel 8 Pro (`husky`) Tensor Linux boot artifacts and Pixel 8 (`shiba`) existing Google kernel/source build.
- Inspect kernel release, module vermagic / KMI constraints, DTBO names/compatibles, and hardware-specific ramdisk settings where available.
- Never treat shared SoC or a common custom recovery as proof of interchangeable boot images.

**BUILD ONLY • DO NOT FLASH • NOT BOOTABLE**
