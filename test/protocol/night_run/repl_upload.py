#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repl_upload.py — 透過 normal REPL (ctrl-B) 把本機檔案寫入 ESP32 (base64 傳輸)

用途：當 mpremote exec/cp 因 TaskManager 佔住 raw REPL 而失敗時，改用這個。
     它會 ctrl-C 中斷執行 + ctrl-B 切到 normal REPL，再用 base64 分段寫檔。

用法：
    python repl_upload.py <port> <local_path> <remote_path>
    python repl_upload.py /dev/cu.usbmodem11401 slave/lib/sys/bus_speed.py /lib/sys/bus_speed.py

注意：
    - 目標板必須是 MicroPython（ESP32）。
    - 寫入後建議 soft-reset (ctrl-D) 讓模組重新 import。
"""

import base64
import posixpath
import sys
import time

import serial


def _mkdir_commands(remote_path):
    """Build idempotent normal-REPL commands for remote parent directories."""
    parent = posixpath.dirname(remote_path)
    if not remote_path.startswith("/") or parent in ("", "/"):
        return []

    commands = []
    current = "/"
    for name in parent.strip("/").split("/"):
        next_path = posixpath.join(current, name)
        commands.append(
            "os.mkdir(%r) if %r not in os.listdir(%r) else None" %
            (next_path, name, current))
        current = next_path
    return commands


def upload(port, local_path, remote_path):
    with open(local_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    print(f"[repl_upload] {local_path} -> {remote_path} ({len(data)} bytes, b64 {len(b64)})")

    s = serial.Serial(port, 115200, timeout=0.5)
    s.dtr = False
    s.rts = False
    time.sleep(0.3)
    s.reset_input_buffer()

    # 中斷任何執行 + 切 normal REPL
    s.write(b'\x03\x03\x03')
    time.sleep(0.6)
    s.write(b'\x02')   # ctrl-B 離開 raw REPL
    time.sleep(0.6)
    s.reset_input_buffer()

    # Fresh firmware has no /lib, /tasks, etc. Create remote parents first.
    s.write(b"import os\r\n")
    time.sleep(0.2)
    for command in _mkdir_commands(remote_path):
        s.write((command + "\r\n").encode())
        time.sleep(0.2)

    # 分塊寫入 b64 到暫存檔
    s.write(b"f=open('/_up.b64','wb')\r\n")
    time.sleep(0.3)
    CHUNK = 400
    for i in range(0, len(b64), CHUNK):
        c = b64[i:i + CHUNK]
        line = "f.write(" + repr(c) + ")\r\n"
        s.write(line.encode())
        time.sleep(0.03)
    s.write(b"f.close()\r\n")
    time.sleep(0.4)

    # 解碼寫入目標
    s.write(b"import ubinascii\r\n")
    time.sleep(0.2)
    s.write(b"d=ubinascii.a2b_base64(open('/_up.b64').read())\r\n")
    time.sleep(0.4)
    s.write(("open(%r,'wb').write(d)\r\n" % remote_path).encode())
    time.sleep(0.6)
    s.write(b"print('UPLOADED', len(d))\r\n")
    time.sleep(0.5)
    s.write(b"import os; os.remove('/_up.b64')\r\n")
    time.sleep(0.3)

    out = b''
    t0 = time.time()
    while time.time() - t0 < 4:
        while s.in_waiting:
            out += s.read(s.in_waiting)
        time.sleep(0.1)
    s.close()

    txt = out.decode('utf-8', 'replace')
    ok = f"UPLOADED {len(data)}" in txt
    print(f"[repl_upload] {'OK' if ok else 'FAIL'}: {txt[-200:]}")
    return ok


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    ok = upload(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if ok else 1)
