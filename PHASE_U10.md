# Ubuntu Phase U10 — integrate actual rootfs/systemd in QEMU + shiba firmware readiness

**OFFLINE BUILD/VM ONLY • NOT A FLASHABLE PIXEL 8 ROM • DO NOT FLASH**

## Goal and scope

The user's Pixel 8 (`shiba`) currently runs Evolution X Android 16.
Prior U9 confirmed a **generic QEMU AArch64** Linux kernel booting from
U8 first-stage into the real Ubuntu 26.04 ARM64 ext4 rootfs and **systemd PID1
logs**. However, the VM did **not** show an interactive login or real systemd
service execution and did not validate Pixel 8 hardware.

U10 separates the word *integration* into two independently checked tracks:

### Track A: execute an actual Ubuntu systemd unit inside a virtual ARM64 guest

- Reuse SHA256-pinned **U6 original Ubuntu GUI rootfs**, **U8 first-stage**
  and **U9 successful generic QEMU guest Linux 6.6.89 kernel**, downloaded
  from previous successful Actions runs.
- Never mutate U6 original: create a 2GiB **disposable CI-only copy** with a
  custom `u10-vm-smoke.service` and `u10-vm-smoke.target` injected offline
  via `debugfs`, with integrity validation.
- Continue using first-stage **exact UUID + ext4 label/type checks** and an
  initial read-only `ro,noload` mount, from U8.
- Boot using `qemu-system-aarch64 -M virt`, and request isolated target
  `systemd.unit=u10-vm-smoke.target`.
- Only claim this track passed if serial logs show the actual one-shot service
  executed by systemd and wrote `U10_SYSTEMD_VM_SERVICE_EXECUTED` to console.
- No password, login account or network-access services are created;
  no actual interactive login is implied by an isolated service marker.
- No physical phone, ADB, fastboot, Android partition or user data is accessed.

### Track B: device compatibility readiness (STATIC ONLY)

- Revalidate prior [U7 research v4 `boot.img`](PHASE_U7_RESULTS.md) kernel
  payload provenance via exact SHA256.
- Pin public Evolution X Android 16 `shusky` and `zuma` board tree revisions
  used in [U5](PHASE_U5_RESULTS.md). These public trees are **not proof of
  the user's installed build**.
- Explicitly record what is *not* verified: current Evolution X firmware
  kernel/vendor module KMI, shiba DTBO, vendor boot fragments, AVB/security,
  physical Linux rootfs location, panel/touch/Mali/USB-C display/power.
- U9 Linux **6.6.89** is a `QEMU virt` kernel, NOT a Pixel 8/Tensor G3 kernel.
  U7 experimental Google shusky Linux is a *different* kernel and is also
  not established to match the currently installed ROM.
- No new deployable `boot.img`, `init_boot.img`, `vendor_boot.img`,
  `userdata.img` or firmware is generated here.

## Source

- [GitHub Actions U10](.github/workflows/phase-u10-integration.yml)
- [VM-only rootfs copy and systemd unit injection](scripts/u10_prepare_vm.py)
- [Real VM execution assertion](scripts/u10_vm_assert.py)
- [Pinned Android 16 shiba compatibility gate](scripts/u10_shiba_readiness.py)

Successful CI would prove the **Ubuntu userspace boot chain running a unit
inside QEMU**, and the ability to reason honestly about outstanding
shiba-specific integration. It does **NOT** mean Linux can boot Pixel 8,
run GUI or be safely flashed.

Initial CI is triggered by committing this plan.
