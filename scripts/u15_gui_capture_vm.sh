#!/bin/sh
# U14 isolated, QEMU-only Ubuntu 26.04 ARM64 Labwc GUI userspace test.
# It does NOT use Pixel display, GPU, DRM, input or Android vendor drivers.
set -eu
exec >/dev/console 2>&1
echo "U14_GUEST_LABWC_TEST_STARTED"
echo "U15_GUEST_PIXEL_CAPTURE_STARTED"

if [ ! -x /usr/bin/labwc ]; then
    echo "U14_GUI_FAIL: labwc binary missing"
    exit 1
fi
if [ ! -x /usr/bin/u14-wayland-probe ]; then
    echo "U14_GUI_FAIL: wayland probe missing/not executable"
    exit 1
fi
export PATH=/usr/bin:/bin
export HOME=/root
export XDG_RUNTIME_DIR=/run/u14-labwc
export XDG_CONFIG_HOME=/run/u14-labwc/config
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=labwc
unset WAYLAND_DISPLAY
# Let Labwc create its own primary socket: wayland-0 in fresh QEMU guest.
SOCKET_PATH="$XDG_RUNTIME_DIR/wayland-0"
export WLR_BACKENDS=headless
export WLR_HEADLESS_OUTPUTS=1
export WLR_RENDERER=pixman
export WLR_RENDERER_ALLOW_SOFTWARE=1
export WLR_LIBINPUT_NO_DEVICES=1
# A readonly 2GiB test rootfs does not provide writable /tmp/.X11-unix;
# disable optional Xwayland for native Wayland-only CI compositor testing.
export WLR_XWAYLAND=
echo "U14_XWAYLAND_DISABLED_IN_HEADLESS_GUEST"
export TMPDIR=/run/u14-labwc/tmp
unset DISPLAY

mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/labwc" "$TMPDIR"
chmod 0700 "$XDG_RUNTIME_DIR" "$TMPDIR"
# The U6 ext4 filesystem remains mounted ro; Xwayland needs /tmp/.X11-unix.
# Overlay /tmp with an ephemeral tmpfs ONLY inside disposable QEMU VM.
if ! mount -t tmpfs -o size=32m,mode=1777 tmpfs /tmp; then
    echo "U14_GUI_FAIL: unable to mount VM-only writable /tmp for Xwayland"
    exit 1
fi
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp /tmp/.X11-unix
echo "U14_QEMU_TMPFS_FOR_XWAYLAND_READY"
# There is no persistent root filesystem write, no login, no network service.
echo "U14_STARTING_REAL_LABWC_HEADLESS_BACKEND"
echo "U14_LOADER_LIBRARY_LIST_BEGIN"
if [ -x /usr/bin/ldd ]; then /usr/bin/ldd /usr/bin/labwc 2>&1 || :; fi
echo "U14_LOADER_LIBRARY_LIST_END"
/usr/bin/labwc --version 2>&1 || :
[ -r /etc/u14_gui_vm.sh ] && echo "U14_VM_TEST_SCRIPT_ACCESSIBLE"
[ -e /usr/lib/aarch64-linux-gnu/libwlroots-0.18.so ] && echo "U14_WLROOTS_SHARED_LIBRARY_PRESENT" || :
/usr/bin/labwc -d > "$XDG_RUNTIME_DIR/labwc.log" 2>&1 &
labwc_pid=$!

finished=0
i=0
while [ "$i" -lt 35 ]; do
    if [ -S "$SOCKET_PATH" ]; then
        echo "U14_REAL_WAYLAND_SOCKET_FOUND"
        if /usr/bin/u14-wayland-probe "$SOCKET_PATH"; then
            echo "U14_GUI_HEADLESS_COMPOSITOR_AND_WAYLAND_OK"
            finished=1
            break
        fi
    fi
    if ! kill -0 "$labwc_pid" 2>/dev/null; then
        if [ "$i" -ge 10 ]; then
            echo "U14_GUI_FAIL: labwc parent exited, no Wayland socket after 10 seconds"
            break
        fi
        # Some compositors fork or daemonize; don't race with startup.
        if [ "$i" -eq 0 ]; then
            echo "U14_LABWC_PARENT_EXITED_EARLY_WAITING_FOR_SOCKET"
        fi
    fi
    sleep 1
    i=$((i+1))
done

# U15: actual Wayland compositor PNG screencopy into writable /run tmpfs.
# Encode as base64 over serial console to avoid requiring any writable
# disk, host mount, guest networking, or phone data access.
if [ "$finished" -eq 1 ]; then
    if [ ! -x /usr/bin/u15-grim ]; then
        echo "U15_FAIL: grim Wayland screenshot client missing"
        exit 1
    fi
    echo "U15_STARTING_WAYBAR_CLIENT"
    if [ -x /usr/bin/dbus-run-session ]; then
        WAYLAND_DISPLAY=wayland-0 /usr/bin/dbus-run-session -- \
          /usr/bin/waybar -c /etc/u15-waybar.json \
          -s /etc/u15-waybar.css \
          > "$XDG_RUNTIME_DIR/u15-waybar.log" 2>&1 &
    else
        echo "U15_DBUS_RUN_SESSION_MISSING"
        WAYLAND_DISPLAY=wayland-0 /usr/bin/waybar \
          -c /etc/u15-waybar.json -s /etc/u15-waybar.css \
          > "$XDG_RUNTIME_DIR/u15-waybar.log" 2>&1 &
    fi
    waybar_pid=$!
    sleep 6
    echo "U15_CAPTURE_REAL_WAYLAND_FRAME"
    screenshot="$XDG_RUNTIME_DIR/u15-wayland-screen.png"
    if ! WAYLAND_DISPLAY=wayland-0 /usr/bin/u15-grim -t png "$screenshot"; then
        echo "U15_FAIL: wlroots screencopy failed"
        cat "$XDG_RUNTIME_DIR/u15-waybar.log" || :
        exit 1
    fi
    if [ ! -s "$screenshot" ]; then
        echo "U15_FAIL: screenshot file empty"
        exit 1
    fi
    if ! command -v base64 >/dev/null 2>&1; then
        echo "U15_FAIL: base64 encoder unavailable"
        exit 1
    fi
    echo "U15_PNG_BASE64_BEGIN"
    base64 "$screenshot"
    echo "U15_PNG_BASE64_END"
    echo "U15_REAL_WAYLAND_PNG_SERIALIZED"
    echo "U15_WAYBAR_LOG_START"
    cat "$XDG_RUNTIME_DIR/u15-waybar.log" || :
    echo "U15_WAYBAR_LOG_END"
    kill "$waybar_pid" 2>/dev/null || :
    wait "$waybar_pid" 2>/dev/null || :
fi

echo "U14_LABWC_DIAGNOSTICS"
ls -la "$XDG_RUNTIME_DIR" || :
ls -l /usr/bin/labwc /usr/bin/u14-wayland-probe || :
exit_code=0
if ! kill -0 "$labwc_pid" 2>/dev/null; then
    wait "$labwc_pid" || exit_code=$?
    echo "U14_LABWC_EXIT_STATUS=$exit_code"
fi
echo "U14_LABWC_LOG_START"
if [ -f "$XDG_RUNTIME_DIR/labwc.log" ]; then
    # Full -d debug log is small (~3 KiB) without LD_DEBUG: do not truncate
    # its last lines because they may contain the actual error.
    cat "$XDG_RUNTIME_DIR/labwc.log" || :
fi
echo "U14_LABWC_LOG_END"
kill "$labwc_pid" 2>/dev/null || :
wait "$labwc_pid" 2>/dev/null || :
if [ "$finished" -ne 1 ]; then
    echo "U14_GUI_HEADLESS_COMPOSITOR_FAILED"
    exit 1
fi
echo "U14_RESEARCH_HEADLESS_WAYLAND_TEST_PASSED"
exit 0
