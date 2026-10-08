# Phase 3: Classify Halium kernel requirements

**BUILD ONLY — NO FLASH — NO NEW KERNEL COMPILE**

Phase 2 [config-build succeeded](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37724909814)
and reported **15 matches / 44 differences** between Google's Pixel 8 shusky
kernel configuration and Droidian's 6.1 Android 14 Halium fragments.

## Run

Open **Actions → Droidian Phase 3 - Classify kernel differences (BUILD ONLY)**,
click **Run workflow**, and keep these defaults:

- `phase2_run_id`: `37724909814`
- `phase2_artifact`: `halium-readiness-config-build-2`

The workflow downloads the 58 KB Phase 2 report/config artifact and produces
`phase3-triage.md` under **Summary** and **Artifacts**. It does not clone the
Google kernel or compile it again.

Note: the Phase 2 artifact is scheduled to expire on **October 15, 2026**.
If it has expired, re-run Phase 2 `config-build` and enter the new run ID
and new `halium-readiness-config-build-N` artifact name.

## Output classification

The Python script cross-checks the saved report's values against the actual
compiled `google-built.config` and groups differences into investigation queues:

- Halium core kernel/runtime capability
- Boot/rootfs design
- Security-sensitive configuration
- Android integration
- Built-in vs loadable modules
- Possible renamed/legacy kernel symbols
- Container-only/optional features

No Kconfig fragment is automatically applied. `user namespace`, `SELinux`,
and vendor-module signing features **must not** be changed blindly.

## What this does not establish

- It does not build Droidian/Halium for Pixel 8.
- It does not demonstrate Android 17 vendor compatibility with the Droidian
  Android 14 GSI package.
- It does not establish that the Google source branch matches the factory
  `CP3A.260905.009` boot image.
- It does not verify module ABI/signing, rootfs layout, or real hardware boot.

All work runs on the GitHub-hosted runner without ADB, fastboot or flash.
