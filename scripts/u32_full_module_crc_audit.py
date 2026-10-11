#!/usr/bin/env python3
"""U32: full discovered .ko inventory and research-GKI CRC audit (NO PHONE).

No Android device, USB, administrator rights, bootloader, partitions or boot
images are used. This compares *our isolated 6.1.157 research build* against
its *own* Module.symvers, never against unprovided official stock CP2A blobs.
It scans every directly discovered .ko (within the same U31 source/build roots),
deduplicates byte-identical files, and refuses to claim unexamined modules pass.
"""
import argparse
from collections import Counter
import hashlib
import json
import sys
from pathlib import Path

# This script and the already CI-proven U31 audit live together in scripts/.
import u31_offline_abi_audit as u31

def stop(reason):
    raise SystemExit("U32 MODULE COVERAGE FAIL CLOSED: " + reason)

def sha(file):
    h=hashlib.sha256()
    with file.open("rb") as stream:
        for data in iter(lambda:stream.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def read_single(folder,name):
    matches=sorted(folder.rglob(name))
    if len(matches)!=1:
        stop("expected one reference "+name+", got "+str(len(matches)))
    return json.loads(matches[0].read_text())

def save(path,body):
    path.write_text(json.dumps(body,indent=2,ensure_ascii=False)+"\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--u31-evidence",required=True,type=Path)
    args=ap.parse_args()
    src=args.src
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    baseline=read_single(args.u31_evidence,"U31_OFFLINE_ABI_BOARD_AUDIT.json")
    if (baseline.get("phase")!="U31" or
        baseline.get("status")!="U31_RESEARCH_OFFLINE_INVENTORY_COMPLETE_NOT_CP2A_DEVICE_CERTIFIED" or
        baseline.get("device_flash_gate")!="DENY" or
        baseline.get("source_GKI_exported_symbol_count",0)<1 or
        baseline.get("vendor_modules_inspected")!=180 or
        baseline.get("kernel_exported_symbol_crc_disagreements")!=0):
        stop("trusted immutable U31 audit does not match previously passed research evidence")

    rc,git,_=u31.command(["git","-C",str(src/"aosp"),"rev-parse","HEAD"])
    if rc!=0 or git!=u31.GKI_SHA:
        stop("wrong kernel/common Git pin")

    direct=src/"bazel-bin/aosp/kernel_aarch64/Image"
    dist=src/"out/shusky/dist/Image"
    symvers=src/"bazel-bin/aosp/kernel_aarch64/kernel_aarch64_Module.symvers"
    if not all(p.is_file() for p in (direct,dist,symvers)):
        stop("actual source kernel, full dist Image or GKI symvers missing")
    if sha(direct)!=sha(dist):
        stop("source Image and full vendor dist Image hashes differ")
    release=u31.kernel_banner(dist)
    if not release or not release.startswith("6.1.157-android14-11"):
        stop("not the source-built 6.1.157 kernel")
    exports,_,malformed=u31.read_symvers(symvers)
    if len(exports)<1 or len(exports)!=baseline["source_GKI_exported_symbol_count"]:
        stop("GKI export count unexpected relative to U31")

    # Sort paths for reproducibility and count ALL paths found by U31 discovery.
    # The file content hash, not a path-based guess, de-duplicates outputs
    # copied to multiple Bazel locations. This is NOT a list of stock modules.
    paths=sorted(u31.module_listing(src), key=lambda p:str(p))
    if len(paths)<baseline["vendor_modules_found_as_direct_ko"]:
        stop("discovered fewer .ko paths than immutable U31 research baseline")
    if not paths:
        stop("no research module outputs found")
    classes={}
    item_errors=[]
    for p in paths:
        try:
            fingerprint=sha(p)
        except OSError as exc:
            item_errors.append({"path":str(p),"error":str(exc)[:300]})
            continue
        group=classes.setdefault(fingerprint,{"representative":p,"paths":[]})
        group["paths"].append(str(p))
    inspected=[]
    for fingerprint,group in sorted(classes.items()):
        module=u31.inspect_ko(group["representative"], exports)
        module["sha256"]=fingerprint
        module["duplicates_or_other_build_paths"]=len(group["paths"])
        module["representative_path"]=str(group["representative"])
        inspected.append(module)

    problem_mods=[]
    parse_errors=[]
    vermagic_fail=[]
    disagreements=[]
    unknown_examples=[]
    total_research_imports_compared=0
    total_unknown_imports=0
    for mod in inspected:
        if not mod.get("vermagic_has_6_1_157_prefix"):
            vermagic_fail.append(mod["module"])
        if mod.get("module_crc_inspection_rc")!=0:
            parse_errors.append(mod["module"])
        total_research_imports_compared+=mod.get("module_crc_compared_count",0)
        total_unknown_imports+=mod.get("unmatched_external_symbols",0)
        if mod.get("module_crc_disagree_count",0):
            problem_mods.append(mod["module"])
            if len(disagreements)<12:
                disagreements.append({
                    "module":mod["module"],
                    "symbols":mod.get("crc_mismatch_symbol_examples",[]),
                    "count":mod["module_crc_disagree_count"]
                })
        if mod.get("unmatched_external_symbols",0) and len(unknown_examples)<15:
            unknown_examples.append({
                "module":mod["module"],
                "symbols":mod.get("symbol_not_in_base_gki_examples",[]),
                "unknown_count":mod.get("unmatched_external_symbols",0)
            })

    distinct=len(inspected)
    count_by_module=Counter(mod["module"] for mod in inspected)
    module_names_reused={k:v for k,v in count_by_module.items() if v>1}
    all_covered=(not item_errors and distinct==len(classes)
                 and len(paths)==sum(len(x["paths"]) for x in classes.values()))
    fully_parsed=(len(parse_errors)==0 and len(vermagic_fail)==0)
    mismatch_count=sum(m.get("module_crc_disagree_count",0) for m in inspected)
    pass_research=(all_covered and fully_parsed and mismatch_count==0
                   and total_research_imports_compared>0)
    recorded={
        "phase":"U32",
        "status":("U32_ALL_DISCOVERED_RESEARCH_MODULES_AUDITED_NO_BASE_GKI_CRC_CONFLICT"
                  if pass_research else
                  "U32_DISCOVERED_MODULE_AUDIT_INCOMPLETE_OR_CONFLICT"),
        "source_GKI_git_sha":git,
        "source_GKI_Image_banner":release,
        "actual_full_dist_Image_sha256":sha(dist),
        "U31_baseline_paths":baseline["vendor_modules_found_as_direct_ko"],
        "U31_baseline_modules_scanned":baseline["vendor_modules_inspected"],
        "U31_baseline_imported_CRC_matches":baseline["kernel_exported_symbol_crc_comparisons"],
        "research_exported_GKI_symbols":len(exports),
        "malformed_GKI_symvers_rows":malformed,
        "all_discovered_ko_paths":len(paths),
        "distinct_file_content_SHA256":distinct,
        "identical_content_extra_paths":len(paths)-distinct,
        "all_discovered_content_groups_examined":all_covered,
        "modules_with_duplicate_name_across_distinct_contents":module_names_reused,
        "research_GKI_symbol_import_CRC_comparisons":total_research_imports_compared,
        "research_GKI_export_CRC_disagreement_total":mismatch_count,
        "modules_with_CRC_disagreement":problem_mods[:30],
        "crc_conflict_examples":disagreements,
        "unmatched_symbols_NOT_IN_BASE_GKI_EXPORT_TABLE_count":total_unknown_imports,
        "unknown_vendor_or_other_source_import_examples":unknown_examples,
        "module_vermagic_bad_count":len(vermagic_fail),
        "module_vermagic_bad_examples":vermagic_fail[:30],
        "module_crc_parser_errors_count":len(parse_errors),
        "module_crc_parser_error_examples":parse_errors[:30],
        "module_file_hash_errors_count":len(item_errors),
        "module_file_hash_error_examples":item_errors[:20],
        "scope":"all .ko directly reachable by inherited U31 Bazel/dist discovery roots",
        "compressed_or_packed_ko_inside_vendor_images_separately_extracted":False,
        "unique_CP2A_vendor_binary_reference_present":False,
        "stock_CP2A_Module_symvers_reference_present":False,
        "stock_CP2A_vendor_KMI_CRC_compatibility_verified":False,
        "DTBO_shiba_panel_selection_compatibility_verified":False,
        "rootfs_or_device_boot_verified":False,
        "real_pixel8_device_accessed":False,
        "admin_rights_on_local_school_PC_required":False,
        "real_device_flash_gate":"DENY"
    }
    save(out/"U32_COMPLETE_RESEARCH_KMI_CRC.json",recorded)

    # A compact inventory permits source-only inspection without exporting .ko.
    # No kernel/boot or vendor image bytes are copied to this report.
    manifest={
        "phase":"U32",
        "every_file_content_group_examined":all_covered,
        "records":[{
            "module":m["module"],"sha256":m["sha256"],
            "size_bytes":m["bytes"],
            "content_duplicate_paths":m["duplicates_or_other_build_paths"],
            "vermagic":m.get("vermagic"),
            "crc_compared_with_research_gki":m["module_crc_compared_count"],
            "crc_mismatches":m["module_crc_disagree_count"],
            "crc_symbols_unavailable_in_base_gki":m["unmatched_external_symbols"],
            "crc_inspection_exit":m["module_crc_inspection_rc"]
        } for m in inspected],
        "not_verified_against_stock_CP2A":True,
        "device_flash_gate":"DENY"
    }
    save(out/"U32_RESEARCH_MODULE_MANIFEST.json",manifest)

    missing={
        "phase":"U32",
        "already_proven":"U30/31 research 6.1.157 kernel and own modules compile and self-consistency",
        "unavailable_stock_CP2A_inputs":[
            "trusted original shiba CP2A.260805.005 stock GKI Module.symvers",
            "CP2A shiba original matching vendor_dlkm/system_dlkm module binaries",
            "signed-stock CP2A kernel metadata, exact full release and config",
            "verified shiba panel DTBO IDs and overlay selections",
            "trusted AVB rollback and full recovery/backup evidence",
            "reviewed Ubuntu rootfs storage mapping and init/device logs"
        ],
        "not_solved_by_more_research_module_CRCs":True,
        "flash_gate":"DENY"
    }
    save(out/"U32_STOCK_CP2A_REFERENCE_GAPS.json",missing)
    summary=[
        "# U32 — full discovery-scope research module CRC coverage",
        "",
        "**ONLY OUR ISOLATED RESEARCH BUILD. STOCK CP2A ABI NOT COMPARED.**",
        "",
        "- U31 available .ko file paths: "+str(baseline["vendor_modules_found_as_direct_ko"]),
        "- U32 total discovered .ko paths: "+str(len(paths)),
        "- Unique SHA256 module contents inspected: "+str(distinct),
        "- Repeated/copied module paths: "+str(len(paths)-distinct),
        "- Source-built Linux kernel: "+str(release),
        "- Own-GKI \`Module.symvers\` exported symbols: "+str(len(exports)),
        "- Own-GKI imported symbol CRC comparisons: "+str(total_research_imports_compared),
        "- Own-GKI CRC disagreements: "+str(mismatch_count),
        "- Imported symbol references absent from BASE GKI export list: "+str(total_unknown_imports),
        "- Module vermagic failures: "+str(len(vermagic_fail)),
        "- Module version-table parse failures: "+str(len(parse_errors)),
        "- Content file read errors: "+str(len(item_errors)),
        "- Full discovered content-group coverage: "+str(all_covered),
        "",
        "**Missing GKI-only exports may originate from vendor module exports, "
        "and are NOT treated as proof of a CRC mismatch.**",
        "",
        "## Remaining STOP conditions",
        "- No reference CP2A stock ABI/module CRCs: never claim compatibility",
        "- No shiba panel/DTBO selection validation, AVB/rollback/rescue, rootfs boot",
        "- Only discovered unpacked .ko files were scanned; other packed modules unverified",
        "- All output is text/JSON/SHA256, never device-ready firmware",
        "",
        "**REAL DEVICE FLASH GATE: DENY.**"
    ]
    (out/"U32_COMPLETE_RESEARCH_KMI_CRC.md").write_text("\n".join(summary)+"\n")
    print("\n".join(summary))
    if not pass_research:
        stop("CRC, vermagic or inspection errors exist; inspect U32 JSON evidence")
    if total_research_imports_compared<baseline["kernel_exported_symbol_crc_comparisons"]:
        stop("U32 all modules had fewer parsed GKI-imported CRCs than U31 sample")

if __name__=="__main__":
    main()
