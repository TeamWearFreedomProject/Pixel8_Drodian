#!/usr/bin/env python3
"""U32 follow-up: locate OLD 6.1.124 modules found in actual U32 CI outputs.

A diagnostic after the strict CRC gate fails. Does NOT hide 58 old modules,
change any kernel config, whitelist incompatible modules or approve flashing.
It inventories every path and distinguishes a staged Bazel output from files
copied to the final shusky dist directory. Packed images are NOT inspected.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import u31_offline_abi_audit as u31

OLD="6.1.124-android14-11"
CURRENT="6.1.157-android14-11"

def stop(message):
    raise SystemExit("U32 LEGACY MODULE ORIGIN FAIL CLOSED: "+message)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--previous",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    previous=json.loads(args.previous.read_text())
    if (previous.get("phase")!="U32" or
        previous.get("real_device_flash_gate")!="DENY"):
        stop("previous U32 audit not the expected fail-closed evidence")
    current_map={}
    for path in u31.module_listing(args.src):
        content_sha=sha(path)
        item=current_map.setdefault(content_sha,[])
        item.append(path)
    if len(current_map)!=previous.get("distinct_file_content_SHA256"):
        stop("source-build module SHA256 groups changed relative to CRC audit")
    if sum(map(len,current_map.values()))!=previous.get("all_discovered_ko_paths"):
        stop("module path count changed relative to CRC audit")
    legacy=[]
    current=[]
    unknown=[]
    counts=collections.Counter()
    for content_sha,paths in sorted(current_map.items()):
        probe=min(paths,key=lambda p:str(p))
        rc, name, _ =u31.command(["modinfo","-F","name",str(probe)])
        vr, version, error =u31.command(["modinfo","-F","vermagic",str(probe)])
        if rc or vr:
            stop("cannot inspect module "+probe.name+": "+error)
        rel_paths=[]
        classes=[]
        for p in sorted(paths,key=str):
            try:
                rel=p.relative_to(args.src)
            except ValueError:
                stop("module escaped source workspace")
            relative=rel.as_posix()
            rel_paths.append(relative)
            if relative.startswith("out/shusky/dist/"):
                kind="FINAL_SHUSKY_DIST_UNPACKED"
            elif relative.startswith("bazel-bin/private/google-modules/"):
                kind="GOOGLE_VENDOR_BAZEL_OUTPUT"
            elif relative.startswith("bazel-bin/private/devices/google/shusky/"):
                kind="SHUSKY_BAZEL_OUTPUT"
            else:
                kind="OTHER_DISCOVERED_BUILD_ROOT"
            classes.append(kind)
            counts[kind]+=1
        record={
            "name":name,"sha256":content_sha,"vermagic":version,
            "path_count":len(paths),"source_path_classes":sorted(set(classes)),
            "paths":rel_paths,
            "in_final_dist_as_unpacked_ko":"FINAL_SHUSKY_DIST_UNPACKED" in classes
        }
        if version.startswith(OLD):
            legacy.append(record)
        elif version.startswith(CURRENT):
            current.append(record)
        else:
            unknown.append(record)
    if len(legacy)!=previous.get("module_vermagic_bad_count"):
        stop("old 6.1.124 inventory does not agree with failed U32 gate")
    loaded_in_dist=[r for r in legacy if r["in_final_dist_as_unpacked_ko"]]
    result={
        "phase":"U32_ORIGIN",
        "status":"U32_OLD_6_1_124_PROVENANCE_CAPTURED_NOT_RESOLVED",
        "previous_crc_conflicts_with_research_GKI":
            previous.get("research_GKI_export_CRC_disagreement_total"),
        "total_unique_content_groups":len(current_map),
        "research_6_1_157_distinct_groups":len(current),
        "old_6_1_124_distinct_groups":len(legacy),
        "other_releases_distinct_groups":len(unknown),
        "old_groups_directly_in_unpacked_final_dist":len(loaded_in_dist),
        "old_groups_directly_in_unpacked_final_dist_names":
            [x["name"] for x in loaded_in_dist],
        "module_path_classes":dict(counts),
        "all_legacy_modules_and_each_origin_path":legacy,
        "unknown_release_modules":unknown,
        "note":"Does NOT scan inside compressed/packed vendor_dlkm.img or system_dlkm.img",
        "unpacked_dist_absence_proves_packed_image_safe":False,
        "stock_CP2A_vendor_module_compatibility_proven":False,
        "source_modules_still_contain_old_prebuilt_6_1_124":len(legacy)>0,
        "real_pixel8_accessed":False,
        "real_device_flash_gate":"DENY"
    }
    (args.out/"U32_OLD_GKI_MODULE_ORIGINS.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    summary=[
        "# U32 — legacy 6.1.124 module origin forensics",
        "",
        "**OLD GKI MODULES STILL PRESENT. NEVER FLASH.**",
        "",
        "- Distinct research source 6.1.157 modules: "+str(len(current)),
        "- Distinct OLD 6.1.124 modules: "+str(len(legacy)),
        "- Other releases: "+str(len(unknown)),
        "- Old modules directly present as unpacked .ko under out/shusky/dist: "+
          str(len(loaded_in_dist)),
        "",
        "## Real paths of every old module are recorded in U32_OLD_GKI_MODULE_ORIGINS.json",
    ]
    for kind,count in sorted(counts.items()):
        summary.append("- "+kind+": "+str(count)+" output path occurrences (all versions)")
    summary.extend([
        "",
        "No module exclusion or version bypass has been applied.",
        "Only when actual packaging paths are examined may we distinguish",
        "unused Bazel intermediates from kernel module contents packaged",
        "inside vendor_dlkm.img and system_dlkm.img.",
        "**RESEARCH AUDIT BLOCKED; REAL DEVICE FLASH GATE DENY.**"
    ])
    (args.out/"U32_OLD_GKI_MODULE_ORIGINS.md").write_text(
        "\n".join(summary)+"\n")
    print("\n".join(summary))

if __name__=="__main__":
    main()
