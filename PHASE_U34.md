# U34 — Ubuntu 26.04 ARM64 guest smoke boot entirely in GitHub Actions

**USER'S SCHOOL PC IS RECLAIMED 2026-10-12 AND UNAVAILABLE FOR ABOUT TWO WEEKS.** U34 runs with **zero access to that PC or Pixel 8 phone**. Once opened, GitHub Actions continues on its own runner; check progress from an iPad or other browser without local administrator privileges.

## Source and test

Use the official Canonical **Ubuntu Server 26.04 LTS Resolute Raccoon ARM64 cloud image**, [release listing](https://cloud-images.ubuntu.com/releases/resolute/release/): `ubuntu-26.04-server-cloudimg-arm64.img`. Download the same directory's `SHA256SUMS` over HTTPS and verify the exact image's SHA256; record its digest and QCOW2 metadata. The signed SHA256SUMS GPG signature is **NOT independently verified** in this initial smoke test.

Create an ephemeral write-once cloud-init NoCloud seed and QEMU copy-on-write overlay in the GitHub-hosted Ubuntu runner. Emulate generic **QEMU ARM64 `virt`** with **QEMU ARM EFI**, virtual block device, serial console, and virtio networking. The guest must reach **cloud-init final stage**, report `uname -m=aarch64`, report Ubuntu `VERSION_ID=26.04` from `/etc/os-release`, emit unique serial-only success markers, and shut down with actual QEMU exit code **0**, within a bounded 27-minute watchdog. Any failure is a real red gate with auditable flags.

Only hashes, QEMU exit status and serial witness lines are preserved as a GitHub Actions artifact. **No QCOW2 disk, `.img`, Ubuntu userdata payload, kernel binary or flashed vendor data is uploaded.**

## Distinguish QEMU success from a bootable Pixel 8

The QEMU guest boots its **own Ubuntu-provided generic arm64 kernel**, not the U33 Tensor G3 Linux 6.1.157 source-based shusky kernel. QEMU's generic `virt` machine is **NOT** an emulator of Pixel 8's proprietary boot ROM, bootloader, Mali/display/panel, USB, clock, power, modem, UWB, boot images or AVB. Even a green cloud boot cannot prove phone compatibility.

U33 [successful source GKI + 454 unique modules full-coverage CI](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38182445756) eliminated 58 previously stale 6.1.124 modules and performed 26,203 internal CRC comparisons with no observed conflict, but **stock CP2A reference ABI**, actual shiba DTBO/panel selection, release suffix, AVB rollback, reliable rescue, and correct rootfs/initramfs/DTBO packaging are not tested. The source kernel's banner `6.1.157-android14-11` is not full stock `6.1.157-android14-11-gbd23337e42e7-ab14791245`. No installable Pixel 8 Ubuntu image is being produced.

## U35 decision point

Schedule a **read-only CP2A compatibility reference audit and packaging checklist**, not an arbitrary real-device deadline. Since the school PC is taken today, there is no safe reason to rush into a non-recoverable flash. Work on GitHub can resume in 2 weeks or on another trusted non-managed PC. Do not rely on factory-image recovery as a guarantee if the device bootloader/AVB security path itself becomes inaccessible.

**REAL PIXEL 8 BOOT / FLASH GATE: DENY.**
