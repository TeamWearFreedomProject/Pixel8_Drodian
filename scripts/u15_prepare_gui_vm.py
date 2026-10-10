#!/usr/bin/env python3
"""U15: inject screenshot client + high contrast Waybar panel into disposable U6 image.

Keeps original U6 immutable and creates a separate throwaway QEMU-only disk.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import u14_prepare_gui_vm as u14

WAYBAR_CFG="""{
  "layer": "top",
  "position": "top",
  "height": 88,
  "spacing": 8,
  "modules-left": ["custom/u15"],
  "modules-right": ["clock"],
  "custom/u15": {
    "format": "UBUNTU 26.04 - ARM64 - LABWC - U15",
    "interval": "once",
    "tooltip": false
  },
  "clock": {"format": "{:%H:%M}", "tooltip": false}
}
"""
WAYBAR_CSS="""* {
  font-family: sans-serif;
  font-size: 23px;
  font-weight: bold;
  min-height: 0;
}
window#waybar {
  background: #1946c2;
  color: #ffffff;
  border-bottom: 5px solid #fcd32e;
}
#custom-u15 {
  background: #12cfe3;
  color: #152431;
  padding: 14px 23px;
}
#clock {
  background: #bd2b83;
  color: #ffffff;
  padding: 14px 20px;
}
"""

def main():
    ap=argparse.ArgumentParser()
    for name in ("u6","output","probe","gui_script","grim","work"):
        ap.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=ap.parse_args()
    cmd=[sys.executable,str(Path(__file__).parent/"u14_prepare_gui_vm.py"),
         "--u6",str(a.u6),"--output",str(a.output),"--probe",str(a.probe),
         "--gui-script",str(a.gui_script),"--work",str(a.work)]
    subprocess.run(cmd,check=True)
    f=a.output
    if not a.grim.is_file() or a.grim.stat().st_size < 10000:
        raise SystemExit("No ARM64 grim binary")
    dest="/usr/bin/u15-grim"
    u14.put(f,a.grim,dest)
    u14.dbfs(f,f"sif {dest} mode 0100755",True)
    if "Mode:  0755" not in u14.dbfs(f,"stat "+dest) and \
       "Mode:    0755" not in u14.dbfs(f,"stat "+dest):
        # Honor formatting variations if the canonical regex is present.
        import re
        if not re.search(r"Mode:\s+0755\b",u14.dbfs(f,"stat "+dest)):
            raise RuntimeError("u15-grim executable mode missing")
    for name,txt in (("u15-waybar.json",WAYBAR_CFG),
                     ("u15-waybar.css",WAYBAR_CSS)):
        item=a.work/name
        item.write_text(txt)
        u14.put(f,item,"/etc/"+name)
        if u14.dbfs(f,"cat /etc/"+name).strip()!=txt.strip():
            raise RuntimeError("Injected file differs "+name)
    if u14.sha(a.u6)!=u14.SOURCE_SHA:
        raise RuntimeError("Original U6 IMG modified")
    status={
        "state":"U15_QEMU_SCREENSHOT_GUEST_READY",
        "original_u6_sha256":u14.SOURCE_SHA,
        "scratch_vm_rootfs_sha256":u14.sha(f),
        "screenshot_client_sha256":u14.sha(a.grim),
        "pixel8_device_touched":False,
        "virtual_drm_screen":False,
        "headless_wayland_pixel_capture_attempt":True,
        "flashable":False
    }
    (a.work/"U15_VM_PREP.json").write_text(json.dumps(status,indent=2)+"\n")
    print(json.dumps(status,indent=2))
if __name__=="__main__":main()
