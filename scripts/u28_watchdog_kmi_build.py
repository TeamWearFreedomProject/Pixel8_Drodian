#!/usr/bin/env python3
"""U28 tightly scoped CI-only watchdog VLA repair and honest build audit.

This never builds flashable firmware or disables USB, watchdog, ABI or
warnings. Any unexpected source revision or unexpected compiler behavior
must fail closed and be logged for manual review.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

GKI = "bd23337e42e794964a89f47596daf1209a25ee1a"
SOC = "057ab18a9cc0e318538b419eafc565a7fbe1d320"
STOCK = "6.1.157-android14-11-gbd23337e42e7-ab14791245"
WDT_REL = "private/google-modules/soc/gs/drivers/watchdog/s3c2410_wdt.c"
BEFORE = "char buf[max(NR_CPUS, PRINT_CPUS_LIMIT)];"
AFTER = "char buf[(NR_CPUS > PRINT_CPUS_LIMIT) ? NR_CPUS : PRINT_CPUS_LIMIT];"

def abort(msg):
    raise SystemExit("U28 fail-closed: " + msg)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()

def pin_git(repo, expected):
    p=subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],
                     capture_output=True,text=True,check=True)
    if p.stdout.strip()!=expected:
        abort("unexpected official source revision for "+str(repo))

def patch(src, report, out):
    pin_git(src/"aosp",GKI)
    pin_git(src/"private/google-modules/soc/gs",SOC)
    evidence=json.loads(report.read_text())
    if evidence.get("status")!="U27_REPRODUCIBLE_WATCHDOG_SOURCE_AND_KMI_DIAGNOSIS_PASS":
        abort("U27 source provenance not passed")
    expected=evidence["source_watchdog_sha256"]
    wdt=src/WDT_REL
    if sha(wdt)!=expected:
        abort("Zuma watchdog file differs from independently pinned U27 source")
    text=wdt.read_text()
    if text.count(BEFORE)!=1 or AFTER in text:
        abort("watchdog VLA patch anchor not unique or already patched")
    updated=text.replace(BEFORE,AFTER,1)
    wdt.write_text(updated)
    if updated.count(AFTER)!=1 or text.count(BEFORE)!=1:
        abort("watchdog patch mismatch")
    out.mkdir(parents=True,exist_ok=True)
    info={
        "status":"U28_REVIEWABLE_WATCHDOG_SOURCE_PATCH_APPLIED_TO_CI_ONLY",
        "gki_git_sha":GKI,"soc_git_sha":SOC,
        "old_exact_source_sha256":expected,
        "patched_source_sha256":sha(wdt),
        "source_file":WDT_REL,
        "old_expression":BEFORE,"new_expression":AFTER,
        "watchdog_function_kept":True,
        "usb_DWC3_module_kept":True,
        "modpost_and_werror_kept_enabled":True,
        "real_device_flash_gate":"DENY"
    }
    (out/"U28_WATCHDOG_PATCH.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps(info,indent=2))

def patch_bms_legacy_max(src, out):
    """Rename ONLY the local legacy MAX macro, preserving battery code.

    The modern GKI provides MAX() from include/linux/minmax.h. The old BMS
    module declares another MAX() with overlapping semantics; redefining it
    is a fatal -Werror. Do not change driver logic or GKI headers.
    """
    bmsroot=src/"private/google-modules/bms"
    battery=bmsroot/"google_dual_batt_gauge.c"
    if not battery.is_file():
        abort("pinned Google BMS source file missing")
    code=battery.read_text()
    old_define=re.compile(
        r"(?m)^([ \t]*#[ \t]*define[ \t]+)MAX([ \t]*\([ \t]*x[ \t]*,[ \t]*y[ \t]*\)[ \t]*"
        r"\(\(x\)[ \t]*<[ \t]*\(y\)[ \t]*\?[ \t]*\(y\)[ \t]*:[ \t]*\(x\)\)[ \t]*)$")
    if len(old_define.findall(code))!=1:
        abort("BMS MAX definition does not match source-verified two-input comparison")
    upstream=(src/"aosp/include/linux/minmax.h").read_text()
    if not re.search(r"(?m)^[ \t]*#[ \t]*define[ \t]+MAX[ \t]*\([ \t]*a[ \t]*,[ \t]*b[ \t]*\)", upstream):
        abort("modern GKI MAX(a,b) unexpectedly missing")
    prior_sha=sha(battery)
    old_uses=len(re.findall(r"\bMAX[ \t]*\(",code))
    new_name="GBMS_DUAL_BATT_LOCAL_MAX"
    revised,n=re.subn(r"\bMAX(?=[ \t]*\()",new_name,code)
    if old_uses<1 or n!=old_uses:
        abort("BMS macro usage/definition count unexpected")
    if re.search(r"\bMAX[ \t]*\(",revised) or revised.count("#define "+new_name)!=1:
        abort("BMS legacy MAX declaration not fully isolated")
    battery.write_text(revised)
    evidence={
        "status":"BMS_LOCAL_MACRO_RENAMED_IN_DISPOSABLE_CI_ONLY",
        "path":"private/google-modules/bms/google_dual_batt_gauge.c",
        "official_source_before_sha256":prior_sha,
        "patched_source_sha256":sha(battery),
        "original_legacy_macro_definition_count":1,
        "local_macro_replacements":n,
        "GKI_linux_minmax_header_unchanged":True,
        "battery_function_logic_changed":False,
        "battery_module_disabled":False,
        "watchdog_and_internal_USB_kept":True,
        "real_device_flash_gate":"DENY",
    }
    (out/"U28_BMS_MAX_MACRO_PATCH.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))


def patch_uwb_local_min(src, out):
    """Resolve *only* fwupdater.c's private MIN symbol vs modern Linux MIN.

    This keeps the UWB updater compiled and never overwrites kernel minmax.h.
    A source layout or behavior change is a hard stop, not an excuse to disable
    UWB or relax -Wmacro-redefined checks.
    """
    uwbdir=src/"private/google-modules/uwb/qorvo/qm35/qm35s"
    file=uwbdir/"libfwupdater/src/fwupdater.c"
    if not file.is_file():
        abort("expected Google/Qorvo fwupdater source was not synced")
    body=file.read_text()
    signature="#define MIN(a, b) ((a) < (b) ? (a) : (b))"
    if body.count(signature)!=1:
        abort("UWB updater MIN definition differs from observed U28 compiler log")
    modern=(src/"aosp/include/linux/minmax.h").read_text()
    if not re.search(r"(?m)^[ \t]*#[ \t]*define[ \t]+MIN[ \t]*\([ \t]*a[ \t]*,[ \t]*b[ \t]*\)",modern):
        abort("expected GKI MIN(a, b) is not present")
    before_sha=sha(file)
    oldcalls=len(re.findall(r"\bMIN[ \t]*\(",body))
    if oldcalls<1:
        abort("no MIN definition/use found in UWB updater")
    name="QM35_FWUPDATER_LOCAL_MIN"
    rewritten,count=re.subn(r"\bMIN(?=[ \t]*\()",name,body)
    if count!=oldcalls or rewritten.count("#define "+name)!=1:
        abort("local UWB MIN substitution was incomplete")
    if re.search(r"\bMIN[ \t]*\(",rewritten):
        abort("legacy UWB MIN would still collide with modern GKI")
    file.write_text(rewritten)
    (out/"U28_UWB_MIN_MACRO_PATCH.json").write_text(json.dumps({
        "status":"UWB_LOCAL_MIN_RENAMED_IN_ISOLATED_CI_ONLY",
        "source_path":"private/google-modules/uwb/qorvo/qm35/qm35s/libfwupdater/src/fwupdater.c",
        "old_SHA256":before_sha,
        "new_SHA256":sha(file),
        "macro_replacements":count,
        "uwb_firmware_updater_disabled":False,
        "battery_module_disabled":False,
        "usb_soc_and_watchdog_disabled":False,
        "GKI_minmax_h_untouched":True,
        "real_device_flash_gate":"DENY"
    },indent=2)+"\n")
    # Capture exactly the single UWB source change as part of the run evidence.
    diff=subprocess.run(
        ["git","-C",str(uwbdir),"diff","--","libfwupdater/src/fwupdater.c"],
        capture_output=True,text=True,check=True)
    if "QM35_FWUPDATER_LOCAL_MIN" not in diff.stdout:
        abort("no inspectable UWB updater source diff; stopping")
    (out/"U28_UWB_MIN_SOURCE_DIFF.txt").write_text(diff.stdout)
    print("U28 UWB MIN: guarded local macro rename applied, with reviewed diff")


def scan_version(image):
    if not image.is_file():return None
    before=b""
    with image.open("rb") as f:
        while True:
            block=f.read(1024*1024)
            if not block: break
            m=re.search(rb"Linux version (6\.1\.[^\x00\s]+)",before+block)
            if m:return m.group(1).decode("ascii","replace")
            before=block[-512:]
    return None

def audit(src, out, rc):
    log=out/"U28_FULL_BUILD.log"
    if not log.is_file() or log.stat().st_size==0:
        abort("true Bazel compiler output log not found")
    original=json.loads((out/"U28_WATCHDOG_PATCH.json").read_text())
    if original["real_device_flash_gate"]!="DENY":
        abort("source patch guard changed")
    t=log.read_text(errors="replace")
    dist=src/"out/shusky/dist"
    image=dist/"Image"
    images={}
    for name in ("Image","Image.gz","Image.lz4","boot.img","dtbo.img",
                 "vendor_dlkm.img","system_dlkm.img","vendor_kernel_boot.img"):
        f=dist/name
        if f.is_file():images[name]={"bytes":f.stat().st_size,"sha256":sha(f)}
    version=scan_version(image)
    errors={
        "KMI_6_1_124_provider_mismatch":(
            "KMI or sublevel mismatch before running make modules_install" in t and
            "6.1.124-android14-11" in t),
        "watchdog_VLA_reappeared":("variable length array used" in t and "s3c2410_wdt" in t),
        "DWC3_macro_collision_reappeared":("'DWC3_LLUCTL' macro redefined" in t),
        "BMS_legacy_MAX_macro_collision_reappeared":("'MAX' macro redefined" in t),
        "UWB_fwupdater_MIN_macro_collision_reappeared":("\'MIN\' macro redefined" in t),
        "RTL8150_usb_helper_error_reappeared":('usb_check_int_endpoints' in t and 'undefined' in t),
    }
    succeeded=rc==0 and image.is_file() and version is not None
    status="U28_RESEARCH_COMPILE_PASS_NOT_CP2A_FIRMWARE" if succeeded else "U28_REAL_COMPILE_FAILED_LOG_PRESERVED"
    report={
        "status":status,"real_bazel_exit_code":rc,
        "source_common_commit":GKI,"source_soc_commit":SOC,
        "build_command_uses_local_source_only":True,
        "source_patch_diagnostic_only":True,
        "actual_built_kernel_release":version,
        "exact_stock_cp2a_kernel_release":STOCK,
        "kernel_release_equal_stock":version==STOCK,
        "compiler_diagnostics":errors,
        "generated_image_identifiers_HASH_ONLY":images,
        "actual_prebuilt_provider_resolved_binary_sha256_verified":False,
        "real_CP2A_signed_boot_equivalence":False,
        "pixel8_shiba_module_symbol_crc_verified":False,
        "pixel8_DTBO_panel_GPU_touch_USB_verified":False,
        "pixel8_ubuntu_booted":False,
        "on_device_rollback_AVB_verified":False,
        "physical_pixel8_modified":False,
        "safe_to_flash":False,"real_device_flash_gate":"DENY"
    }
    (out/"U28_SOURCE_BUILD_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    md=["# U28 — source-only 6.1.157 GKI + shiba diagnostic rebuild","",
        f"**{status}; REAL DEVICE FLASH GATE: DENY**","",
        f"- Actual Bazel exit: **{rc}**.",
        f"- Actual Image release: \`{version or 'NOT GENERATED'}\`.",
        "- The old optional USB RTL8150 is excluded with user approval.",
        "- Integrated DWC3 and watchdog kept; vendor-local source adaptations applied.",
        "- GKI source git HEAD pinned but KMI provider resolution still requires",
        "  explicit ABI verification, even if compilation succeeds.",
        "","## Recurring build errors"]
    md += [f"- {k}: {v}" for k,v in errors.items()]
    md += ["","## Built files SHA256, not for device"]
    md += [f"- {k}: {v['sha256']} ({v['bytes']} bytes)" for k,v in images.items()]
    md += ["","No Pixel phone boot, no signed stock firmware equivalence,",
           "no AVB/rollback review, no DTBO runtime test, no host-to-device writes.",
           "This project never authorizes flash or booting the CI images."]
    (out/"U28_SOURCE_BUILD_REPORT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="op",required=True)
    for name in ("patch","audit"):
        p=sub.add_parser(name)
        p.add_argument("--src",type=Path,required=True)
        p.add_argument("--out",type=Path,required=True)
        if name=="patch":p.add_argument("--u27",type=Path,required=True)
        else:p.add_argument("--exit-code",type=int,required=True)
    a=ap.parse_args()
    if a.op=="patch":
        patch(a.src,a.u27,a.out)
        patch_bms_legacy_max(a.src,a.out)
        patch_uwb_local_min(a.src,a.out)
    else:audit(a.src,a.out,a.exit_code)
if __name__=="__main__":main()
