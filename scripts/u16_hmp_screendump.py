#!/usr/bin/env python3
"""Capture *actual* QEMU virtio-GPU scanout using QMP + HMP screendump.

QEMU-only test. Unlike a raw HMP terminal socket, QMP produces a complete
JSON response: verify monitor command completion before closing the socket.
"""
import argparse
import json
import socket
import time
from pathlib import Path

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--serial", type=Path, required=True)
parser.add_argument("--socket", type=Path, required=True)
parser.add_argument("--ppm", type=Path, required=True)
parser.add_argument("--png", type=Path, required=True)
parser.add_argument("--log", type=Path, required=True)
args = parser.parse_args()
args.log.parent.mkdir(parents=True, exist_ok=True)

def record(message):
    line = str(message)
    with args.log.open("a") as log:
        log.write(line + "\n")
    print("U16 QMP:", line, flush=True)

def qmp_receive(reader, request_id=None):
    """Receive complete line-delimited QMP responses; skip async events."""
    for _ in range(32):
        line = reader.readline(65536)
        if not line:
            raise RuntimeError("QMP monitor closed the connection")
        response = json.loads(line)
        if request_id is None:
            return response
        if response.get("id") == request_id:
            return response
        record("QMP notification/unmatched reply: " + line[:400].strip())
    raise RuntimeError("No matching QMP response after 32 monitor messages")

def qmp_execute(sock, reader, command, ident, arguments=None):
    request = {"execute": command, "id": ident}
    if arguments is not None:
        request["arguments"] = arguments
    sock.sendall((json.dumps(request, separators=(",", ":")) + "\n").encode())
    reply = qmp_receive(reader, ident)
    if "error" in reply:
        raise RuntimeError("QMP command error: " + str(reply["error"]))
    if "return" not in reply:
        raise RuntimeError("QMP reply has no return value: " + repr(reply))
    record("QMP " + command + " reply: " + str(reply["return"])[:1500])
    return reply["return"]

deadline = time.monotonic() + 95
marker = "U16_QEMU_DISPLAY_CAPTURE_WINDOW"
while time.monotonic() < deadline:
    contents = args.serial.read_text(errors="replace") if args.serial.exists() else ""
    if marker in contents:
        break
    if "U16_FAIL_" in contents or "U16_LABWC_EXITED_EARLY" in contents:
        record("Guest failed before capture window; see guest serial output")
        raise SystemExit(2)
    time.sleep(0.5)
else:
    record("No guest capture marker before timeout")
    raise SystemExit(2)

record("Guest reports DRM compositor capture window; request independent QEMU scanout")
for _ in range(20):
    if args.socket.exists():
        break
    time.sleep(0.25)
else:
    raise SystemExit("QMP Unix socket was not created by QEMU")

args.ppm.unlink(missing_ok=True)
args.png.unlink(missing_ok=True)

try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(12)
        sock.connect(str(args.socket))
        with sock.makefile("r", encoding="utf-8") as reader:
            greeting = qmp_receive(reader)
            if "QMP" not in greeting:
                raise RuntimeError("Missing QMP greeting: " + repr(greeting))
            record("Connected to QEMU QMP (" + str(greeting["QMP"].get("version", {}))[:300] + ")")
            qmp_execute(sock, reader, "qmp_capabilities", "u16-capabilities")
            # HMP screendump writes a PPM file directly on the ephemeral runner.
            # Unlike the previous HMP command-line reader, this waits for the
            # COMPLETE success/error response rather than reading one echo byte.
            command = "screendump " + str(args.ppm.resolve())
            result = qmp_execute(sock, reader, "human-monitor-command",
                                 "u16-screendump", {"command-line": command})
            if not isinstance(result, str):
                raise RuntimeError("Unexpected HMP screendump return type")
            error_words = ("Error:", "error:", "Could not", "Failed", "failed", "unknown command")
            if any(word in result for word in error_words):
                raise RuntimeError("HMP screendump failed: " + result)
except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
    record("Monitor communication failure: " + repr(exc))
    raise SystemExit(2) from exc

for _ in range(24):
    if args.ppm.is_file() and args.ppm.stat().st_size > 1000:
        break
    time.sleep(0.25)
else:
    record("QMP command responded but QEMU produced no PPM scanout")
    raise SystemExit(2)

with Image.open(args.ppm) as image:
    image.load()
    record("QEMU raw PPM " + str(image.size) + ", mode=" + image.mode)
    image.convert("RGB").save(args.png, format="PNG")
args.ppm.unlink(missing_ok=True)
record("Host QEMU virtio-GPU scanout captured as " + str(args.png))
