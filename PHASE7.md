# Phase 7 — shiba adaptation packaging experiment

**Status: workflow authored; CI run NOT YET VERIFIED. BUILD ONLY.**

## Purpose

Phases 4–5 produced evidence that:
- Google's shusky source-GKI kernel build accepted eight experimental
  Halium-related Kconfig settings ([Phase 4 run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37728429488)).
- A real Debian trixie arm64 minbase filesystem was constructed and
  successfully tested with QEMU ([Phase 5 run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37760550966)).

Phase 6 established that the current official generic Droidian image list
does not include Pixel 8 shiba, and building a new official Droidian
userspace was interrupted by the upstream signed APT server outage.

The [official Droidian community adaptation template](https://github.com/droidian-releng/droidian-build-tools/blob/master/bin/src/build-tools/adaptation.sh)
normally contains **device-specific configurations** plus a package depending
on the appropriate `adaptation-hybris-apiN` flavor. The correct
Android 17 vendor/Halium package for Pixel 8 remains **unverified**. We
must NOT fake a functional adaptation package or choose an API arbitrarily.

## Real CI deliverable (build-only)

[**Run Phase 7 Actions**](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase7-shiba-adaptation-research.yml)

This workflow:

1. Creates a **real Debian arm64 .deb** named
   `adaptation-google-shiba-research_0.1.0_arm64.deb`.
2. Packs just two inert files:
   - `/usr/share/droidian-porting/shiba/port-status.json`
   - `/usr/share/doc/adaptation-google-shiba-research/README`
3. Validates the package architecture, device identity, evidence references,
   exact file allowlist, absence of maintainer scripts, and every
   compatibility gate being **false**.
4. Downloads the previous Phase 5 Debian arm64 minbase Artifact, checks its
   recorded SHA-256, and extracts it into a **temporary GitHub runner directory**.
5. Installs the .deb inside that disposable ARM64 chroot with `dpkg --install`
   using GitHub's QEMU/binfmt setup and checks its installed status and files.
6. Uploads the .deb and CI test report. It does **not** modify Android,
   create bootable images, download vendor binaries, access the Pixel 8,
   or call ADB/fastboot.

This is a genuine .deb and a genuine compatibility *packaging test*, but
**the package is NOT a working Droidian device adaptation**. It is only
inert research metadata; do not install it on your phone.

The Phase 5 base Artifact must still be available when this workflow runs:
the published expiration is **October 15, 2026 at 10:04 UTC**.
If the artifact has expired, Phase 5 must be rebuilt or the workflow
updated to reuse a new verified rootfs artifact.

## Major remaining dependencies

- Verify the source-built kernel's KMI/ABI against the actual Google
  firmware/vendor modules on Pixel 8; keep module and boot protections intact.
- Determine whether an Android 14 Halium/GSI base can work with
  the user's Android 17 vendor, or whether a newer Android userspace is needed.
- Build **actual** Droidian ARM64 userspace (including Phosh, libhybris and
  an Android LXC container) with authenticated upstream packages.
- Implement actual shiba-specific device adaptations, initialization,
  logging and split-boot composition.
- Establish firmware and recovery prerequisites before any real boot tests.

**Never flash or install any Phase 7 output on the physical Pixel 8.**
