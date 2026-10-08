# Phase 6 — Build an authentic Droidian ARM64 base (BUILD ONLY)

**Experimental. Not verified, not an installable ROM, no flashing.**

## Why this phase differs from the Phase 5 base

Phase 5 produced Debian 13 (trixie) ARM64 minbase. That was useful,
but Droidian's official rootfs recipes bootstrap Droidian's own
signed "rolling" repository and install the `droidian-base` package.
Simply unpacking Debian minbase does **not** produce Droidian.

Phase 6 experiments with the official Droidian repository and source
recipes without using the Pixel 8 itself.

## GitHub Actions

[Run Phase 6](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/workflows/phase6-droidian-userspace.yml).

Use **Run workflow**, keeping the default `mode=base`.

- `audit`: Fetch the official upstream sources and document what exists,
  including known missing Android 17 and shiba support.
- `base`: Additionally bootstrap `rolling` with `mmdebstrap` using the
  official Droidian GPG key. Install `droidian-apt-config`,
  `droidian-archive-keyring`,
  `mobian-droidian-archive-keyring` and `droidian-base`
  in a temporary ARM64 filesystem. Package that **non-bootable**
  directory tree as `droidian-base-arm64-NOT-BOOTABLE-NOT-FLASHABLE.tar.xz`
  if and only if all steps succeed.

The workflow does **not** download any boot image, create an Android
GSI, install a recovery image, provide a firmware package, or access
the user's Pixel 8. Service startup and flash-bootimage are explicitly
disabled inside the ephemeral CI filesystem.

If the upstream package repository cannot be accessed or a dependency
is unavailable, the build must fail (rather than silently falling
back to generic Debian or accepting unsigned packages).

## Official references

- [Droidian rootfs recipe](https://github.com/droidian-releng/rootfs-templates/blob/droidian/recipes/droidian_base.yaml)
- [Droidian Phosh layer](https://github.com/droidian-releng/rootfs-templates/blob/droidian/droidian_phosh.yaml)
- [Official images configuration](https://github.com/droidian-images/droidian/blob/main/devices.yml)
- [Droidian porting guide](https://github.com/droidian/porting-guide/blob/master/rootfs-creation.md)

## Remaining blockers

1. Droidian Phosh UI and its mobile service packages are **not yet**
   installed by Phase 6; that requires its own validated build.
2. The official generic device matrix currently lists API 28, 29, 30,
   32 and 33; API 34 is not shown there at the audited revision.
   The separate GSI 34 source does not prove a working shiba port.
3. Android 17 Pixel 8 (shiba) vendor/Halium compatibility is unverified.
4. Phase 4's kernel config was compiled, but its KMI/ABI compatibility
   with the current firmware was not tested.
5. No device adaptation, initramfs, display/graphics drivers or
   split-boot images have been packaged.

**BUILD ONLY — DO NOT FLASH THE ROOTFS ARCHIVE.**
