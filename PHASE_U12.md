# Phase U12 — exact Evolution X Android 16 shiba installed build identity

**NO PHONE / NO FLASH / NO 3 GB ZIP DOWNLOAD YET**

## Explicit user-confirmed current ROM

`EvolutionX-16.0-20260915-shiba-11.11-Official.zip`

The user confirmed the entire basename including `16.0`, `20260915`,
`shiba`, `11.11` and `Official`. This is the **Google Apps / GApps build**,
not `Vanilla`, nor the Pixel 8 Pro `husky` build.

## Exact official OTA index

Official GitHub: https://github.com/Evolution-X/OTA/blob/bka/builds/shiba.json

The **bka** branch commit verified by GitHub:
`b400c98274f840b503e142782957cd37d699f0bb`

Official shiba OTA index data:

- ROM filename: `EvolutionX-16.0-20260915-shiba-11.11-Official.zip`
- Build type: `user`
- Version: `11.11`
- File size: **3,033,648,565 bytes** (~3.03 GB decimal)
- Official ZIP SHA256:
  `41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0`
- Official ZIP MD5:
  `7ce0ffbbbe391a376483330b40db168a`
- Release record download URL:
  https://cdn.evolution-x.org/shiba/16/EvolutionX-16.0-20260915-shiba-11.11-Official.zip/download
- Official initial installation image **names**:
  `boot`, `dtbo`, `vendor_kernel_boot`, `vendor_boot`.

The above checksum comes from the **official index**, not from having
personally downloaded or hashed all 3 GB of ZIP content. The public index
does **not** establish the binary kernel KMI/ABI, phone installed slot
contents, binary module SHA256, boot/init_boot/DTBO binary hashes or
Ubuntu bootability. Official initial installation *names* are not
per-image SHA256 values.

## Automated U12 evidence check

- [Workflow](.github/workflows/phase-u12-exact-ota.yml) checks the exact
  official OTA index at pinned Git SHA.
- [Verifier](scripts/u12_exact_ota_pin.py) validates the exact file name,
  official SHA256, size, Google Pixel 8 identity, user build type and
  expected installation-image names; compares the separate Pixel 8 Pro record
  to prevent substitution.
- It verifies old experimental U7 `boot.img` as **separate research image**.
- It optionally queries HTTP HEAD status of official download URL without
  downloading 3 GB or treating headers as binary verification.
- Outputs only small metadata JSON/Markdown and connectivity info, never
  phone firmware or flashable images.

The next **substantive binary compatibility** milestone requires a real
copy of this exact official OTA ZIP (matched against the published SHA256)
to inspect `boot`, `vendor_kernel_boot`, `vendor_boot`, `dtbo` and
vendor modules. Full OTA archives are much larger than metadata checks;
do not treat a candidate with a similar filename as equivalent, and do not
substitute older Android 17 or `husky` artifacts.

All actions here occur only in GitHub CI.

**STILL NOT A BOOTABLE PIXEL 8 UBUNTU ROM. DO NOT FLASH.**
