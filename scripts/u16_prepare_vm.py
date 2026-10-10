#!/usr/bin/env python3
"""U16: extend throwaway U15 VM with ARM64 seatd, never alter real U6."""
import argparse, json, subprocess, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import u14_prepare_gui_vm as u14
p=argparse.ArgumentParser()
for name in ("u6","output","probe","gui_script","grim","seatd","work"):
    p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
a=p.parse_args()
subprocess.run([sys.executable,str(Path(__file__).parent/"u15_prepare_gui_vm.py"),
    "--u6",str(a.u6),"--output",str(a.output),
    "--probe",str(a.probe),"--gui-script",str(a.gui_script),
    "--grim",str(a.grim),"--work",str(a.work)],check=True)
if not a.seatd.is_file() or a.seatd.stat().st_size<5000:
    raise SystemExit("Missing real ARM64 seatd executable")
u14.put(a.output,a.seatd,"/usr/bin/u16-seatd")
u14.dbfs(a.output,"sif /usr/bin/u16-seatd mode 0100755",True)
if "Inode:" not in u14.dbfs(a.output,"stat /usr/bin/u16-seatd"):
    raise SystemExit("seatd injection absent")
if u14.sha(a.u6)!=u14.SOURCE_SHA:
    raise SystemExit("U16 original rootfs was changed")
result={"state":"U16_VIRTIO_DRM_GUEST_PREPARED",
        "original_u6_sha256":u14.SOURCE_SHA,
        "vm_rootfs_sha256":u14.sha(a.output),
        "seatd_arm64_sha256":u14.sha(a.seatd),
        "pixel8_touched":False,"phone_bootable":False,
        "requires_guest_kernel_virtio_gpu":True}
(a.work/"U16_PREP.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
