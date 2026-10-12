# U36 — Ubuntu Base actually executes on ARM64 in QEMU, no handset access

**Goal:** turn U35's successful file-format packaging into a genuine **off-device Ubuntu userspace execution test**. The tested board is a **generic QEMU ARM64 `virt` machine**, NOT Pixel 8/Tensor G3.

**Input reference, immutable U35:** [U35 PASS GitHub Actions run 38196600339](https://github.com/TeamWearFreedomProject/Pixel8_Drodian/actions/runs/38196600339) and its `u35-UBUNTU-ARM64-BOOTV4-STAGE0-REPORT-NOT-FLASHABLE-5` audit artifact. Its precise `boot.img` kernel payload SHA256, `init_boot.img` new stage-0 ramdisk SHA256 and Canonical Ubuntu Base archive SHA256 are checked by a fail-closed independent auditor. **No binary phone image is retrieved from U35.**

## What this cloud-only CI actually does

- Download the U35 evidence JSON with exact immutable run ID and check its PASS string, pinned kernel/initramfs hashes, and explicit `physical_Pixel8_flash_gate=DENY`. No large kernel build is repeated.
- Download the official Canonical [Ubuntu Base 26.04.1 ARM64](https://cdimage.ubuntu.com/ubuntu-base/releases/26.04/release/ubuntu-base-26.04.1-base-arm64.tar.gz) archive and official `SHA256SUMS`, verify **its bytes match the very same U35 archive hash** `5a1906794ced63a71a8119c3f211ef5f0bbe0a243001b4bbd41fdf80c5b219fd`. Extract and package into a disposable **768 MiB lab ext4 image** with unique label `U36_UBUNTU_LAB`. This does NOT represent Android `userdata`, does NOT choose a Pixel partition, and is NOT a phone-ready filesystem.
- Boot the known-working **official Canonical Ubuntu Server 26.04 ARM64 cloud image** on QEMU `virt` + AArch64 EFI + virtual blk devices, as U34 successfully did. Attach the separate lab ext4 block drive explicitly as **read-only**.
- From **within the actual ARM64 guest** at cloud-init final stage: check machine `aarch64`, resolve the uniquely labelled attached lab disk, **mount it read-only**, and run `chroot /mnt/u36-base /bin/sh -c ...` which genuinely executes `/bin/sh`, `/bin/ls`, reads `/etc/os-release` and checks version `26.04` **from the separately mounted Ubuntu Base filesystem**, not from the cloud guest filesystem. Verify its architecture, then unmount it, trigger automatic VM shutdown, record QEMU's actual exit code.
- Save **only audit JSON, provenance hashes, exact serial-witness lines and real QEMU exit status**. Never publish QEMU virtual disks, `.img` flashing materials or userdata.
- Test fails red on missing U35 chain of custody, SHA mismatches, failure to mount **read-only**, failed guest `chroot`, wrong Ubuntu version, wrong CPU architecture, absent success witness, or nonzero/timeout QEMU exit.

**What U36 does not do:** it does NOT execute U35 `/init` as PID 1, does NOT do `switch_root` into Ubuntu Base, does NOT boot the U33 Tensor G3 GKI Image in QEMU, and certainly does NOT emulate Pixel 8 proprietary hardware, verify exact stock CP2A module/CRC ABI, shiba DTBO panel or AVB/rollback/rescue. Proving `chroot` is an **intermediate userland smoke test**, not a fully functional Ubuntu boot or safe flash. U35's separate lab `boot.img` and `init_boot.img` are format-only research products, not validated hardware boot images.

**Follow-up after real CI success:** plan a separate generic-QEMU **initramfs PID 1 → `switch_root`** test, then a stock CP2A firmware compatibility and shiba board audit before even *considering* any actual phone operation. Avoid more than necessary kernel rebuild time on failed packaging.

PC is unavailable due to school equipment collection; all work uses GitHub Actions with no PC admin rights or Android phone connection.

**REAL PIXEL 8 HARDWARE BOOT/FLASH GATE: DENY.**
