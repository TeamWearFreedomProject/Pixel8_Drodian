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


def patch_bcm4398_wifi_local_min(src, out):
    """Keep Pixel 8 Broadcom Wi-Fi enabled; rename ONE obsolete local MIN only.

    Narrow, source-checked revision avoids changing generic GKI minmax, driver
    logic, any other WLAN files, or weakening strict compiler diagnostics.
    """
    wlan=src/"private/google-modules/wlan/bcm4398"
    file=wlan/"wb_regon_coordinator.c"
    if not file.is_file():
        abort("bcm4398 WB regon coordinator file missing")
    text=file.read_text()
    definitions=re.findall(
        r"(?m)^[ \t]*#[ \t]*define[ \t]+MIN[ \t]*\([^ \r\n]*[^\r\n]*$",
        text)
    if len(definitions)!=1:
        abort("expected exactly one local bcm4398 MIN macro definition")
    old_def=definitions[0]
    normalized=re.sub(r"\s+","",old_def)
    expected="#defineMIN(a,b)(((a)<(b))?(a):(b))"
    if normalized!=expected:
        abort("Wi-Fi MIN macro does not match actual previous compiler diagnostic: "+normalized)
    linux_minmax=(src/"aosp/include/linux/minmax.h").read_text()
    if not re.search(r"(?m)^[ \t]*#[ \t]*define[ \t]+MIN[ \t]*\([ \t]*a[ \t]*,[ \t]*b[ \t]*\)",linux_minmax):
        abort("upstream GKI MIN macro missing; source revision unknown")
    oldsha=sha(file)
    original_count=len(re.findall(r"\bMIN[ \t]*\(",text))
    if original_count<1:
        abort("bcm4398 MIN definition/use inventory empty")
    renamed_name="BCM4398_REGON_LOCAL_MIN"
    updated,count=re.subn(r"\bMIN(?=[ \t]*\()",renamed_name,text)
    # The original Google source may use tabs or multiple spaces between
    # preprocessor tokens. Match the *token*, not a guessed single-space
    # serialization such as "#define BCM4398_...".
    new_definitions=re.findall(
        r"(?m)^[ \t]*#[ \t]*define[ \t]+BCM4398_REGON_LOCAL_MIN(?=[ \t(])",
        updated)
    if count!=original_count or len(new_definitions)!=1:
        abort("Wi-Fi MIN definition or usage not changed uniquely")
    if re.search(r"\bMIN[ \t]*\(",updated):
        abort("Wi-Fi local MIN collision still present after patch")
    file.write_text(updated)
    diff=subprocess.run(
        ["git","-C",str(wlan),"diff","--","wb_regon_coordinator.c"],
        capture_output=True,text=True,check=True)
    deleted_old=re.search(
        r"(?m)^-[ \t]*#[ \t]*define[ \t]+MIN(?=[ \t(])",diff.stdout)
    added_new=re.search(
        r"(?m)^\+[ \t]*#[ \t]*define[ \t]+BCM4398_REGON_LOCAL_MIN(?=[ \t(])",
        diff.stdout)
    if not (deleted_old and added_new):
        abort("missing inspectable bcm4398 macro declaration diff")
    (out/"U28_BCM4398_WIFI_MIN_SOURCE_DIFF.txt").write_text(diff.stdout)
    info={
        "status":"BCM4398_WIFI_MIN_COLLISION_GUARDED_LOCAL_RENAME_CI_ONLY",
        "path":"private/google-modules/wlan/bcm4398/wb_regon_coordinator.c",
        "original_source_sha256":oldsha,
        "patched_source_sha256":sha(file),
        "local_macro_replacements":count,
        "wifi_bcm4398_driver_disabled":False,
        "uwb_updater_disabled":False,
        "GKI_minmax_h_changed":False,
        "source_tree_modified_only_for_diagnostic_build":True,
        "real_device_flash_gate":"DENY"
    }
    (out/"U28_BCM4398_WIFI_MIN_PATCH.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps(info,indent=2))


def inventory_other_legacy_minmax(src, out):
    """Inventory remaining likely conflicts; no speculative source rewrites."""
    root=src/"private/google-modules"
    examples=[]
    pattern=re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+(MIN|MAX)[ \t]*\(")
    for file in sorted(root.rglob("*")):
        if not file.is_file() or file.suffix not in (".c",".h"):
            continue
        try:
            data=file.read_text(errors="replace")
        except OSError:
            abort("unable to audit source file: "+str(file))
        for hit in pattern.finditer(data):
            examples.append({
                "file":str(file.relative_to(src)),
                "macro":hit.group(1),
                "line":data.count("\n",0,hit.start())+1
            })
    (out/"U28_OTHER_LOCAL_MINMAX_DEFINITIONS.json").write_text(
        json.dumps({
            "remaining_local_MINMAX_definitions":len(examples),
            "locations_for_future_individual_source_review":examples,
            "any_automatic_global_macro_rewrites":False,
            "pixel8_boot_flash_gate":"DENY"
        },indent=2)+"\n")
    print("Other potential MIN/MAX name collisions inventoried:",len(examples))


def patch_mali_gpu_minmax_compat(src, out):
    """Apply explicit Linux minmax support to one pinned-form GPU header.

    Keep the actual Mali GPU module, all other driver code and -Werror.
    This research-only API adaptation may have behavioral differences from
    legacy macros; a successful compile alone does not establish safe GPU use.
    """
    gpu=src/"private/google-modules/gpu"
    header=gpu/"mali_kbase/mali_malisw.h"
    if not header.is_file():
        abort("Expected Mali GPU header missing")
    text=header.read_text()
    min_line="#define MIN(x, y) ((x) < (y) ? (x) : (y))"
    max_line="#define MAX(x, y) ((x) < (y) ? (y) : (x))"
    if text.count(min_line)!=1 or text.count(max_line)!=1:
        abort("Mali min/max macro implementations no longer match observed compiler error")
    if text.count("#define _MALISW_H_")!=1:
        abort("Mali header include guard unexpected")
    generic=(src/"aosp/include/linux/minmax.h").read_text()
    for name in ("MIN","MAX"):
        if not re.search(
            r"(?m)^[ \t]*#[ \t]*define[ \t]+"+name+
            r"[ \t]*\([ \t]*a[ \t]*,[ \t]*b[ \t]*\)",generic
        ):
            abort("New GKI "+name+" macro not found; refuse to change GPU")
    if "#include <linux/minmax.h>" in text or "#ifndef MIN" in text:
        abort("GPU header was already minmax-integrated; review before reapplying")

    # For kernel builds, guarantee the new GKI definitions exist before
    # GPU C code loads this header; non-kernel users retain older macros.
    updated=text.replace(
        "#define _MALISW_H_",
        "#define _MALISW_H_\n\n"
        "/* U28 research-only: use kernel MIN/MAX in __KERNEL__ builds. */\n"
        "#ifdef __KERNEL__\n"
        "#include <linux/minmax.h>\n"
        "#endif",1
    )
    updated=updated.replace(
        min_line,"#ifndef MIN\n"+min_line+"\n#endif",1
    ).replace(
        max_line,"#ifndef MAX\n"+max_line+"\n#endif",1
    )
    if updated.count("#include <linux/minmax.h>")!=1 or updated.count("#ifndef MIN")!=1 or updated.count("#ifndef MAX")!=1:
        abort("Mali macro protection edit did not apply exactly once")
    if updated.count(min_line)!=1 or updated.count(max_line)!=1:
        abort("Mali legacy fallback must be retained exactly")
    before=sha(header)
    header.write_text(updated)
    diff=subprocess.run(
        ["git","-C",str(gpu),"diff","--","mali_kbase/mali_malisw.h"],
        capture_output=True,text=True,check=True
    )
    if "<linux/minmax.h>" not in diff.stdout or "+#ifndef MIN" not in diff.stdout or "+#ifndef MAX" not in diff.stdout:
        abort("Mali expected source-only compatibility change not visible in Git diff")
    (out/"U28_MALI_GPU_MINMAX_SOURCE_DIFF.txt").write_text(diff.stdout)
    report={
        "status":"U28_RESEARCH_ONLY_MALI_GPU_GKI_MINMAX_HEADER_ADAPTATION",
        "source_path":"private/google-modules/gpu/mali_kbase/mali_malisw.h",
        "source_original_SHA256":before,
        "source_updated_SHA256":sha(header),
        "source_legacy_min_max_definitions_preserved_for_non_kernel":True,
        "kernel_will_resolve_GKI_minmax_first":True,
        "new_GKI_minmax_semantics_may_differ_from_old_Mali_macros":True,
        "GPU_module_disabled":False,
        "Linux_kernel_header_modified":False,
        "GPU_runtime_or_module_KMI_compatibility_verified":False,
        "physical_pixel8_tested":False,
        "real_device_flash_gate":"DENY",
    }
    (out/"U28_MALI_GPU_MINMAX_PATCH.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


def patch_goodix_touch_local_max(src, out):
    """Review all Goodix local MIN/MAX definitions; patch only two proven MAX's.

    Both Goodix inspection and proc had the *same* compiler failure at
    source line 123 / 102 respectively in U28 runs 8 and 9. Retain all touch
    functionality and error checking; do not blanket replace macros.
    """
    module_dir=src/"private/google-modules/touch/goodix"
    if not module_dir.is_dir():
        abort("Goodix touch module source missing")
    common=(src/"aosp/include/linux/minmax.h").read_text()
    if not re.search(
        r"(?m)^[ \t]*#[ \t]*define[ \t]+MAX[ \t]*\([ \t]*a[ \t]*,[ \t]*b[ \t]*\)",
        common
    ):
        abort("new GKI MAX definition absent; cannot verify conflict")

    # Early inventory means an unexpected third conflict fails BEFORE another
    # expensive real kernel build instead of hiding the collision.
    macro_re=re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+(MIN|MAX)[ \t]*\([^\r\n]*$")
    candidates={}
    for file in sorted(module_dir.rglob("*")):
        if file.is_file() and file.suffix in (".c",".h"):
            body=file.read_text(errors="replace")
            found=[{"macro":m.group(1),"definition":m.group(0).strip()}
                   for m in macro_re.finditer(body)]
            if found:
                candidates[str(file.relative_to(module_dir))]=found

    (out/"U28_GOODIX_ALL_LOCAL_MINMAX_DEFS.json").write_text(
        json.dumps({"definitions_before_patch":candidates,
                    "globally_rewritten":False,
                    "real_device_flash_gate":"DENY"},indent=2)+"\n"
    )
    target_names=("goodix_ts_inspect.c","goodix_ts_proc.c")
    if set(candidates)!=set(target_names):
        abort("unexpected Goodix MIN/MAX definition files: "+repr(candidates))
    expected="#defineMAX(a,b)((a>b)?a:b)"
    for name in target_names:
        definitions=candidates[name]
        if len(definitions)!=1 or definitions[0]["macro"]!="MAX":
            abort("unexpected Goodix MIN/MAX definition count: "+name)
        if re.sub(r"\s+","",definitions[0]["definition"])!=expected:
            abort("unexpected Goodix MAX semantics in "+name)

    changes=[]
    for name in target_names:
        source=module_dir/name
        before=source.read_text()
        local_name={
            "goodix_ts_inspect.c":"GOODIX_INSPECT_LOCAL_MAX",
            "goodix_ts_proc.c":"GOODIX_PROC_LOCAL_MAX",
        }[name]
        if local_name in before:
            abort("Goodix local macro already renamed: "+name)
        count_before=len(re.findall(r"\bMAX(?=[ \t]*\()",before))
        if count_before<1:
            abort("Goodix MAX definition absent from "+name)
        after,count=re.subn(r"\bMAX(?=[ \t]*\()",local_name,before)
        new_defs=re.findall(
            r"(?m)^[ \t]*#[ \t]*define[ \t]+"+local_name+r"(?=[ \t(])",
            after
        )
        if count!=count_before or len(new_defs)!=1:
            abort("Goodix macro rewrite failed exact token-count check: "+name)
        if re.search(r"\bMAX(?=[ \t]*\()",after):
            abort("Goodix old MAX still found: "+name)
        previous=sha(source)
        source.write_text(after)
        diff=subprocess.run(["git","-C",str(module_dir),"diff","--",name],
                            text=True,capture_output=True,check=True)
        old_decl=re.search(
            r"(?m)^-[ \t]*#[ \t]*define[ \t]+MAX(?=[ \t(])",diff.stdout
        )
        new_decl=re.search(
            r"(?m)^\+[ \t]*#[ \t]*define[ \t]+"+local_name+r"(?=[ \t(])",
            diff.stdout
        )
        if not (old_decl and new_decl):
            abort("Goodix source diff failed review: "+name)
        (out/("U28_GOODIX_"+name+"_DIFF.txt")).write_text(diff.stdout)
        changes.append({
            "path":"private/google-modules/touch/goodix/"+name,
            "original_SHA256":previous,
            "patched_SHA256":sha(source),
            "legacy_macro": "MAX",
            "local_name":local_name,
            "definition_and_uses_renamed":count,
        })
    combined=subprocess.run(
        ["git","-C",str(module_dir),"diff","--",
         "goodix_ts_inspect.c","goodix_ts_proc.c"],
        text=True,capture_output=True,check=True
    )
    (out/"U28_GOODIX_TOUCH_MAX_SOURCE_DIFF.txt").write_text(combined.stdout)
    report={
        "status":"U28_GOODIX_INSPECT_AND_PROC_LOCAL_MAX_RENAME_IN_CI_ONLY",
        "source_files_changed":changes,
        "all_local_goodix_min_max_definitions_audited":True,
        "touchscreen_module_disabled":False,
        "GPU_WiFi_USB_watchdog_UWB_battery_modules_disabled":False,
        "compiler_warning_suppressed":False,
        "gki_header_modified":False,
        "physical_touch_functionality_verified":False,
        "KMI_6_1_124_vs_6_1_157_resolved":False,
        "real_device_flash_gate":"DENY",
    }
    (out/"U28_GOODIX_TOUCH_MAX_PATCH.json").write_text(
        json.dumps(report,indent=2)+"\n"
    )
    print(json.dumps(report,indent=2))


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
        "some_local_MIN_macro_collision_reappeared":("'MIN' macro redefined" in t),
        "Goodix_TOUCH_MAX_macro_collision_reappeared":("goodix_ts_inspect.c" in t and "MAX" in t and "macro redefined" in t),
        "Mali_GPU_minmax_macro_collision_reappeared":("mali_malisw.h" in t and "macro redefined" in t),
        "bcm4398_regon_coordinator_MIN_collision_reappeared":("'MIN' macro redefined" in t and "wb_regon_coordinator.c" in t),
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
        patch_bcm4398_wifi_local_min(a.src,a.out)
        inventory_other_legacy_minmax(a.src,a.out)
        patch_mali_gpu_minmax_compat(a.src,a.out)
        patch_goodix_touch_local_max(a.src,a.out)
    else:audit(a.src,a.out,a.exit_code)
if __name__=="__main__":main()
