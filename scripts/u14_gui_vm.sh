#!/bin/sh
# U14 isolated, QEMU-only Ubuntu 26.04 ARM64 Labwc GUI userspace test.
# It does NOT use Pixel display, GPU, DRM, input or Android vendor drivers.
set -eu
exec >/dev/console 2>&1
echo "U14_GUEST_LABWC_TEST_STARTED"

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
export WAYLAND_DISPLAY=wayland-u14
export WLR_BACKENDS=headless
export WLR_HEADLESS_OUTPUTS=1
export WLR_RENDERER=pixman
export WLR_RENDERER_ALLOW_SOFTWARE=1
export WLR_LIBINPUT_NO_DEVICES=1
export TMPDIR=/run/u14-labwc/tmp
unset DISPLAY

mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/labwc" "$TMPDIR"
chmod 0700 "$XDG_RUNTIME_DIR" "$TMPDIR"
# There is no persistent root filesystem write, no login, no network service.
echo "U14_STARTING_REAL_LABWC_HEADLESS_BACKEND"
/usr/bin/labwc > "$XDG_RUNTIME_DIR/labwc.log" 2>&1 &
labwc_pid=$!

finished=0
i=0
while [ "$i" -lt 35 ]; do
    if [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
        echo "U14_REAL_WAYLAND_SOCKET_FOUND"
        if /usr/bin/u14-wayland-probe "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"; then
            echo "U14_GUI_HEADLESS_COMPOSITOR_AND_WAYLAND_OK"
            finished=1
            break
        fi
    fi
    if ! kill -0 "$labwc_pid" 2>/dev/null; then
        echo "U14_GUI_FAIL: labwc exited before protocol handshake"
        break
    fi
    sleep 1
    i=$((i+1))
done

echo "U14_LABWC_LOG_START"
if [ -f "$XDG_RUNTIME_DIR/labwc.log" ]; then
    tail -n 80 "$XDG_RUNTIME_DIR/labwc.log" || :
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
