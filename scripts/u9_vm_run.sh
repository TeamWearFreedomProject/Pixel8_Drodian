#!/usr/bin/env bash
# U9: QEMU AArch64 virtual machine ONLY. Never touches physical hardware.
set -euo pipefail
: "${U9_KERNEL:?}"
: "${U9_RAMDISK:?}"
: "${U9_ROOT_IMG:?}"
: "${U9_OUT:?}"
: "${U9_VOLUME_UUID:?}"
mkdir -p "$U9_OUT"

base=(qemu-system-aarch64
  -M virt,gic-version=3
  -cpu cortex-a72
  -smp 2
  -m 2048
  -nodefaults
  -display none
  -monitor none
  -serial stdio
  -no-reboot
  -nic none
  -kernel "$U9_KERNEL"
  -initrd "$U9_RAMDISK"
  -drive "if=none,format=raw,readonly=on,file=$U9_ROOT_IMG,id=u6disk"
  -device "virtio-blk-device,drive=u6disk"
)

run_guest() {
  local label="$1" duration="$2" append="$3"
  echo "U9: starting QEMU guest $label (max ${duration}s)"
  set +e
  timeout -k 5 "$duration" "${base[@]}" -append "$append" \
    > "$U9_OUT/U9_${label}.log" 2>&1
  local rc=$?
  set -e
  echo "U9: QEMU $label exit $rc" | tee -a "$U9_OUT/U9_RUN_STATUS.txt"
  if (( rc != 0 && rc != 124 )); then
    echo "U9 QEMU error code $rc"
    tail -n 60 "$U9_OUT/U9_${label}.log"
    exit 1
  fi
  tail -n 25 "$U9_OUT/U9_${label}.log"
}

# Negative no-UUID control must halt before trying to mount rootfs.
run_guest NEGATIVE 32 \
  "console=ttyAMA0,115200 earlycon=pl011,0x9000000 loglevel=5 rdinit=/init"

# Positive path uses UUID from VERIFIED OFFLINE U6 ext4 file, not any Pixel path.
run_guest POSITIVE 115 \
  "console=ttyAMA0,115200 earlycon=pl011,0x9000000 loglevel=6 rdinit=/init u8.rootuuid=$U9_VOLUME_UUID u8.research_gate=I_UNDERSTAND_THIS_IS_UNVERIFIED"
