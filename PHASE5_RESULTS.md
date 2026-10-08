# Phase 5 results — arm64 Debian rootfs build

**SUCCESS: Debian trixie arm64 minbase rootfs created and archived.**

- Date: 2026-10-08
- [GitHub Actions run #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37760550966)
- Workflow: `Droidian Phase 5 - ARM64 rootfs foundation (BUILD ONLY)`
- Duration: approximately 4 min 15 sec
- GitHub artifact: `shiba-phase5-bootstrap-3` (30,854,995 bytes ZIP)
- [Artifact page](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37760550966/artifacts/11541983198)
- GitHub artifact expiry: **2026-10-15 10:04 UTC**

## Actual results

- `mmdebstrap` ran successfully using the Debian trixie repository.
- Cross-architecture execution used QEMU user-mode binfmt emulation.
- `chroot dpkg --print-architecture` returned `arm64`.
- `/etc/os-release` identified Debian trixie.
- `debian-arm64-minbase-TRIXIE-NOT-DROIDIAN.tar.xz` was created (~30 MiB).
- Tarball SHA256: `f1038f5fff7872dd82239388cdae3f9983186bc7e5e0b97331167417214d935d`.
- Generated package manifest, checksums and build logs were uploaded.

## Upstream Droidian findings

- Main `droidian-images/droidian` generic rootfs API list at audited revision:
  `28, 29, 30, 32, 33`; **does not list API 34**.
- The separate `droidian/android-system-gsi-34-bin` source does define
  `android-system-gsi-34`, but this is not a verified Pixel 8 adaptation.
- No compatible `adaptation-hybris-api34` or Android 17 vendor interface was proven.
- No functional shiba-specific adaptation package has been built yet.

## Interpretation and next steps

This is a **genuine, minimal Debian arm64 filesystem**, not Droidian, not a
kernel image, not a bootable ROM. Phase 4 separately compiled a Google shusky
kernel with 8/8 requested Halium config settings, but vendor KMI/ABI and
boot compatibility were not tested.

Before any boot-image assembly or phone test: identify a matching Halium
Android container and vendor API, implement device adaptation, analyze Pixel
split-boot images and verify exact kernel/vendor compatibility.

**BUILD ONLY — NOT SAFE TO FLASH — NO DEVICE OPERATIONS.**
