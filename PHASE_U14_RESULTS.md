# U14 RESULTS — ARM64 Ubuntu 26.04 Labwc headless Wayland compositor

**PASS: real Labwc Wayland socket and protocol response under generic ARM64 QEMU.**
**NOT Pixel 8 native display, not a screenshot, not a deployable Ubuntu phone ROM.**

## Evidence

- [U14 run #8: SUCCESS](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38067190650) (completed 2026-10-11 01:21 JST).
- [U14 serial/JSON test artifact](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38067190650/artifacts/11675490776):
  `shiba-u14-arm64-headless-wayland-evidence-8`, 7,114 bytes.
  Expires 2026-11-09 16:21 UTC.
- [Workflow](.github/workflows/phase-u14-wayland-gui-vm.yml)
- [Test plan and seven failed retries](PHASE_U14.md)

## What the actual VM log proves

```text
U14_FIRST_STAGE_STARTED
U14_REACHED_SWITCH_ROOT
U14_GUEST_LABWC_TEST_STARTED
U14_REAL_WAYLAND_SOCKET_FOUND
U14_REAL_WAYLAND_PROTOCOL_REGISTRY_OK
U14_GUI_HEADLESS_COMPOSITOR_AND_WAYLAND_OK
U14_RESEARCH_HEADLESS_WAYLAND_TEST_PASSED
```

Inside the QEMU ARM64 guest, original Ubuntu 26.04 U6 packages were
executed with real `labwc 0.9.3`, wlroots headless backend, pixman
software renderer and shm allocator. The debug log records actual
`pixman buffer 1280x720` creation and `WAYLAND_DISPLAY=wayland-0`.
An independently cross-compiled AArch64 client connected to the Unix
socket, queried the compositor's registry and received an actual
`wl_registry.global` protocol response; CI correctly rejects merely
launching a process or creating an empty socket.

The guest was brought up using the tested QEMU-specific Linux 6.6.89
kernel, guarded U8 initramfs, and a **throwaway copy** of original
Ubuntu 26.04 ARM64 rootfs. The original U6 image was untouched. The
systemd `u14-gui.service` and `u14-gui.target` ran in the real guest.
The QEMU runner used `-display none`, and intentionally used headless
backend `WLR_BACKENDS=headless`.

## Scope of "GUI SUCCESS"

| Capability | Status |
| --- | --- |
| Ubuntu ARM64 rootfs and systemd service under QEMU | **PASS** |
| Real Labwc compositor initialized | **PASS** |
| Real Wayland socket + registry handshake | **PASS** |
| Software renderer created 1280x720 virtual pixel buffers | **PASS** |
| Visible virtual display screenshot, virtio-gpu DRM | **NOT TESTED** |
| Phosh phone UI visible on screen | **NOT TESTED** |
| Real Pixel 8 native display, touch and GPU | **NOT TESTED** |
| Kernel/vendor KMI and shiba DTBO integrated | **NOT VERIFIED** |
| Flashable Pixel 8 Ubuntu firmware | **NO** |

Thus "**GUI startup**" here means a working *headless Wayland compositor*,
not a verified complete desktop image or Pixel 8 display.

## What took eight runs?

The first attempts proved kernel/U8/systemd worked but Labwc exited.
Investigations showed full ELF library resolution and functioning
wlroots headless/pixman, then isolated a specific failure:
`No display available in the first 33` from Xwayland. The
original U6 was mounted read-only and /tmp had no writable X11 socket
directory. Simply setting `WLR_XWAYLAND=` didn't solve it.
A VM-only in-memory tmpfs for /tmp with correctly permissioned
`/tmp/.X11-unix` let Labwc initialize and answer a real protocol
client. No Pixel 8 partition was used.

## Next verified milestone

Run a **visible** QEMU `virtio-gpu`/DRM compositor test and capture
display pixel output in a VM, or a verified Phosh Wayland client
inside headless VM. In parallel, the actual Pixel 8 shiba Linux
kernel/vendor module, DTBO, panel, touch, Mali GPU, AVB and safe
rootfs handoff remain unverified. Official EvoX OTA CDN had blocked
the U13 binary comparison with HTTP 403.

**Do not flash U8/U9/U14 artifacts to the phone.**
