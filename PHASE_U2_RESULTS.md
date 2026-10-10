# Phase U2 RESULTS — Pixel 8 Pro / Pixel 8 static hardware comparison

**SUCCESS: STATIC COMPARISON COMPLETED; NO PHONE ACCESS; NO FLASHING.**

- Date: 2026-10-10
- CI: [Ubuntu U2 Run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38034504680) — **success**
- Artifact: [shiba-ubuntu-u2-static-report-1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38034504680/artifacts/11663405021)
- Artifact size: **34,624 bytes**, expiry **2026-11-09 07:28 UTC**
- Contains **U2_REPORT.md and U2_METADATA.json only**, not images.
- CI source code: [phase_u2_static_compare.py](scripts/phase_u2_static_compare.py)
- Husky source: official Tensor Linux V1.0 release, SHA256
  `3ef1f4e6675ffef522d939e5bb7dd9fdb06c6da60cde784b4ec7fe14e99dff9f`.
  The user-supplied `husky-boot-images.zip` was independently CRC-checked
  and had **exactly this SHA256**.

## A. Reproducible CI comparison: upstream husky vs earlier experimental Google shusky build

| Property | Husky Tensor Linux V1.0 | Experimental Google shusky CI |
| --- | --- | --- |
| Embedded boot kernel version | 6.1.124-android14-11 | 6.1.124-android14-11 |
| DTBO entries | 19 | 19 |
| Byte-identical DTBO entry hashes | **0** | **0** |
| Vendor-kernel-boot modules decoded | **211** | **211** |
| Shared full module paths | **211** | **211** |
| Shared modules with unequal vermagic | **211** | **211** |

Note that matching major/minor kernel numbers **does not** establish kernel
module ABI compatibility. The earlier Google shusky build used an
**android16 manifest branch**; it has *not* been shown to match the user's
Android 17 factory build.

## B. Supplemental read-only examination of earlier user-provided image files

**Not the inputs used in GitHub CI**; examined locally and never uploaded
to GitHub. Source firmware/provenance among separately uploaded image files
is **unverified**.

| Property | Husky V1.0 release | User-uploaded Pixel 8 image |
| --- | --- | --- |
| Boot kernel release | `6.1.124-android14-11-g8d713f9e8e7b-ab13202960` | `6.1.162-android14-11-g2ec90535fa34-ab15810641` |
| DTBO table count | 19 | 19 |
| DTBO entry ID/revision tuples | same set | same set |
| Bit-identical DTBO entries | 0 | 0 |
| Decoded vendor_kernel_boot .ko entries | 211 | 210 |
| Shared module **basenames** | 208 | 208 |
| Same binary hash among shared modules | 0 | 0 |
| Identical reported `vermagic` among shared modules | 0 | 0 |

Normalized basenames were used for B because the two ramdisks store modules
in **different paths** (husky has kernel-release/source paths; shiba has
flat `lib/modules` paths). Raw paths would incorrectly show zero overlap.

**Husky-only module basenames in these two ramdisks:**
`iovad-best-fit-algo.ko`, `mali_kbase.ko`, `mali_pixel.ko`.

**Shiba-only module basenames in these two ramdisks:**
`fips140.ko`, `iovad-vendor-hooks.ko`.

**Very important:** A module absent from *vendor_kernel_boot* may exist in
another partition or have a different name; the list above does **not**
mean the Pixel 8 has no Mali GPU driver.

Sample `vermagic` from the user-uploaded Pixel 8 vendor-kernel-boot module
(`panel-google-bigsurf.ko`):
`6.1.162-android14-11-g622c1358585b-ab15912884 SMP preempt mod_unload modversions aarch64`.

This differs in full build suffix from the separately uploaded Pixel 8
`boot(3).img` kernel (`g2ec90535fa34-ab15810641`), **even though both
show 6.1.162**. Without verifying image origin, do **not** assume the
separately uploaded files are an ABI-matched factory pair.

## Interpretation

1. Tensor G3 devices share a sizeable vendor-module family; code concepts
   and common drivers may be useful for an Ubuntu port.
2. The **19 DTBO table IDs/revisions match**, but **none of the payloads are
   byte-identical**. Some differences may be version/build differences as well
   as hardware-specific configuration; classify at FDT node level later.
3. The released husky kernel is substantially older than the uploaded
   Android17 Pixel 8 boot kernel and should **not** be treated as a drop-in
   boot component.
4. `vermagic` mismatch is a concrete **compatibility warning**, not by
   itself a definitive judgment on all Linux kernel module ABI subtleties.
5. Touch display, GPU acceleration, external monitor, power management,
   Wi-Fi, radio, sound and suspend are **unverified on shiba**.

## Next: U3

- Source-level audit of Google `shusky` panel/display/USB-C and input
  differences; determine which pieces can be reused from Tensor Linux.
- Native Ubuntu 26.04 touch-friendly Wayland session and an external-display
  desktop **in CI only**; document compositor/GPU prerequisites.
- Compare correct Android17 Pixel 8 vendor interfaces and exact matching
  kernel-module release/KMI without using the device.
- Keep kernel building, analysis and Ubuntu rootfs artifacts separate.

**BUILD ONLY • NOT BOOTABLE • NOT A ROM • NO ADB/FASTBOOT/DEVICE OPERATIONS.**
