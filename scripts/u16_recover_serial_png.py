#!/usr/bin/env python3
"""Extract bounded, real guest-produced DRM Wayland PNG from serial. Not generated pixels."""
import argparse, base64, re
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--log",type=Path,required=True)
p.add_argument("--png",type=Path,required=True)
a=p.parse_args()
log=a.log.read_text(errors="replace")
begin="U16_PNG_BASE64_BEGIN\n"
end="\nU16_PNG_BASE64_END"
if log.count(begin)!=1 or log.count(end)!=1:
    raise SystemExit("DRM screenshot markers absent/ambiguous")
data=log.split(begin,1)[1].split(end,1)[0]
lines=data.splitlines()
if not (lines and len(data)<5_000_000 and all(re.fullmatch("[A-Za-z0-9+/=]+",x) for x in lines)):
    raise SystemExit("DRM PNG payload invalid or oversized")
blob=base64.b64decode("".join(lines),validate=True)
if not blob.startswith(b"\x89PNG\r\n\x1a\n") or len(blob)<512:
    raise SystemExit("Not a real PNG")
a.png.parent.mkdir(parents=True,exist_ok=True)
a.png.write_bytes(blob)
print("U16 recovered guest DRM Wayland frame:",len(blob),"bytes")
