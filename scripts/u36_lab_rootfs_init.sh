#!/bin/busybox sh
# Runs after actual switch_root on a disposable QEMU ARM64 virt VM.
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
if [ "$(/bin/busybox uname -m)" != "aarch64" ]; then
  echo U36_LAB_WRONG_CPU >/dev/console
  /bin/busybox poweroff -f
fi
if ! /bin/busybox grep -q '^VERSION_ID="*26\.04' /etc/os-release; then
  echo U36_LAB_WRONG_UBUNTU_RELEASE >/dev/console
  /bin/busybox poweroff -f
fi
echo U36_LAB_SWITCH_ROOT_AARCH64_UBUNTU_BASE_OK >/dev/console
echo "U36 Ubuntu Base reached through switch_root; this is NOT systemd or GUI" >/dev/console
/bin/busybox sync
/bin/busybox poweroff -f
/bin/busybox sleep 30
