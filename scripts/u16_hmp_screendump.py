#!/usr/bin/env python3
"""Capture QEMU's real virtio video scanout via private Unix HMP socket (VM only)."""
import argparse, socket, time
from pathlib import Path
from PIL import Image

p=argparse.ArgumentParser()
p.add_argument("--serial",type=Path,required=True)
p.add_argument("--socket",type=Path,required=True)
p.add_argument("--ppm",type=Path,required=True)
p.add_argument("--png",type=Path,required=True)
p.add_argument("--log",type=Path,required=True)
a=p.parse_args()
a.log.parent.mkdir(parents=True,exist_ok=True)
def record(msg):
    with a.log.open("a") as f: f.write(msg+"\n")
    print("U16 HMP:",msg,flush=True)

deadline=time.monotonic()+90
marker="U16_QEMU_DISPLAY_CAPTURE_WINDOW"
while time.monotonic()<deadline:
    contents=a.serial.read_text(errors="replace") if a.serial.exists() else ""
    if marker in contents:
        break
    if "U16_FAIL_" in contents or "U16_LABWC_EXITED_EARLY" in contents:
        record("Guest reported earlier failure; skip screenshot. See serial log.")
        raise SystemExit(2)
    time.sleep(1)
else:
    record("Timeout: guest did not report DRM display capture window")
    raise SystemExit(2)
record("Guest indicates Labwc/Waybar capture window; requesting raw QEMU display scanout")
sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
sock.settimeout(8)
sock.connect(str(a.socket))
try:
    greeting=sock.recv(4096).decode(errors="replace")
    record("monitor: "+greeting[-250:])
    sock.sendall(("screendump "+str(a.ppm.resolve())+"\n").encode())
    reply=sock.recv(4096).decode(errors="replace")
    record("screendump reply: "+reply[-500:])
finally:
    sock.close()
for _ in range(10):
    if a.ppm.is_file() and a.ppm.stat().st_size>1000:
        break
    time.sleep(0.6)
else:
    record("No QEMU monitor screendump file; scanout not proven")
    raise SystemExit(2)
with Image.open(a.ppm) as img:
    img.load()
    record(f"raw QEMU scanout {img.size} {img.mode}")
    img.convert("RGB").save(a.png,format="PNG")
a.ppm.unlink(missing_ok=True)
record(f"Host QEMU DRM display PNG saved: {a.png}")
