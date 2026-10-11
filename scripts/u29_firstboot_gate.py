#!/usr/bin/env python3
"""U29 first-boot preflight: combine *real* CI provenance, deny physical flash.

This is a negative safety gate, not a recipe for bypassing AVB, or a Pixel 8
boot-image packager. It never touches the phone. Every unknown fails closed.
"""
import argparse
import json
from pathlib import Path

GKI_SHA = "bd23337e42e794964a89f47596daf1209a25ee1a"
STOCK_CP2A = "6.1.157-android14-11-gbd23337e42e7-ab14791245"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def demand(ok,reason):
    if not ok:
        raise SystemExit("U29 FAIL CLOSED: "+reason)

def main():
    p=argparse.ArgumentParser()
    for s in ("u18","u19","u20","u23","u24","u26","u27","u28workflow","out"):
        p.add_argument("--"+s,type=Path,required=True)
    p.add_argument("--u28report",type=Path)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    reports={s:load(getattr(a,s)) for s in
             ("u18","u19","u20","u23","u24","u26","u27")}
    u28workflow=load(a.u28workflow)
    u28report=load(a.u28report) if a.u28report and a.u28report.is_file() else None

    expect_status={
        "u19":"U19_OFFLINE_BINARY_ABI_AUDIT_PASS_INTEGRATION_BLOCKED",
        "u20":"U20_OFFLINE_ASSET_INTEGRITY_AND_INIT_HANDOFF_AUDIT_PASS",
        "u23":"PASS_QEMU_GUEST_U20_REBUILT_INIT_TO_UBUNTU_SYSTEMD",
        "u24":"U24_OFFICIAL_PINNED_SOURCE_PROVIDER_AND_DWC3_COLLISION_CONFIRMED",
        "u26":"U26_NEGATIVE_BOOT_SAFETY_TESTS_PASS_PHYSICAL_BOOT_DENIED",
        "u27":"U27_REPRODUCIBLE_WATCHDOG_SOURCE_AND_KMI_DIAGNOSIS_PASS",
    }
    for name, state in expect_status.items():
        demand(reports[name]["status"]==state,"invalid "+name+" source report status")
    demand(reports["u18"]["observed_commit"]==GKI_SHA,"CP2A upstream GKI SHA drift")
    demand(reports["u18"]["real_device_flash_gate"]=="DENY","U18 gate missing")
    demand(reports["u19"]["safe_to_combine_U17_modules_with_U18_GKI"] is False,
           "old incompatible modules marked safe")
    demand(reports["u20"]["physical_pixel8_modified"] is False,
           "unexpected physical device use in U20")
    demand(reports["u23"]["pixel8_real_hardware_kernel_booted"] is False,
           "VM wrongly classified as physical hardware")
    demand(reports["u26"]["safe_to_flash_pixel8"] is False,
           "U26 flash authorization is unsafe")
    for name,report in reports.items():
        demand(report.get("real_device_flash_gate")=="DENY",
               "missing real-device DENY gate: "+name)
    demand(len(reports["u26"]["negative_boot_cases"])==4,
           "QEMU negative-control count wrong")
    for name,case in reports["u26"]["negative_boot_cases"].items():
        demand(case["halt_observed"] and not case["ubuntu_systemd_started"],
               "negative QEMU guest did not safely halt: "+name)
    demand(u28workflow.get("id")==38113211356,"wrong U28 workflow run ID")
    demand(u28workflow.get("head_branch")=="research/u28-source-gki-shiba-watchdog-build",
           "unexpected U28 workflow branch")
    demand(u28workflow.get("status") in ("queued","in_progress","completed"),
           "unexpected GitHub workflow state")
    conclusion=u28workflow.get("conclusion")
    demand(conclusion in (None,"success","failure","cancelled","timed_out",
                          "neutral","action_required","skipped","stale"),
           "unexpected U28 conclusion")
    if u28report:
        demand(u28report.get("source_common_commit")==GKI_SHA,
               "U28 audit GKI source SHA mismatch")
        demand(u28report.get("real_device_flash_gate")=="DENY",
               "U28 artifact missing DENY")
        demand(u28report.get("safe_to_flash") is False,
               "U28 audit made unsupported device claim")

    blockers={
        "stock_cp2a_device_signed_boot_chain_reproduced":False,
        "exact_CP2A_vendor_driver_KMI_CRC_match_verified":False,
        "correct_shiba_device_DTBO_panel_touch_verified":False,
        "physical_device_bootloader_AVB_rollback_state_read_only_verified":False,
        "physical_Android_backup_and_recovery_plan_verified":False,
        "non_destructive_Ubuntu_rootfs_storage_plan_verified":False,
        "USB_console_or_reliable_early_kernel_logs_on_Pixel8_verified":False,
        "physical_Pixel8_running_Ubuntu_kernel_verified":False,
    }
    achievements={
        "Google_official_GKI_6_1_157_source_matching_CP2A_Git_suffix":True,
        "QEMU_Ubuntu_26_04_systemd_boot_observed":True,
        "QEMU_bad_firststage_parameters_fail_closed":True,
        "older_6_1_124_vendor_module_incompatibility_detected":True,
        "Google_upstream_watchdog_VLA_issue_source_pinned":True,
        "physical_Pixel8_first_boot_ready":False,
    }
    all_hardware_ready=all(blockers.values())
    demand(not all_hardware_ready,"unexpected unsafe readiness state")
    report={
        "phase":"U29",
        "status":"U29_RESEARCH_PREFLIGHT_COMPLETED_PHYSICAL_FIRST_BOOT_NO_GO",
        "shiba_stock_firmware":"CP2A.260805.005",
        "shiba_stock_kernel_observed":STOCK_CP2A,
        "verified_research_milestones":achievements,
        "u28_workflow":{
            "id":u28workflow["id"],
            "url":u28workflow.get("html_url"),
            "status":u28workflow["status"],
            "conclusion":conclusion,
            "note":"A green CI compile is not stock firmware or a device flash permission",
            "u28_compiler_report_available":bool(u28report)
        },
        "U30_first_physical_boot_blockers":blockers,
        "physical_firstboot_go":False,
        "physical_device_modified":False,
        "signed_or_flashable_pixel8_firmware_generated":False,
        "real_device_flash_gate":"DENY"
    }
    (a.out/"U29_FIRSTBOOT_PREFLIGHT.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    )
    md=[
        "# U29 — Pixel 8 first boot preflight (strict NO-GO)",
        "",
        "**U29 CI report generated. Pixel 8 first boot is NOT APPROVED.**",
        "",
        f"- Currently installed Pixel 8 shiba CP2A kernel: \`{STOCK_CP2A}\`.",
        f"- U28 kernel build CI status: \`{u28workflow['status']}\` / \`{conclusion}\`.",
        "- CI source-provenance or compilation is NOT AVB/rollback compatibility.",
        "- Ubuntu 26.04 systemd started in a *generic ARM64 QEMU guest*, NOT Tensor G3.",
        "- Existing U17 vendor .ko images are for 6.1.124, not a verified CP2A 6.1.157 ABI.",
        "",
        "## Verified offline achievements",
    ]
    md += [f"- {'YES' if good else 'NO'}: {item}"
           for item,good in achievements.items()]
    md += ["","## Real hardware U30 blockers (must be reviewed independently)"]
    md += [f"- BLOCKED: {item}" for item,ready in blockers.items() if not ready]
    md += [
        "", "**REAL DEVICE FLASH GATE: DENY**",
        "No real device connected. No bootloader unlock/rollback, slot switching,",
        "partition imaging, userdata erasure, firmware signing or Android boot image",
        "writing was performed by this phase.",
        "The U30 aspirational milestone is not a deadline to risk bricking the phone.",
    ]
    (a.out/"U29_FIRSTBOOT_PREFLIGHT.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))
if __name__=="__main__":
    main()
