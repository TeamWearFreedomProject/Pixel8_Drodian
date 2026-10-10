# Phase U13 RESULTS — official CDN blocks GitHub Actions; exact offline extraction fallback

**STATUS: BLOCKED by official CDN HTTP 403. NO claim of full OTA ZIP/binary verification.**
**Pixel 8 remains unchanged; NOT READY TO FLASH.**

## Two real CI attempts

1. [U13 attempt #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38063861509) failed BEFORE downloading the ROM while compiling the pinned Go extraction tool: `lzma.h: No such file or directory`. This was fixed by installing `liblzma-dev`.
2. [U13 attempt #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38063978790) successfully checked out and compiled the pinned [payload-dumper-go](https://github.com/ssut/payload-dumper-go) source with Go 1.27.0. **Official Evolution X CDN returned HTTP 403 on five attempts** for the exact ROM's download endpoint. The job therefore stopped BEFORE downloading or hashing the 3.03GB zip, before any `payload.bin` extraction, before any kernel/vendor SHA comparison.

No unverified alternative mirror was substituted. The old SourceForge Evolution X official shiba directory indexes Android 15 from 2025, **not this 2026 Android 16 11.11 shiba ROM**.

These 403 responses are server rejections of the GitHub-hosted runner's request. They do **not** imply that the user's locally downloaded Evolution X file is corrupted or that the user's phone ROM is faulty.

## What is still known from earlier confirmed official OTA metadata (U12)

| Property | Official OTA value, NOT re-verified against downloaded bytes |
| --- | --- |
| Filename | `EvolutionX-16.0-20260915-shiba-11.11-Official.zip` |
| Full ZIP expected bytes | `3033648565` |
| Full ZIP expected SHA256 | `41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0` |
| User-uploaded `payload_properties.txt` FILE_SIZE | `3033640593` |
| User-uploaded `payload_properties.txt` FILE_HASH | `kZO/l+sj+c97aUxtyKJUd/LhIqtTuT063uwfWZJwKQ0=` |
| User-uploaded `payload_properties.txt` METADATA_SIZE | `189195` |
| User-uploaded `payload_properties.txt` METADATA_HASH | `dFOED5c5AxRBN3gV+1TqYyTOcGLKrHiVYp+t8pkklqo=` |

The user uploaded the three small sidecars `payload_properties.txt`, `apex_info.pb` and `care_map.pb`. These files by themselves cannot reveal the exact boot and vendor module binary hashes.

## Available offline Windows alternative (NO GitHub 25MB file upload)

The user already holds the raw `payload.bin` or whole OTA ZIP on a Windows 11 ThinkPad. To avoid sending it to GitHub or ChatGPT:

- [Verified extraction PowerShell helper](scripts/u13_windows_local_extract.ps1) in this repository.
- [Upstream Windows amd64 payload-dumper-go 2.1.0 prebuilt release](https://github.com/ssut/payload-dumper-go/releases/download/2.1.0/payload-dumper-go_2.1.0_windows_amd64.tar.gz), small ~3.5MB download.
- [Upstream published tool checksums](https://github.com/ssut/payload-dumper-go/releases/download/2.1.0/payload-dumper-go_sha256checksums.txt).

The helper verifies the **full official ZIP SHA256** if passed a ZIP, or the **raw payload.bin SHA256 via the user's uploaded `payload_properties.txt`** if passed the BIN, then extracts only:

`boot`, `init_boot`, `dtbo`, `vendor_boot`, `vendor_kernel_boot`, `vendor_dlkm`, `system_dlkm`

into a NEW local directory. It makes a small `U13_PARTITION_SHA256_REPORT.json` containing SHA256 values that can be uploaded directly to the ChatGPT conversation or committed in a later research report. The actual extracted images are kept on the ThinkPad and are **NOT** to be flashed to the phone.

Example PowerShell usage, with actual user paths substituted:

```powershell
powershell -File .\u13_windows_local_extract.ps1 -PayloadFile "D:\ROM\payload.bin" -PayloadProperties "D:\ROM\payload_properties.txt" -DumperExe "D:\Tools\payload-dumper-go.exe"
```

This local helper has been authored and committed but has **NOT** been run against the user's actual file nor verified on their ThinkPad. Do not claim completed extraction until the user reports its result.

## Strict status

- Official OTA metadata match: **PASS from U12**.
- Official 3GB binary downloaded into U13 runner: **NO (HTTP 403)**.
- Actual official boot vs U7 experimental kernel SHA/ABI: **UNKNOWN**.
- Matching current ROM vendor .ko ABI/vermagic or shiba DTBO: **UNKNOWN**.
- QEMU Ubuntu systemd integration: **PASS from U10, QEMU only**.
- Pixel 8 native Ubuntu boot: **NOT TESTED**.
- Any images safe to flash: **NO**.

**DO NOT FLASH. U13 binary validation is BLOCKED until exact source bytes are available for offline analysis.**
