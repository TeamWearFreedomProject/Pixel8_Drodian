#!/bin/busybox sh
# U36: QEMU-only ARM64 rootfs handoff laboratory. No device boot/flash.
# Explicitly refuses shiba/Pixel and all unknown board models.
# A successful test validates an isolated generic ARM64 lab only.
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
BB=/bin/busybox
$BB mkdir -p /proc /sys /dev /newroot
$BB mount -t proc proc /proc || exec $BB sh
$BB mount -t sysfs sysfs /sys || exec $BB sh
$BB mount -t devtmpfs devtmpfs /dev || exec $BB sh

die() {
  echo "U36_HANDOFF_DENIED: $1" >/dev/console
  exec /bin/busybox sh </dev/console >/dev/console 2>&1
}
test -r /proc/device-tree/model || die "not an identified generic QEMU virt machine"
model="$($BB tr -d '\000' < /proc/device-tree/model)"
case "$model" in
  *"linux,dummy-virt"*|*"QEMU Virtual Machine"*|*"QEMU virt"*) ;;
  *) die "machine model not allowlisted" ;;
esac

mode=
root=
for arg in $($BB cat /proc/cmdline); do
  case "$arg" in
    u36.lab=1) mode=1 ;;
    u36.root=/dev/vdb) root=/dev/vdb ;;
    u36.*) die "unknown u36 kernel argument" ;;
  esac
done
test "$mode" = 1 || die "explicit u36.lab=1 absent"
test "$root" = /dev/vdb || die "explicit QEMU virtual root block device absent"
echo U36_QEMU_ARM64_STAGE0_ENTERED >/dev/console

# Wait briefly for the *known* QEMU virtio test disk; no device discovery.
count=0
while [ ! -b /dev/vdb ] && [ "$count" -lt 25 ]; do
  $BB sleep 1
  count=$((count+1))
done
test -b /dev/vdb || die "known lab virtio disk not present"
# Read-only mount is deliberate; never format, decrypt or modify user data.
$BB mount -t ext4 -o ro /dev/vdb /newroot || die "lab ext4 mount failed"
test -f /newroot/etc/u36-lab-rootfs || die "research rootfs marker absent"
test "$($BB cat /newroot/etc/u36-lab-rootfs)" = "QEMU_ARM64_UBUNTU_26.04_U36_ONLY" || die "wrong research rootfs marker"
test -f /newroot/etc/os-release || die "Ubuntu release metadata missing"
$BB grep -q '^VERSION_ID="*26\.04' /newroot/etc/os-release || die "Ubuntu 26.04 required"
test -x /newroot/sbin/init || die "known lab init missing"

# Linux switch_root transfers rootfs and execs PID 1's lab init.
# Any success on QEMU DOES NOT provide evidence for Pixel 8 bootchain.
echo U36_QEMU_ARM64_SWITCH_ROOT_INVOKED >/dev/console
$BB mount --move /dev /newroot/dev || die "move dev failed"
$BB mount --move /proc /newroot/proc || die "move proc failed"
$BB mount --move /sys /newroot/sys || die "move sys failed"
exec /bin/busybox switch_root /newroot /sbin/init
