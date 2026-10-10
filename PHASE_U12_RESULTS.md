# Phase U12 RESULTS — exact user-installed Evolution X Pixel 8 release identity

**SUCCESS: official OTA metadata matched the user-confirmed Pixel 8 ROM precisely.**
**THIS IS A METADATA MATCH ONLY; ZIP PAYLOAD AND DEVICE KERNEL/VENDOR ABI UNVERIFIED.**

## Successful GitHub Actions result

- [U12 GitHub Actions run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38062319876) completed **SUCCESS**.
- [U12 report, JSON and CDN HEAD response artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38062319876/artifacts/11673477278): `shiba-u12-exact-evolutionx-ota-metadata-1`, 3,485 bytes, expires **2026-11-09 15:07 UTC**.
- [Pinned official OTA index](https://github.com/Evolution-X/OTA/blob/bka/builds/shiba.json), commit `b400c98274f840b503e142782957cd37d699f0bb`.
- [U12 exact-release verifier](scripts/u12_exact_ota_pin.py) and [workflow](.github/workflows/phase-u12-exact-ota.yml).

## Identified, authentic official OTA record

| Field | Official metadata |
| --- | --- |
| Device | Google Pixel 8, `shiba` |
| Android | 16.0 |
| Build date in filename | 2026-09-15 |
| Evolution X version | 11.11 |
| Variant | `Official`, GApps build, `user` build type |
| Full filename | `EvolutionX-16.0-20260915-shiba-11.11-Official.zip` |
| Expected download size | **3,033,648,565 bytes** (~3.03 GB) |
| Official expected SHA-256 | `41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0` |
| Official expected MD5 | `7ce0ffbbbe391a376483330b40db168a` |

Official ZIP link stored in the source index:
https://cdn.evolution-x.org/shiba/16/EvolutionX-16.0-20260915-shiba-11.11-Official.zip/download

The official OTA config also lists these initial installation image **names**:
`boot`, `dtbo`, `vendor_kernel_boot`, `vendor_boot`.

The filename, release SHA/size, device identity, version, build type,
the four image names, and the fact that the Pixel 8 Pro `husky` metadata
points at a different file were all checked in U12.

## Exactly what U12 does NOT verify

1. **The 3.03 GB archive has not been downloaded or locally hashed yet**. The SHA-256 above is from the official OTA index, not independently computed from ZIP bytes.
2. The HTTP `HEAD` request returned response headers, but the archive **content was not fetched**, and this check alone does not validate availability or integrity.
3. Neither `payload.bin` nor actual official `boot.img`, `dtbo.img`, `vendor_boot.img` or `vendor_kernel_boot.img` was extracted or compared by bytes.
4. The U7 experimental boot image was SHA-checked as **a separate old research artifact**, not assumed compatible with this Evolution X ROM.
5. The real phone's currently installed slot, boot/vendor module KMI, module `vermagic`, graphics/touch driver compatibility, rootfs physical mapping and a recovery path are still **not established**.
6. No flashable Pixel 8 Ubuntu firmware was generated, no phone connected, and no ADB/fastboot/partition writes occurred.

## Next binary integration checkpoint

Acquire exactly this official 3.03 GB ROM ZIP using its published URL, verify **full ZIP SHA256**, and then independently parse the **matching shiba** boot/vendor/DTBO payload metadata and hashes on an offline runner. Extracted potentially flashable images must remain temporary and **not be deployed or distributed as a Pixel 8 Ubuntu ROM**. Comparing with the previously created U7 kernel and U11 manifest is then meaningful, but still cannot by itself prove a complete native Linux boot.

**U12 PASSED OFFICIAL METADATA MATCH; PIXEL 8 UBUNTU FLASH-READINESS FALSE.**
