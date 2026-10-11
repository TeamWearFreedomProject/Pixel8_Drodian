#!/usr/bin/env python3
"""U27: independent audit of U25 compiler and upstream watchdog source.

Audit is read-only, does not construct deployable firmware, and never turns
kernel-version or CI success into permission to boot/flash the Pixel 8.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

GKI = "bd23337e42e794964a89f47596daf1209a25ee1a"
SOC = "057ab18a9cc0e318538b419eafc565a7fbe1d320"
STOCK = "6.1.157-android14-11-gbd23337e42e7-ab14791245"

def need(ok, reason):
    if not ok:
        raise SystemExit("U27 AUDIT FAIL CLOSED: " + reason)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    for key in ("u25", "u24", "watchdog", "bazelrc", "out"):
        ap.add_argument("--" + key, type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    prior = json.loads((a.u24 / "U24_PROVIDER_AUDIT.json").read_text())
    need(prior["status"] == "U24_OFFICIAL_PINNED_SOURCE_PROVIDER_AND_DWC3_COLLISION_CONFIRMED",
         "U24 Google pin report not verified")
    need(prior["source_pin_commits"]["kernel/common"] == GKI, "GKI pin drift")
    need(prior["source_pin_commits"]["kernel/google-modules/soc/gs"] == SOC, "SoC pin drift")
    need(sha(a.bazelrc) == prior["file_sha256"]["device_bazelrc"], "Google Bazelrc not pinned to U24 bytes")
    wdt = a.watchdog.read_text()
    need(wdt.count("char buf[max(NR_CPUS, PRINT_CPUS_LIMIT)];") == 1,
         "watchdog source differs from U25 failure, do not invent patch")
    need("PRINT_CPUS_LIMIT" in wdt and "NR_CPUS" in wdt,
         "watchdog constant bounds missing")
    logs = (a.u25 / "U25_BUILD_TAIL.log").read_text(errors="replace")
    needed = [
        "KMI or sublevel mismatch before running make modules_install",
        "6.1.157-android14-11",
        "6.1.124-android14-11",
        "variable length array used",
        "s3c2410_wdt.c",
    ]
    for fragment in needed:
        need(fragment in logs, "U25 binary build log missing " + fragment)
    need("DWC3_LLUCTL' macro redefined" not in logs,
         "DWC3 driver rename possibly regressed")
    source_patch = json.loads((a.u25 / "U25_RESEARCH_SOURCE_PATCH.json").read_text())
    need(source_patch["official_source_pins"]["kernel/common"] == GKI, "source pin inconsistent")
    need(source_patch["internal_DWC3_exynos_controller_kept_enabled"],
         "core USB controller must not be removed")
    need(source_patch["real_device_flash_gate"] == "DENY", "U25 safety flag drift")
    buildrc = int((a.u25 / "U25_BUILD_EXIT.txt").read_text().strip())
    need(buildrc != 0, "U25 baseline expected a known failure; inspect before continuing")

    bazelrc = a.bazelrc.read_text()
    need("build --use_prebuilt_gki=true" in bazelrc, "default prebuilt dependency unknown")
    need("build:use_source_tree_aosp --kernel_package=@//aosp" in bazelrc,
         "expected old Google source selection config missing")

    report = {
        "status": "U27_REPRODUCIBLE_WATCHDOG_SOURCE_AND_KMI_DIAGNOSIS_PASS",
        "pinned_gki_sha": GKI,
        "pinned_zuma_soc_sha": SOC,
        "u25_compiler_exit_code": buildrc,
        "u25_compiler_errors_verified": {
            "watchdog_vla_under_werror": True,
            "kmi_6_1_157_vs_6_1_124_warning_or_error": True,
            "internal_USB_controller_enabled": True
        },
        "source_watchdog_sha256": sha(a.watchdog),
        "reviewed_watchdog_expression": "max(NR_CPUS, PRINT_CPUS_LIMIT)",
        "u28_candidate_rewrite": "(NR_CPUS > PRINT_CPUS_LIMIT ? NR_CPUS : PRINT_CPUS_LIMIT)",
        "rewrite_would_keep_original_array_bound_math": True,
        "u28_must_compile_to_verify_this_rewrite": True,
        "upstream_kmi_check_may_log_warning_without_fatal_exit": True,
        "requires_real_bazel_provider_resolution": True,
        "CP2A_production_abi_verified": False,
        "shiba_dtbo_panel_usb_runtime_verified": False,
        "physical_pixel8_modified": False,
        "safe_to_flash": False,
        "real_device_flash_gate": "DENY"
    }
    (a.out/"U27_KMI_WATCHDOG_DIAGNOSIS.json").write_text(json.dumps(report,indent=2)+"\n")
    rows = [
        "# U27 — 6.1.157 shusky watchdog VLA and Bazel provider audit",
        "",
        "**OFFICIAL SOURCE + REAL U25 COMPILER LOG VERIFIED. NO REAL DEVICE TEST.**",
        "",
        f"- CP2A stock kernel: \`{STOCK}\`.",
        f"- Official common Git pin: \`{GKI}\`.",
        f"- Zuma watchdog source Git pin: \`{SOC}\`.",
        "- U25's external USB RTL8150 exclusion and internal USB DWC3 name adaptation were retained.",
        "- U25 compiled to a *different* blocker: Linux max() inside watchdog array bound",
        "  triggers compiler variable length array under -Werror,-Wvla.",
        "- Proposed U28 **source-only** diagnostic: replace exactly one matching",
        "  watchdog array bound with a compile-time ternary (same NR_CPUS and",
        "  PRINT_CPUS_LIMIT arithmetic), without disabling watchdog or global -Werror.",
        "- U25 also reports mismatched 6.1.157 device release and 6.1.124 base",
        "  provider; upstream Kleaf variants may only WARN before module install.",
        "  Merely observing that line does not independently prove a prebuilt binary",
        "  was installed: U28 must capture effective Bazel args and provider evidence.",
        "- A compiler PASS cannot establish Pixel bootability, AVB or ABI.",
        "",
        "**REAL DEVICE FLASH GATE: DENY**",
    ]
    (a.out/"U27_KMI_WATCHDOG_DIAGNOSIS.md").write_text("\n".join(rows)+"\n")
    print("\n".join(rows))

if __name__=="__main__":
    main()
