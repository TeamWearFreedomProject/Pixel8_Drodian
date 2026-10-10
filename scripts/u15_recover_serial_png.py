#!/usr/bin/env python3
"""Recover a real Wayland PNG screenshot emitted from QEMU guest serial log.

This accepts only a bounded base64 section bracketed by unique guest
markers, and the resulting PNG must be validated separately against its
actual pixel content (u15_assert_pixels.py).
"""
import argparse
import base64
import re
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--log",type=Path,required=True)
    p.add_argument("--png",type=Path,required=True)
    args=p.parse_args()
    data=args.log.read_text(errors="replace")
    begin="U15_PNG_BASE64_BEGIN\n"
    end="\nU15_PNG_BASE64_END"
    if data.count(begin)!=1 or data.count(end)!=1:
        raise SystemExit("Missing/ambiguous actual guest screenshot markers")
    raw=data.split(begin,1)[1].split(end,1)[0]
    lines=raw.splitlines()
    if len(raw)>5_000_000 or not lines:
        raise SystemExit("Invalid screenshot transport size")
    if any(not re.fullmatch("[A-Za-z0-9+/=]+",line) for line in lines):
        raise SystemExit("Screenshot contained non-base64 serial data")
    payload=base64.b64decode("".join(lines),validate=True)
    if not (payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload)>512):
        raise SystemExit("Not a valid PNG signature/size")
    args.png.parent.mkdir(parents=True,exist_ok=True)
    args.png.write_bytes(payload)
    print(f"U15 recovered PNG from guest Wayland: {len(payload)} bytes to {args.png}")

if __name__=="__main__":
    main()
