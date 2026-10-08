# Phase 2 — Droidian / Halium research (BUILD ONLY)

Phase 1 compiled Google's Pixel 8 shusky kernel successfully:
https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/37721346230

Phase 2 checks Droidian's upstream Android 14 / GKI 6.1 packaging and
Halium configuration fragments against Google's shusky kernel.

## Workflow

**Actions → Droidian Phase 2 - Halium readiness (BUILD ONLY) → Run workflow**

Select:
- `upstream-only` (start here): inspect public Droidian source metadata and list expected kernel features. Usually short.
- `config-build` (second): rebuild shusky kernel using the Google production build method, save its `.config`, and compare it with Droidian's kernel configuration fragments.

The output is `halium-report.md` in an artifact and in the job summary.
This is analysis, not a working Droidian image.

## Upstream references

- https://github.com/droidian-devices/common_fragments/tree/6.1-android-common
- https://github.com/droidian-devices/linux-android-common-6.1-android14
- https://github.com/droidian/android-system-gsi-34-bin
- https://github.com/droidian/porting-guide

## Important limits

The Droidian generic kernel packaging and generic Android 14 GSI have NOT
been established as compatible with Android 17 Pixel 8 vendor binaries.
Neither the generic GKI package nor this audit is a shiba adaptation.
Different build branches may change the results. Security-related fragment
options are for inspection only, not automatic patching.

No phone connections, no flashing, no fastboot, no ADB.
