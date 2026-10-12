#!/bin/busybox sh
# U35 EXPERIMENTAL ARM64 EARLY INIT - OFFLINE BOOT IMAGE FORMAT STUDY ONLY
# NOT A Pixel 8 recovery image, not a usable Ubuntu desktop, never flash.
# Intentionally no userdata autodetection, partition writes or mounting root.
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
/bin/busybox mount -t proc proc /proc 2>/dev/null || true
/bin/busybox mount -t sysfs sysfs /sys 2>/dev/null || true
/bin/busybox mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
/bin/busybox mkdir -p /dev /run /tmp
/bin/busybox echo "U35_ARM64_STAGE0_BEGIN_NO_ROOTFS_AUTO_MOUNT" >/dev/console 2>/dev/null || true
/bin/busybox echo "U35 research: no stock CP2A ABI, DTBO, AVB or rescue validation."
/bin/busybox echo "No Ubuntu root handoff is configured. No block devices are written."
/bin/busybox echo "U35_ARM64_STAGE0_HALT_AT_DIAGNOSTIC_SHELL" >/dev/console 2>/dev/null || true
exec /bin/busybox sh
