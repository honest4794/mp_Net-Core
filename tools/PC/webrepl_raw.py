#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# webrepl_raw.py — 低階 WebREPL 探針：登入後可互動送字元（含 Ctrl+C/Ctrl+D）並 dump 原始 frame。
import base64
import os
import socket
import struct
import sys
import time

_rbuf = bytearray()


def connect(host, port=8266):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((host, port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
           f"Sec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: binary\r\n\r\n")
    sock.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        c = sock.recv(1024)
        if not c:
            raise RuntimeError("handshake EOF")
        buf += c
    if b"101" not in buf.split(b"\r\n", 1)[0]:
        raise RuntimeError("handshake fail: " + buf.split(b"\r\n", 1)[0].decode(errors="replace"))
    global _rbuf
    _rbuf = bytearray(buf.split(b"\r\n\r\n", 1)[1])
    return sock


def _read_exact(sock, n):
    global _rbuf
    while len(_rbuf) < n:
        c = sock.recv(n - len(_rbuf))
        if not c:
            raise EOFError
        _rbuf.extend(c)
    out = bytes(_rbuf[:n])
    del _rbuf[:n]
    return out


def recv_frame(sock, timeout=2.0):
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


def send_frame(sock, data, opcode=0x01):
    data = data if isinstance(data, (bytes, bytearray)) else data.encode()
    mask = os.urandom(4)
    n = len(data)
    hdr = bytearray([0x80 | opcode])
    if n <= 125:
        hdr.append(0x80 | n)
    elif n <= 65535:
        hdr.append(0x80 | 126); hdr.extend(struct.pack(">H", n))
    else:
        hdr.append(0x80 | 127); hdr.extend(struct.pack(">Q", n))
    hdr.extend(mask)
    sock.sendall(hdr + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def drain(sock, seconds, label=""):
    out = b""
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            op, pl = recv_frame(sock, timeout=0.4)
            print(f"[{label}] op={op} {pl!r}")
            out += pl
        except (EOFError, socket.timeout, TimeoutError, OSError):
            pass
    return out


def main():
    host = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "interrupt"

    sock = connect(host)
    # login
    drain(sock, 1.5, "banner")
    send_frame(sock, "12345678\r", 0x01)
    time.sleep(0.5)
    drain(sock, 1.5, "login")

    if mode == "interrupt":
        print("== sending Ctrl+C x3 (text) ==")
        for _ in range(3):
            send_frame(sock, b"\x03", 0x01)
            time.sleep(0.3)
            drain(sock, 1.0, "intr")
        # try eval
        print("== send '2+3' ==")
        send_frame(sock, "2+3\r", 0x01)
        drain(sock, 3.0, "eval")
    elif mode == "softreset":
        print("== sending Ctrl+D ==")
        send_frame(sock, b"\x04", 0x01)
        drain(sock, 6.0, "reset")
    elif mode == "eval":
        cmd = sys.argv[3] if len(sys.argv) > 3 else "print('hello')\r"
        print("== send cmd:", repr(cmd))
        send_frame(sock, cmd, 0x01)
        drain(sock, 3.0, "eval")

    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
