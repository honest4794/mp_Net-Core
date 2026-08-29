#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# webrepl_rawrepl.py — WebREPL 的 raw REPL 模式客戶端（確定性標記 "OK"/"\x04\x04>"）。
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
        raise RuntimeError("handshake fail")
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


def send(sock, data, opcode=0x01):
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


def drain(sock, seconds, stop_on=None):
    out = b""
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            op, pl = recv_frame(sock, 0.3)
            out += pl
            if stop_on and stop_on in out:
                break
        except Exception:
            pass
    return out


def login(sock):
    # password prompt
    drain(sock, 1.0)
    send(sock, "12345678\r", 0x01)
    return drain(sock, 1.5)


def raw_exec(sock, code, timeout=6.0):
    """在 raw REPL 執行 code，回傳輸出 bytes（含 OK 標記）。"""
    # 進入 raw REPL
    send(sock, b"\x01", 0x01)
    time.sleep(0.3)
    drain(sock, 0.8)
    # 送 code + Ctrl-D 執行
    send(sock, code + "\x04", 0x01)
    out = drain(sock, timeout)
    return out


def main():
    host = sys.argv[1]
    code = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "print('OK_RAWREPL')\r\n"
    sock = connect(host)
    login(sock)
    out = raw_exec(sock, code)
    print(out.decode(errors="replace"))
    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
