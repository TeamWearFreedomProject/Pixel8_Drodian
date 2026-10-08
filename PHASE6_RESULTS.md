# Phase 6 status — official Droidian APT server unavailable

**FAILURE (UPSTREAM NETWORK): The signed Droidian rootfs bootstrap did not start.**

- Run: [Phase 6 #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37763151840)
- Date: October 8, 2026
- Duration: 30 seconds
- Official sources and dependency audit completed successfully.
- Attempt to retrieve `https://releases.droidian.org/snapshots/current/dists/rolling/InRelease` failed:
  `Could not connect to releases.droidian.org:443 ... Connection refused`.
- The installer never obtained repository package lists; there is **no Droidian rootfs artifact** from this run.

## Recovery options

The project now has a corrected [Phase 6 workflow](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase6-droidian-userspace.yml):

- `base`: check the official signed snapshot endpoint first, then attempt the real upstream-signed Droidian rootfs build **only if reachable**.
- `release-inventory`: inspect **metadata only** for the official [Droidian GitHub nightly](https://github.com/droidian-images/droidian/releases/tag/nightly); generate `PHASE6_OFFICIAL_NIGHTLY.md` without downloading ~1.5 GB images or claiming boot compatibility.
- `audit`: inspect only the upstream source recipes and Android API inventory.

The October 7, 2026 upstream GitHub release contains generic arm64
images for Android API 28/29/30/32/33 but **no shiba** image and no API 34 image.
These images must **not** be flashed on a Pixel 8.

There may be other official package mirrors, but no replacement is configured
unless repository provenance, package availability and signature checks are
verified. Do not skip APT signing checks, mark an untrusted mirror
`trusted=yes`, or substitute another Android API GSI as a shiba build.

The Phase 4 Halium-oriented shusky kernel experiment and Phase 5 Debian arm64
bootstrap remain successful independent steps. The fully integrated Droidian
userspace + Halium + Pixel 8 adaptation remains **unbuilt and untested**.

**BUILD ONLY / NO DEVICE ACCESS / DO NOT FLASH.**
