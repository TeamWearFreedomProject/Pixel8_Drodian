#!/bin/sh
# U16: QEMU virtio-GPU DRM/KMS experiment ONLY. Not a Pixel 8 startup script.
set -eu
exec >/dev/console 2>&1
echo U16_GUEST_STARTED

export PATH=/usr/bin:/bin:/usr/sbin:/sbin
export HOME=/root
export XDG_RUNTIME_DIR=/run/u16-labwc
export XDG_CONFIG_HOME=/run/u16-labwc/config
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=labwc
export WLR_BACKENDS=drm
export WLR_DRM_DEVICES=/dev/dri/card0
export WLR_RENDERER=pixman
export WLR_RENDERER_ALLOW_SOFTWARE=1
export WLR_LIBINPUT_NO_DEVICES=1
export LIBSEAT_BACKEND=seatd
export SEATD_VTBOUND=0
export TMPDIR=/run/u16-labwc/tmp
unset WAYLAND_DISPLAY DISPLAY
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/labwc" "$TMPDIR"
chmod 0700 "$XDG_RUNTIME_DIR" "$TMPDIR"
mount -t tmpfs -o size=32m,mode=1777 tmpfs /tmp || { echo U16_FAIL_TMPFS; exit 1; }
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

echo U16_DRM_ENUMERATION_BEGIN
ls -la /dev/dri 2>&1 || :
ls -la /sys/class/drm 2>&1 || :
echo U16_VIRTIO_SYSFS_BEGIN
ls -la /sys/bus/virtio/devices 2>&1 || :
ls -la /sys/bus/pci/devices 2>&1 || :
ls -la /sys/bus/virtio/drivers 2>&1 || :
for node in /sys/bus/virtio/devices/*/device; do
  [ -r "$node" ] || continue
  echo "U16_VIRTIO_DEVICE $node $(cat "$node")"
done
echo U16_VIRTIO_SYSFS_END
echo U16_DMESG_DEVICE_PROBE_BEGIN
dmesg | grep -i -E 'virtio|pci|drm|gpu|fbcon|framebuffer|dma|shmem' | tail -n 110 || :
echo U16_DMESG_DEVICE_PROBE_END
echo U16_DRM_ENUMERATION_END
if [ ! -c /dev/dri/card0 ]; then
  echo U16_FAIL_DRM_CARD_ABSENT
  exit 1
fi
echo U16_DRM_CARD_PRESENT
# PCI virtio-gpu has a two-layer driver model: card0's parent is
# PCI "virtio-pci", while the child virtio bus device binds "virtio_gpu".
# Validate the *child of the card's actual PCI parent*, not the PCI driver.
pci_driver=$(readlink -f /sys/class/drm/card0/device/driver 2>/dev/null || :)
echo "U16_DRM_PCI_TRANSPORT $pci_driver"
bound_gpu=0
for child in /sys/class/drm/card0/device/virtio*; do
  [ -r "$child/device" ] || continue
  child_id=$(cat "$child/device" || :)
  child_driver=$(readlink -f "$child/driver" 2>/dev/null || :)
  echo "U16_DRM_VIRTIO_CHILD $child id=$child_id driver=$child_driver"
  case "$child_id:$child_driver" in
    0x0010:*/virtio_gpu) bound_gpu=1 ;;
  esac
done
if [ "$bound_gpu" -ne 1 ]; then
  echo U16_FAIL_NOT_VIRTIO_GPU
  exit 1
fi
echo U16_VIRTIO_GPU_DRIVER_VERIFIED
connected=0
for p in /sys/class/drm/card*-*/status; do
  [ -f "$p" ] || continue
  status=$(cat "$p")
  echo "U16_DRM_CONNECTOR $p $status"
  if [ "$status" = connected ]; then connected=1; fi
done
if [ "$connected" != 1 ]; then
  echo U16_FAIL_DRM_CONNECTOR_NOT_CONNECTED
  exit 1
fi
echo U16_DRM_CONNECTOR_CONNECTED

if [ ! -x /usr/bin/u16-seatd ]; then
  echo U16_FAIL_SEATD_NOT_INSTALLED
  exit 1
fi
echo U16_SEATD_LAUNCH
/usr/bin/u16-seatd -g root -l debug > "$XDG_RUNTIME_DIR/seatd.log" 2>&1 &
seatd_pid=$!
i=0
while [ ! -S /run/seatd.sock ] && [ "$i" -lt 10 ]; do
  sleep 1
  i=$((i+1))
done
if [ ! -S /run/seatd.sock ]; then
  echo U16_FAIL_SEATD_SOCKET_ABSENT
  cat "$XDG_RUNTIME_DIR/seatd.log" || :
  exit 1
fi
echo U16_SEATD_READY
echo U16_LABWC_DRM_ATTEMPT
/usr/bin/labwc -d > "$XDG_RUNTIME_DIR/labwc.log" 2>&1 &
labwc_pid=$!
ready=0
i=0
while [ "$i" -lt 35 ]; do
  if [ -S "$XDG_RUNTIME_DIR/wayland-0" ]; then
    if /usr/bin/u14-wayland-probe "$XDG_RUNTIME_DIR/wayland-0"; then
      echo U16_DRM_WAYLAND_PROTOCOL_OK
      ready=1
      break
    fi
  fi
  if ! kill -0 "$labwc_pid" 2>/dev/null; then
    echo U16_LABWC_EXITED_EARLY
    break
  fi
  sleep 1
  i=$((i+1))
done
if [ "$ready" -eq 1 ]; then
  echo U16_WAYBAR_LAUNCH
  if [ -x /usr/bin/dbus-run-session ]; then
    WAYLAND_DISPLAY=wayland-0 /usr/bin/dbus-run-session -- /usr/bin/waybar -c /etc/u15-waybar.json -s /etc/u15-waybar.css > "$XDG_RUNTIME_DIR/waybar.log" 2>&1 &
  else
    WAYLAND_DISPLAY=wayland-0 /usr/bin/waybar -c /etc/u15-waybar.json -s /etc/u15-waybar.css > "$XDG_RUNTIME_DIR/waybar.log" 2>&1 &
  fi
  waybar_pid=$!
  sleep 8
  screenshot="$XDG_RUNTIME_DIR/u16-drm-wayland.png"
  echo U16_DRM_WAYLAND_CAPTURE_ATTEMPT
  if WAYLAND_DISPLAY=wayland-0 /usr/bin/u15-grim -t png "$screenshot" && [ -s "$screenshot" ]; then
    echo U16_PNG_BASE64_BEGIN
    base64 "$screenshot"
    echo U16_PNG_BASE64_END
    echo U16_DRM_WAYLAND_PNG_SERIALIZED
  else
    echo U16_FAIL_DRM_WAYLAND_SCREENSHOT
  fi
fi
echo U16_QEMU_DISPLAY_CAPTURE_WINDOW
# Keep actual DRM compositor AND Waybar visible during host HMP screendump.
sleep 28
if [ "$ready" -eq 1 ]; then
  kill "$waybar_pid" 2>/dev/null || :
  wait "$waybar_pid" 2>/dev/null || :
fi
echo U16_LABWC_LOG_BEGIN
cat "$XDG_RUNTIME_DIR/labwc.log" 2>/dev/null || :
echo U16_LABWC_LOG_END
echo U16_WAYBAR_LOG_BEGIN
cat "$XDG_RUNTIME_DIR/waybar.log" 2>/dev/null || :
echo U16_WAYBAR_LOG_END
echo U16_SEATD_LOG_BEGIN
cat "$XDG_RUNTIME_DIR/seatd.log" 2>/dev/null || :
echo U16_SEATD_LOG_END
kill "$labwc_pid" "$seatd_pid" 2>/dev/null || :
wait "$labwc_pid" 2>/dev/null || :
wait "$seatd_pid" 2>/dev/null || :
if [ "$ready" -ne 1 ]; then echo U16_FAIL_DRM_LABWC; exit 1; fi
echo U16_DRM_LABWC_FINISHED
exit 0
