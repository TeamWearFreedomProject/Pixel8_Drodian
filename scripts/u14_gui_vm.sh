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
unset WAYLAND_DISPLAY
# Let Labwc create its own primary socket: wayland-0 in fresh QEMU guest.
SOCKET_PATH="$XDG_RUNTIME_DIR/wayland-0"
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
    echo "U14_LABWC_LOG_FIRST_LINES"
    head -n 30 "$XDG_RUNTIME_DIR/labwc.log" || :
    echo "U14_LABWC_LOG_ERROR_LINES"
    grep -Ei '(error|fatal|fail|unable|not found|cannot|denied|backend|renderer|seat|refus|warning|no such|permission|invalid)' "$XDG_RUNTIME_DIR/labwc.log" | tail -n 100 || :
    echo "U14_LABWC_LOG_RECENT_NON_LOADER_LINES"
    grep -Ev '^[[:space:]]*[0-9]+:[[:space:]]*(calling|file=|trying file=|find library=|initialize program|transferring control|symbol=)' "$XDG_RUNTIME_DIR/labwc.log" | tail -n 80 || :
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
