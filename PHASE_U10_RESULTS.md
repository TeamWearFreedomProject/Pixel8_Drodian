# U10 RESULTS — real Ubuntu 26.04 ARM64 systemd unit execution under QEMU + Pixel 8 shiba gating

**U10 GitHub Actions #3: ALL JOBS SUCCESS**
**This is a generic QEMU VM achievement, NOT a Pixel 8 bootable image. Do not flash.**

## Evidence

- Date: 2026-10-10
- [U10 Actions run #3 SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060845096) — both jobs passed:
  1. Generic QEMU AArch64 Ubuntu userspace/service execution.
  2. Android16 public shiba board/kernel source readiness audit.
- [U10 VM boot logs, JSON validation and original-rootfs integrity evidence](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060845096/artifacts/11672644512) — `shiba-u10-qemu-systemd-integration-evidence-3`; 3,738 bytes ZIP, expires 2026-11-09 14:47 UTC.
- [U10 shiba readiness gate artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060845096/artifacts/11672274643) — `shiba-u10-android16-readiness-3`; 1,740 bytes ZIP, expires 2026-11-09 14:45 UTC.

## What was demonstrably achieved in the VM

U10 downloaded the successful, SHA256-pinned U6 Ubuntu ext4 rootfs, U8 AArch64 static-BusyBox initramfs, and U9 **QEMU-only Linux 6.6.89** kernel. CI made a disposable COPY of the Ubuntu rootfs with test-only `u10-vm-smoke.target` and `u10-vm-smoke.service` files, then launched a real QEMU AArch64 guest with read-only virtio disk and explicit UUID gate.

The serial log contains the distinct sequence:

```text
U10_INIT_STARTED
U10_REACHED_SWITCH_ROOT
U10_SYSTEMD_VM_SERVICE_EXECUTED
```

These markers establish that the guest kernel ran the guarded initramfs, the Ubuntu rootfs handoff was reached, and **a systemd-spawned test service actually executed** in Ubuntu inside QEMU. The verification unit was a temporary VM-only addition; the original U6 image does not contain it.

| Test | Result |
| --- | --- |
| Generic QEMU ARM64 kernel | **PASS** |
| Guarded ARM64 initramfs execution | **PASS** |
| U6 rootfs UUID/type/label exact verification | **PASS** |
| First-stage read-only Ubuntu ext4 mount | **PASS** |
| `switch_root` path reached | **PASS** |
| Custom systemd unit actually ran in guest | **PASS** |
| Original U6 ext4 SHA256 remained unchanged | **PASS** |
| Android16 public shiba source + U7 kernel evidence | **PASS** (offline only) |
| Interactive Ubuntu login prompt | **NOT OBSERVED** |
| Phosh/Labwc graphical session | **NOT TESTED** |
| Physical Pixel 8 native Linux boot | **NOT TESTED** |

The isolated VM target was intentionally minimal and ran before a normal systemd welcome banner was printed. The CI verifier was updated to recognize the uniquely named service runtime log together with the test-unit console marker. No incorrect claim of a fully booted desktop or login session is made.

## SHA256 values from successful run

- U6 Ubuntu rootfs **original**: `d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e`
- QEMU-only modified disposable rootfs **copy**: `2405cf96046888e09d99e5ebf7dae5f30617a7fa061ade754a469adcb77105bc`
- Generic QEMU Linux 6.6.89 `Image`: `718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc`
- Repacked VM-only test initramfs: `b54fac796d14535c09539ba9ee43f73f67b9fe31b16efb0717b8e09139e8064c`

## Two earlier U10 runs and their repairs

1. [U10 #1 failed](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060486557) because the VM rootfs injection verifier treated the harmless `debugfs` banner on stderr as part of the expected systemd unit contents. The device readiness check had passed.
2. [U10 #2 VM genuinely executed its systemd unit](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060602316) and printed the target marker, but the old CI log validator required a particular normal systemd startup banner not output by the purposely minimal target.
3. [U10 #3 SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38060845096), using corrected checks. All jobs passed.

## Pixel 8 shiba integration is STILL BLOCKED

The phone runs **Evolution X Android 16**, as reported by the user. The installed build fingerprint, exact running vendor/kernel KMI and module vermagic, `shiba` DTBO, matching `vendor_boot` and `vendor_kernel_boot` components, Android Verified Boot integration, and safe physical Linux rootfs storage location are still not established.

U9/U10 generic QEMU Linux 6.6.89 must NEVER be treated as a bootable Pixel 8 kernel. Earlier U7 Google shusky experimental kernel is separate and unverified against the user's installed vendor modules. Android 17 references and `husky` Pixel 8 Pro boot images are not safe substitutes.

No Pixel 8 flashable firmware was generated, no ADB/fastboot/partition operations were used, and no physical device or Android user data was changed.

## Next milestones

- A safe separate *VM-only* console login verification without enabling accounts/network access on the real phone; then GUI compositor smoke tests under a virtual DRM backend if feasible.
- Exact **shiba** Android 16 running kernel/vendor provenance and module compatibility investigation, with deliberate review of shiba-specific device tree, display, touch, GPU, USB-C alt-mode and power.
- Only after hardware kernel/vendor verification and reviewed storage/rollback architecture can genuine Pixel 8 boot candidates be responsibly considered.

**BUILD/VM ONLY — NOT BOOTABLE ON PIXEL 8 — DO NOT FLASH.**
