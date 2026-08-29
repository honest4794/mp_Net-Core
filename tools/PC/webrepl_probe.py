#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# webrepl_probe.py — 極簡 WebREPL 客戶端 (raw socket + masked WS)
# 用途：設備 NC4 命令層掛掉時，直接進 REPL 檢查/修復檔案系統。
#
# 用法:
#   python3 -B webrepl_probe.py <ip> [command ...]   # 登入後執行 command 並印輸出
#   無 command → 進互動 REPL (逐行 stdin)
#
import base64
import os
import socket
import struct
import sys
import time

HOST = "127.0.0.1"
PORT = 8266
PASSWORD = "12345678"

# 跨 handshake / recv 的持久接收緩衝（101 回應後可能立刻跟 WS frame，不能丟）
_rbuf = bytearray()


def ws_handshake(sock, host, port):
    global _rbuf
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "Sec-WebSocket-Protocol: binary\r\n\r\n"
    )
    sock.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(1024)
        if not chunk:
            raise RuntimeError("handshake EOF")
        buf += chunk
    if b"101" not in buf.split(b"\r\n", 1)[0]:
        raise RuntimeError("handshake failed: " + buf.split(b"\r\n", 1)[0].decode(errors="replace"))
    # 保留 header 之後的殘留位元組 (可能是 WebREPL 的第一個 WS frame)
    _rbuf = bytearray(buf.split(b"\r\n\r\n", 1)[1])
    return buf


def ws_send_masked(sock, payload, opcode=0x01):
    payload = payload if isinstance(payload, (bytes, bytearray)) else payload.encode()
    mask = os.urandom(4)
    n = len(payload)
    hdr = bytearray([0x80 | opcode])
    if n <= 125:
        hdr.append(0x80 | n)
    elif n <= 65535:
        hdr.append(0x80 | 126)
        hdr.extend(struct.pack(">H", n))
    else:
        hdr.append(0x80 | 127)
        hdr.extend(struct.pack(">Q", n))
    hdr.extend(mask)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    sock.sendall(hdr + masked)


def _read_exact(sock, n):
    global _rbuf
    while len(_rbuf) < n:
        chunk = sock.recv(n - len(_rbuf))
        if not chunk:
            raise EOFError("socket EOF")
        _rbuf.extend(chunk)
    out = bytes(_rbuf[:n])
    del _rbuf[:n]
    return out


def ws_recv_frame(sock, timeout=5.0):
    """讀一個完整 WS frame，回傳 (opcode, payload)。"""
    sock.settimeout(timeout)

    b0 = _read_exact(sock, 1)[0]
    b1 = _read_exact(sock, 1)[0]
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    plen = b1 & 0x7F
    if plen == 126:
        plen = struct.unpack(">H", _read_exact(sock, 2))[0]
    elif plen == 127:
        plen = struct.unpack(">Q", _read_exact(sock, 8))[0]
    mask = _read_exact(sock, 4) if masked else b""
    payload = _read_exact(sock, plen)
    if masked:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


def login(sock):
    # 第一個 frame 通常是 "Password: " 提示
    try:
        op, payload = ws_recv_frame(sock, timeout=3.0)
        sys.stdout.write("[server] " + payload.decode(errors="replace"))
        sys.stdout.flush()
    except EOFError:
        pass
    # 送密碼
    ws_send_masked(sock, PASSWORD + "\r", opcode=0x01)
    # 讀登入後 banner，直到看到 >>> 或 timeout
    buf = b""
    deadline = time.time() + 3.0
    while time.time() < deadline:
        try:
            op, payload = ws_recv_frame(sock, timeout=0.5)
            buf += payload
            if b">>>" in buf or b"WebREPL connected" in buf:
                break
        except (EOFError, socket.timeout):
            break
    return buf


def send_cmd(sock, cmd):
    ws_send_masked(sock, cmd + "\r", opcode=0x01)
    # 收輸出直到看到 ">>> " (REPL prompt) 或 timeout
    out = b""
    sock.settimeout(2.0)
    deadline = time.time() + 5.0
    while time.time() < deadline:
        try:
            op, payload = ws_recv_frame(sock, timeout=0.3)
            out += payload
            # WebREPL 每段輸出後會帶 \r\n>>> 提示；連 command echo 一起收
            if b">>> " in out and out.rstrip().endswith(b">>>"):
                # 確認 prompt 在結尾
                pass
        except (EOFError, socket.timeout):
            break
        if out.rstrip().endswith(b">>>") or (b">>> " in out and out.rstrip().endswith(b">>>")):
            break
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    host = sys.argv[1]
    commands = sys.argv[2:]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((host, PORT))
    ws_handshake(sock, host, PORT)
    banner = login(sock)
    sys.stdout.write(banner.decode(errors="replace"))
    sys.stdout.flush()

    if commands:
        for c in commands:
            out = send_cmd(sock, c)
            sys.stdout.write(out.decode(errors="replace"))
            sys.stdout.flush()
    else:
        # 互動模式
        print("\n[interactive WebREPL — Ctrl+C 退出]")
        try:
            while True:
                line = sys.stdin.readline()
                if line == "":
                    break
                out = send_cmd(sock, line.rstrip("\n"))
                sys.stdout.write(out.decode(errors="replace"))
                sys.stdout.flush()
        except KeyboardInterrupt:
            pass

    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
