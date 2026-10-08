# Phase 5 — Building the Linux filesystem foundation

**EXPERIMENTAL / BUILD ONLY / NO ADB / NO FASTBOOT / NO FLASH**

## Current status

- Phase 4: [8/8 targeted Halium kernel settings compiled successfully](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37728429488).
- Phase 5 is **not yet validated**. Its GitHub Actions workflow has been written but still requires a real CI run.
- Next problem: a Droidian userspace/rootfs + Halium Android container compatible with Pixel 8 shiba.

## Official-source checks

The [Droidian rootfs porting guide](https://github.com/droidian/porting-guide/blob/master/rootfs-creation.md)
describes a device-specific **adaptation** Debian package and the
Droidian rootfs builder. The
[images registry](https://github.com/droidian-images/droidian/blob/main/devices.yml)
is not evidence that an Android 17 vendor image is supported.
[Droidian's Android 14 GSI package](https://github.com/droidian/android-system-gsi-34-bin)
exists, but compatibility with this phone's current vendor/firmware
has **not** been established.

The automated preflight reads public upstream repositories, pins their
Git revisions and records the supported API list and GSI package metadata.

## Run the Phase 5 workflow

[**Droidian Phase 5 — ARM64 rootfs foundation**](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase5-rootfs.yml)

On GitHub Actions select **Run workflow** and:

- `bootstrap` (default) builds a real minimal **Debian trixie arm64**
  filesystem using `mmdebstrap` on a GitHub-hosted runner; validates
  the target architecture using `dpkg --print-architecture`; and stores
  a reproducible package list and SHA-256.
- `preflight` only checks upstream Droidian inputs and creates
  `PHASE5_READINESS.md`, without downloading Debian packages.

The `bootstrap` output contains
`debian-arm64-minbase-TRIXIE-NOT-DROIDIAN.tar.xz`
when the run succeeds. It has **no functional display, Android compatibility
layer, Pixel 8 firmware, initramfs, device-specific packages or bootloader
integration**. It is a normal Debian arm64 base directory tree, and nothing
in it should be flashed, booted or installed to a phone.

No Android vendor blobs or rootfs credentials are built into the archive;
it is intended only for build experiments.

## Why we don't call it Droidian yet

Droidian's own template includes packages with names such as
`adaptation-hybris-api<API>` and `android-system-gsi-<API>`.
The presence of an `android-system-gsi-34` source repo does not prove
an Android 17 Pixel 8 shiba-compatible Halium and vendor stack exists.
A device adaptation package plus exact vendor/API/ABI verification is
still required. The kernel's GKI ABI compatibility also remains unverified.

## Next phase (not implemented here)

1. Identify compatible Droidian/Android vendor API and GSI or build it.
2. Build a shiba-specific Debian adaptation package with actual config
   and dependencies rather than a placeholder.
3. Integrate Halium and a Droidian userspace with Phosh.
4. Validate rootfs and split-boot composition without touching a device.
5. Only discuss any real-device test after exact compatibility,
   safe recovery and backup requirements are established.

**This is not a flashable ROM and is NOT proven safe to boot.**
