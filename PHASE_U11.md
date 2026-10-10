# Ubuntu Phase U11 — Pixel 8 shiba kernel/vendor module compatibility evidence

**RESEARCH / GITHUB ACTIONS ONLY. NOT BOOTABLE. DO NOT FLASH.**

## Mission

The U9/U10 ARM64 QEMU virtual machine genuinely entered Ubuntu 26.04 and
executed a custom systemd unit, but that kernel is generic QEMU Linux 6.6.89.
This is *not* equivalent to booting a Google Pixel 8 with Tensor G3.

U11 checks the publicly declared Android16 Evolution X shiba kernel driver
load sequence and compares it to the experimental U7 boot header/kernel
without claiming that public metadata is installed firmware. The user's real
device is reported to be on Evolution X Android 16; its exact installed
firmware, build fingerprint, kernel and vendor driver revision are unknown.

## Immutable inputs and provenance

- [U7 experimental shiba research boot run](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38050847238):
  earlier independently compiled Google shusky kernel, NOT official
  Evolution X kernel and NOT confirmed compatible with the phone.
- [Evolution-X-Devices/device_google_shusky](https://github.com/Evolution-X-Devices/device_google_shusky/tree/bka),
  pinned `56006ae8162db285e776d85319d9942945b87194`.
- [Evolution-X-Devices/device_google_zuma](https://github.com/Evolution-X-Devices/device_google_zuma/tree/bka),
  pinned `fba447c6317f23501dbac209b6479e458800c449`.
- [LineageOS/android_device_google_shusky-kernels](https://github.com/LineageOS/android_device_google_shusky-kernels/tree/lineage-23.2),
  pinned `9bba989e7dba6f33258049b113adcb33c89054e8`.

The public LineageOS kernel *device repository* currently holds only a
small set of module load configuration lists. It does **not** contain actual
`.ko` drivers to compare against the U7 kernel or installed phone.

The shiba-specific init list includes `goodix_brl_touch.ko`, whereas the
husky-specific list uses `ftm5.ko`. This is a concrete example of why
husky (Pixel 8 Pro) files must not be substituted as shiba firmware.

## Actual U11 GitHub Actions experiment

[U11 workflow](.github/workflows/phase-u11-module-compat.yml)
and [read-only module compatibility auditor](scripts/u11_module_compat_audit.py):

1. Download prior U7 experimental `boot.img` from a successful artifact.
2. Verify the exact boot SHA256, Android header v4 and extracted kernel
   section SHA256; do not write or boot this research image.
3. Pin the public Android16 Evolution X shiba/zuma and Lineage kernel
   manifest repository commits.
4. Count common, `vendor_kernel_boot`, `vendor_dlkm` and `system_dlkm`
   module loading entries; compare shiba and husky special-module loads.
5. Check Evolution X device source declarations for Linux kernel 6.1,
   public kernel module metadata dependency and vendor boot module ordering.
6. Emit a module inventory CSV plus JSON and Markdown compatibility gate,
   explicitly recording zero independently verified driver binaries.
7. **Fail closed** on missing pins, changed manifests or inaccurate claims
   that files are flashable or bootable.

## Hard limits

The exact installed Evolution X build and its corresponding binary vendor
modules, module vermagic, modversions/KMI, DTBO/DTB, real panel/touch/USB-C/GPU
drivers, firmware signature/AVB chain and physical Linux rootfs location
remain unknown. U11 is **not** a proof that U7 kernel can boot with current
Evolution X vendor images. Filename equality and kernel version 6.1 do not
provide binary pairing.

No ADB, fastboot, phone connection, unlocking, flash, user data change or
new bootable firmware. All checks execute in GitHub Actions.

**U11 source-manifest SUCCESS would still mean PHYSICAL FLASH READINESS = FALSE.**
