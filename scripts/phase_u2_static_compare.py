#!/usr/bin/env python3
"""Read-only metadata comparison, Pixel 8 Pro Tensor Linux vs shiba Google CI."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

HUSKY = {"boot_a.img", "dtbo_a.img", "vendor_boot_a.img", "vendor_kernel_boot_a.img",
         "init_boot_a.img", "pvmfw_a.img", "vbmeta_a.img", "vbmeta_system_a.img",
         "vbmeta_vendor_a.img"}
SHIBA = {"boot.img", "dtbo.img", "vendor_kernel_boot.img", "Image", "Image.gz",
         "Image.lz4", "vendor_dlkm.img", "system_dlkm.img", "dtb.img"}
MAX_IMAGE = 160 * 1024 * 1024
KEYWORDS = ("husky", "shiba", "zuma", "akita", "google")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def uint(raw, off, fmt="<"):
    return struct.unpack_from(fmt + "I", raw, off)[0]


def align(n, page):
    return (n + page - 1) // page * page


def strings_of_interest(raw, count=16):
    found = set()
    for entry in re.findall(rb"[\x20-\x7e]{6,150}", raw):
        val = entry.decode("ascii", "replace")
        if any(word in val.lower() for word in KEYWORDS):
            found.add(val)
    return sorted(found)[:count]


def parse_boot(raw):
    if not raw.startswith(b"ANDROID!") or len(raw) < 4096:
        return None
    version = uint(raw, 40)
    out = {"header_version": version, "kernel_size": uint(raw, 8),
           "ramdisk_size": uint(raw, 12)}
    if version in (3, 4):
        page = 4096
        out["header_size"] = uint(raw, 20)
    elif version in (0, 1, 2):
        page = uint(raw, 36)
    else:
        out["warning"] = "unrecognized boot header version"
        return out
    if page < 512 or page > 65536 or page & (page - 1):
        out["warning"] = "invalid page size"
        return out
    size = out["kernel_size"]
    if size and page + size <= len(raw):
        out["kernel_offset"] = page
        out["kernel_magic"] = raw[page:page + 8].hex()
    return out


def parse_vendor_boot(raw):
    if not raw.startswith(b"VNDRBOOT") or len(raw) < 2128:
        return None
    version = uint(raw, 8)
    page = uint(raw, 12)
    out = {"header_version": version, "page_size": page,
           "ramdisk_size": uint(raw, 24), "header_size": uint(raw, 2096),
           "dtb_size": uint(raw, 2100),
           "device_name": raw[2080:2096].split(b"\x00")[0].decode("ascii", "replace"),
           "cmdline_hardware_strings": strings_of_interest(raw[28:2076])}
    if version >= 4:
        out["fragment_table_bytes"] = uint(raw, 2112)
        out["fragment_count"] = uint(raw, 2116)
        out["bootconfig_size"] = uint(raw, 2124)
    if 2048 <= page <= 65536 and not page & (page - 1):
        pos = align(out["header_size"], page)
        if pos + out["ramdisk_size"] <= len(raw):
            out["ramdisk_offset"] = pos
            out["ramdisk_prefix"] = raw[pos:pos + 8].hex()
    return out


def parse_dtbo(raw):
    if raw[:4] == bytes.fromhex("d7b7ab1e"):
        byteorder = ">"
    elif raw[:4] == bytes.fromhex("1eabb7d7"):
        byteorder = "<"
    elif raw[:4] == bytes.fromhex("d00dfeed"):
        return {"format": "single FDT", "sha256": digest(raw),
                "strings": strings_of_interest(raw)}
    else:
        return None
    if len(raw) < 32:
        return {"error": "short dtbo header"}
    magic, total, head, stride, count, entries_off, page, version = struct.unpack_from(
        byteorder + "8I", raw, 0)
    obj = {"format": "Android DTBO", "version": version,
           "entry_count": count, "entries": []}
    if count > 256 or stride < 32 or total > len(raw) or entries_off + count * stride > len(raw):
        obj["error"] = "invalid dtbo bounds"
        return obj
    for i in range(count):
        pos = entries_off + i * stride
        length, offset, board_id, rev = struct.unpack_from(byteorder + "4I", raw, pos)
        if length == 0 or offset + length > len(raw):
            obj["entries"].append({"index": i, "error": "invalid overlay bounds"})
            continue
        payload = raw[offset:offset + length]
        obj["entries"].append({
            "index": i, "id": board_id, "revision": rev, "size": length,
            "sha256": digest(payload), "valid_fdt": payload.startswith(bytes.fromhex("d00dfeed")),
            "strings": strings_of_interest(payload, 10)})
    return obj


def unpack_kernel(raw, temp):
    compressors = {
        bytes.fromhex("04224d18"): "lz4",
        bytes.fromhex("02214c18"): "lz4",
        bytes.fromhex("1f8b08"): "gzip",
        bytes.fromhex("fd377a585a00"): "xz"}
    for magic, command in compressors.items():
        if raw.startswith(magic):
            source = temp / "kernel.bin"
            target = temp / "kernel.out"
            source.write_bytes(raw)
            with target.open("wb") as out:
                try:
                    result = subprocess.run([command, "-dc", str(source)], stdout=out,
                                            stderr=subprocess.DEVNULL, timeout=60)
                except (OSError, subprocess.TimeoutExpired):
                    return None, "decompression failed"
            if result.returncode == 0 and target.stat().st_size <= 256 * 1024 * 1024:
                return target.read_bytes(), command
            return None, "decompression failed/too large"
    return raw, "uncompressed or unknown"


def banner(raw):
    if raw is None:
        return None
    m = re.search(rb"Linux version [\x20-\x7e]{6,160}", raw)
    return m.group(0).decode("ascii", "replace") if m else None


def parse_cpio_modules(raw):
    # Never extract paths from an untrusted archive into the filesystem.
    pos, modules = 0, {}
    for _ in range(5000):
        if raw[pos:pos + 6] not in (b"070701", b"070702") or pos + 110 > len(raw):
            break
        try:
            fields = [int(raw[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
        except ValueError:
            break
        size, namesize = fields[6], fields[11]
        if not 0 < namesize < 4096 or size > MAX_IMAGE:
            break
        end_name = pos + 110 + namesize
        if end_name > len(raw):
            break
        name = raw[pos + 110:end_name].strip(b"\x00").decode("utf-8", "replace")
        data_start = align(end_name, 4)
        data_end = data_start + size
        if data_end > len(raw):
            break
        if name == "TRAILER!!!":
            break
        if name.endswith(".ko") and size > 0:
            modules[name] = raw[data_start:data_end]
        pos = align(data_end, 4)
    return modules


def modules_in_vendor(raw, vendor, temp):
    if not vendor or "ramdisk_offset" not in vendor:
        return {}, "vendor ramdisk unreadable"
    start = vendor["ramdisk_offset"]
    chunk = raw[start:start + vendor["ramdisk_size"]]
    found = parse_cpio_modules(chunk)
    label = "raw cpio"
    if not found:
        inflated, label = unpack_kernel(chunk, temp)
        if inflated is not None:
            found = parse_cpio_modules(inflated)
    records = {}
    for name, payload in sorted(found.items()):
        with tempfile.NamedTemporaryFile(dir=temp, suffix=".ko") as f:
            f.write(payload)
            f.flush()
            try:
                p = subprocess.run(["modinfo", "-F", "vermagic", f.name],
                                   capture_output=True, text=True, timeout=3)
                vermagic = p.stdout.strip()[:180] if p.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                vermagic = None
        records[name] = {"sha256": digest(payload), "size": len(payload),
                         "vermagic": vermagic}
    if not records:
        label += " (no modules decoded; split fragments may require another parser)"
    return records, label


def inspect(path, temp):
    raw = path.read_bytes()
    obj = {"name": path.name, "size": len(raw), "sha256": digest(raw),
           "magic": raw[:16].hex()}
    b = parse_boot(raw)
    v = parse_vendor_boot(raw)
    dt = parse_dtbo(raw) if path.name.startswith(("dtbo", "dtb")) else None
    if b:
        obj["boot"] = b
        if "kernel_offset" in b:
            start = b["kernel_offset"]
            unpacked, decoder = unpack_kernel(raw[start:start + b["kernel_size"]], temp)
            obj["kernel_version"] = banner(unpacked)
            obj["kernel_decoder"] = decoder
    if path.name in ("Image", "Image.lz4", "Image.gz"):
        unpacked, decoder = unpack_kernel(raw, temp)
        obj["kernel_version"] = banner(unpacked)
        obj["kernel_decoder"] = decoder
    if v:
        obj["vendor_boot"] = v
        found, mode = modules_in_vendor(raw, v, temp)
        obj["modules"] = found
        obj["module_decoder"] = mode
    if dt:
        obj["dtbo"] = dt
    return obj


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--husky-zip", required=True, type=Path)
    p.add_argument("--husky-sha256", required=True)
    p.add_argument("--shiba-dir", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    opts = p.parse_args()
    opts.out.mkdir(parents=True, exist_ok=True)
    if digest(opts.husky_zip.read_bytes()) != opts.husky_sha256:
        raise SystemExit("FAIL CLOSED: husky archive does not match official release SHA256")
    results = {"status": "STATIC_RESEARCH_NOT_FLASHABLE", "devices": {},
               "husky_origin": "Tensor Linux V1.0 GitHub release SHA256 verified",
               "shiba_origin": "Experimental Google Android16-branch shusky CI; not factory Android17",
               "limitations": ["No device test", "No factory kernel ABI/KMI match",
                               "No GPU, touch, USB display or boot functionality proven"]}
    with tempfile.TemporaryDirectory() as root:
        temp = Path(root)
        hd = temp / "husky"
        hd.mkdir()
        with zipfile.ZipFile(opts.husky_zip) as zf:
            if zf.testzip() is not None:
                raise SystemExit("ZIP CRC failed")
            for member in zf.infolist():
                filename = Path(member.filename).name
                if filename not in HUSKY or member.is_dir():
                    continue
                if member.file_size > MAX_IMAGE:
                    raise SystemExit("unexpected image size: " + filename)
                dest = hd / filename
                if dest.exists():
                    raise SystemExit("duplicate boot image")
                with zf.open(member) as incoming, dest.open("wb") as outgoing:
                    import shutil
                    shutil.copyfileobj(incoming, outgoing)
        if not (hd / "boot_a.img").is_file():
            raise SystemExit("husky boot_a.img not found")
        if not (opts.shiba_dir / "boot.img").is_file():
            raise SystemExit("experimental shiba boot.img not found")
        for model, directory, allow in (("husky", hd, HUSKY),
                                         ("shiba", opts.shiba_dir, SHIBA)):
            results["devices"][model] = {
                file.name: inspect(file, temp)
                for file in sorted(directory.iterdir())
                if file.name in allow and file.is_file() and file.stat().st_size <= MAX_IMAGE}
    h = results["devices"]["husky"]
    s = results["devices"]["shiba"]
    hmods = h.get("vendor_kernel_boot_a.img", {}).get("modules", {})
    smods = s.get("vendor_kernel_boot.img", {}).get("modules", {})
    common = sorted(set(hmods) & set(smods))
    hdt = h.get("dtbo_a.img", {}).get("dtbo", {}).get("entries", [])
    sdt = s.get("dtbo.img", {}).get("dtbo", {}).get("entries", [])
    overlap = {item.get("sha256") for item in hdt if item.get("sha256")} & {
        item.get("sha256") for item in sdt if item.get("sha256")}
    cmp = {
        "husky_kernel_version": h.get("boot_a.img", {}).get("kernel_version"),
        "shiba_kernel_version": s.get("boot.img", {}).get("kernel_version"),
        "husky_dtbo_entry_count": len(hdt), "shiba_dtbo_entry_count": len(sdt),
        "identical_dtbo_payload_hashes": sorted(overlap),
        "husky_module_count_decoded": len(hmods),
        "shiba_module_count_decoded": len(smods),
        "shared_module_names": common,
        "shared_module_vermagic_differences": [
            {"path": n, "husky": hmods[n]["vermagic"], "shiba": smods[n]["vermagic"]}
            for n in common if hmods[n]["vermagic"] and smods[n]["vermagic"]
            and hmods[n]["vermagic"] != smods[n]["vermagic"]]}
    results["comparison"] = cmp
    (opts.out / "U2_METADATA.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = [
        "# Ubuntu U2 — Pixel 8 Pro vs Pixel 8 static research",
        "",
        "**NO DEVICE — NOT BOOTABLE — DO NOT FLASH**",
        "",
        "- Husky: Tensor Linux V1.0 archive, SHA256 matched to GitHub release metadata (not a digital signature).",
        "- Shiba: prior Google shusky CI build from Android16 branch; NOT Android17 factory matched.",
        "- No boot, hardware or ABI compatibility is established.",
        "",
        "## Kernel version strings (None means parser did not find a string)",
        "- husky: " + str(cmp["husky_kernel_version"]),
        "- shiba: " + str(cmp["shiba_kernel_version"]),
        "",
        "## DTBO payloads",
        "- husky entries: " + str(cmp["husky_dtbo_entry_count"]),
        "- shiba entries: " + str(cmp["shiba_dtbo_entry_count"]),
        "- identical entry SHA256 digests: " + str(len(overlap)),
        "",
        "## Vendor ramdisk modules",
        "- husky successfully decoded: " + str(len(hmods)),
        "- shiba successfully decoded: " + str(len(smods)),
        "- common module paths: " + str(len(common)),
        "- common modules with different vermagic: " + str(len(cmp["shared_module_vermagic_differences"])),
        "",
        "Zero modules decoded does NOT prove the ramdisk contains no kernel modules.",
        "Android v4 split-vendor-ramdisk parsing may need further work.",
        "",
        "## Next validation",
        "- Review JSON for exact boot headers, per-image hashes, DTBO overlays, vermagic.",
        "- Examine shiba factory Android17 vendor modules and matching kernel KMI.",
        "- Determine shiba-specific display, input, external display and power architecture.",
        "",
        "Research code never calls adb, fastboot, boot-image packers or flash tools."
    ]
    (opts.out / "U2_REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
