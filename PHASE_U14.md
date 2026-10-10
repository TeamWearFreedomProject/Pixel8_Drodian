# Phase U14 — real Ubuntu 26.04 ARM64 Labwc GUI startup in QEMU (headless only)

**BUILD AND VIRTUAL-MACHINE TEST ONLY. NO PIXEL 8 FLASHING.**

## Deadline and goal

The project's immediate goal is to launch a real GUI session. A fully
working **Pixel 8 native screen** by 2026-10-11 noon Japan time is **not
established or guaranteed**: the phone's kernel/vendor module ABI, display,
touch, GPU, secure boot and safe on-phone root filesystem are unverified.

The nearest independently testable milestone is for the **real Ubuntu ARM64
userspace installed in U6** to launch **Labwc**, an actual Wayland GUI
compositor, under the same real generic ARM64 QEMU VM kernel that passed U10.

U14 deliberately sets `WLR_BACKENDS=headless`,
`WLR_RENDERER=pixman`, and `WLR_HEADLESS_OUTPUTS=1`; successful startup
would prove only a **headless Wayland session**, NOT rendered pixels on the
Pixel 8 or on an actual virtual video display.

## Existing verified, unchanged inputs

- Original **2 GiB Ubuntu 26.04 ARM64 rootfs from U6**:
  `d3cbe5e0a0e170e9e1e3071b32394e0ddd686887351ed1f4aa2b8bed814bde9e`.
  Includes actual native ARM64 Labwc 0.9.3, Waybar and Phosh packages,
  although only Labwc is the direct U14 runtime target.
- Guarded **U8 static BusyBox ARM64 initramfs**:
  `dc50919b6a4e89dc8c27d84dee5335105c756573ef3dcf74c3465a414e50372b`.
- **Generic QEMU-only ARM64 Linux kernel** from U9:
  `718c5584d0a1a69943c68689c0dadbd9b0ce6623e48e9a1b97429293c41efddc`.
- All three are fetched from previous successful Actions and independently
  SHA256 checked. Not a Pixel 8 firmware kernel.

## Technical test

1. Copy U6 rootfs to a **disposable virtual-machine ext4 IMG**, never touch
   the U6 source, and inject an isolated `u14-gui.target`,
   `u14-gui.service`, and [GUI test shell](scripts/u14_gui_vm.sh)
   using offline `debugfs` operations.
2. Build a **statically linked ARM64 probe** from
   [u14_wayland_probe.c](scripts/u14_wayland_probe.c) and place it only in
   the disposable QEMU rootfs. It connects to the real Wayland Unix socket,
   issues `wl_display.get_registry` and requires a real
   `wl_registry.global` response from the compositor.
3. Boot genuine AArch64 Linux in `qemu-system-aarch64 -M virt`, with a
   **read-only** virtio Ubuntu disk and U8's exact UUID research gate.
4. Have systemd run `labwc` under a **headless wlroots backend**, with
   `pixman` software rendering; no Android vendor GPU or real hardware
   screen devices are available in this test.
5. The verifier rejects success unless the actual guest serial log shows
   Linux startup, guarded `switch_root`, the systemd GUI service, Labwc's
   Wayland Unix socket, and the **real Wayland protocol registry reply**.
   Merely installing Labwc or creating a socket is insufficient.
6. Save guest serial log and evidence reports as **small GitHub Artifacts**,
   not rootfs firmware, payloads or bootable phone partitions.

## Sources

- [U14 QEMU GUI Action](.github/workflows/phase-u14-wayland-gui-vm.yml)
- [Temporary Ubuntu rootfs preparation](scripts/u14_prepare_gui_vm.py)
- [Actual Labwc startup script](scripts/u14_gui_vm.sh)
- [Independent Wayland protocol probe](scripts/u14_wayland_probe.c)
- [Guest serial evidence auditor](scripts/u14_assert_gui_vm.py)

Even if U14 succeeds, **a headless compositor is not a visible GUI**.
A further test using a QEMU virtual DRM/virtio GPU (and ultimately shiba
hardware) is needed before saying a screen displays anything.

**NO FLASHABLE PIXEL 8 UBUNTU IMAGE. DO NOT FLASH.**

## U14 first real QEMU GUI attempt — incomplete

- [U14 run #1](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38065300606) compiled the static ARM64 Wayland protocol probe successfully, verified the SHA256-pinned U6/U8/U9 inputs, created the VM-only rootfs, and booted real AArch64 Linux into Ubuntu systemd.
- Console logged `U14_FIRST_STAGE_STARTED`, `U14_REACHED_SWITCH_ROOT`, `U14_GUEST_LABWC_TEST_STARTED` and `U14_STARTING_REAL_LABWC_HEADLESS_BACKEND`.
- The Labwc process exited before a Wayland socket/registry handshake was observed, causing deliberate final CI FAIL. The immediate guest diagnostic file was empty. It **did not demonstrate a working GUI**.
- The GUI startup tester now waits up to 10 seconds even if the launcher process exits (allowing for a possible fork), prints the binary version and runtime directory, and captures console diagnostics before concluding failure.
- This update starts **U14 retry #2**. No real phone or vendor drivers are exercised.

## U14 retry #2 and deeper compositor startup diagnostics

- [U14 retry #2](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38065708768): kernel `switch_root` and systemd GUI service executed, but the Labwc launcher process exited and no Wayland socket appeared after ten seconds. Actual GUI remains **NOT proven**.
- The original guest stdout filter stripped out nonmatching errors and an empty Labwc log did not reveal why the process quit.
- GUI script now captures `ldd` shared-library dependencies, Linux dynamic-loader traces (`LD_DEBUG=libs,files`), the real child exit code, and more guest diagnostics.
- GitHub Actions now prints the **unfiltered** guest GUI serial section; QEMU timeout for these diagnostics is 68 seconds.
- This document update triggers **U14 retry #3**, still without Pixel 8 hardware or flashable images.

## U14 retry #3 diagnostic — Labwc exists and libraries resolve, but exits 1

- [U14 run #3](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38065994115) reached guest Ubuntu systemd GUI service; `ldd` resolved the ARM64 Labwc/wlroots 0.19 libraries, `labwc --version` printed `labwc 0.9.3`, and the real Labwc command exited with status **1**.
- No Wayland registry handshake or visible GUI was observed. The guest had produced a very large dynamic-loader trace, and `tail` accidentally retained library unload calls instead of the actual startup error.
- U14 now reports the **first log lines**, errors filtered by words such as `fail`/`backend`/`renderer`/`seat`, and **recent non-loader** lines separately.
- This triggers **U14 retry #4** to capture a specific compositor failure instead of guessing. Physical Pixel 8 is still unchanged.

## U14 retry #4: dynamic linker fine; Labwc exits before socket

- [U14 run #4](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38066211416) again reached systemd. Labwc 0.9.3 exited with code 1. `ldd` showed all required shared libraries resolved, but there was no accepted socket; no GUI handshake.
- The labwc upstream manpage documents `labwc -d` to enable full debug information. The new launch now uses this option, removes noisy `LD_DEBUG`, and **unsets `WAYLAND_DISPLAY` before spawning Labwc** (so it does not attempt a nested connection). The test probes the fresh VM's expected auto-created `wayland-0` socket.
- [U14 run #5] is triggered by this documentation update. No ROM firmware is generated or flashed.

## U14 retry #5 — actual headless backend and software renderer initialized

- [U14 run #5](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38066452022) showed something important: **Labwc 0.9.3 genuinely initialized wlroots headless backend, pixman renderer, and shm allocator** in the ARM64 Ubuntu VM. That is further GUI infrastructure progress beyond merely executing a binary.
- It still exited with code 1 before creating a Wayland socket, so **no compositor Wayland handshake / visible GUI** can yet be claimed.
- Its `-d` startup log was only approximately 2.7 KB, but the first-30-lines truncation cut off the final cause. The test now writes the **ENTIRE small Labwc debug log** into QEMU guest serial output, retaining the end of startup.
- This documentation change triggers **U14 retry #6**, which seeks the remaining failure and keeps the pass gate strict.
