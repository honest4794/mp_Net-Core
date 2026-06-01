# -*- coding: utf-8 -*-
"""WiFi 測試工具 — 對 ESP managed area 做上傳/下載/列表/刪除

用法:
  python3 wifi_test.py <ESP_IP>
  python3 wifi_test.py <ESP_IP> list
  python3 wifi_test.py <ESP_IP> upload <local_file>
  python3 wifi_test.py <ESP_IP> download <managed_name> <output>
  python3 wifi_test.py <ESP_IP> trim <managed_name>
"""

import socket, sys, os, hashlib, json, struct

PORT = 9000  # 與 slave config.json 相同

def _send(sock, cmd, payload):
    """發送封包, 接收回應"""
    data = json.dumps({"cmd": cmd, "payload": payload}).encode()
    # 使用 slave 的 packet 格式: 需要查 schema
    # 簡單版本: send + recv
    sock.send(data)
    return json.loads(sock.recv(65536).decode())


# ════════════════════════════════════════════════════════════
# 高階操作
# ════════════════════════════════════════════════════════════

def cmd_list(sock):
    r = _send(sock, 0x3001, {})
    print("Managed files:", r)

def cmd_upload(sock, local_path):
    name = os.path.basename(local_path)
    with open(local_path, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    total = (len(data) + 511) // 512

    print("Upload: {} -> {} ({} sectors, SHA256={})".format(local_path, name, total, sha[:16]))

    r = _send(sock, 0x3003, {"name": name, "sectors": total, "file_id": 1})
    if not r.get("ok"): print("fail:", r); return
    print("alloc sector:", r["sector"])

    # 分塊上傳 (16KB per chunk)
    chunk = 16384
    off = 0
    while off < len(data):
        piece = data[off:off+chunk]
        r = _send(sock, 0x3004, {"data": list(piece), "off": off // 512, "file_id": 1})
        if not r.get("ok"): print("chunk fail:", r); return
        off += chunk
        pct = min(off * 100 // len(data), 100)
        sys.stdout.write("\r  {}% ({}/{})".format(pct, off, len(data)))
        sys.stdout.flush()

    r = _send(sock, 0x3005, {"file_id": 1})
    print("\n✅ Upload ok:", r)

def cmd_download(sock, name, output):
    r = _send(sock, 0x3002, {"name": name})
    if r is None: print("not found"); return
    with open(output, "wb") as f:
        f.write(bytes(r))
    print("✅ {} -> {} ({} bytes)".format(name, output, len(r)))

def cmd_trim(sock, name):
    r = _send(sock, 0x3006, {"name": name})
    print("Trim result:", r)


# ════════════════════════════════════════════════════════════
# 主
# ════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 wifi_test.py <ip> list")
        print("  python3 wifi_test.py <ip> upload <file>")
        print("  python3 wifi_test.py <ip> download <name> [out]")
        print("  python3 wifi_test.py <ip> trim <name>")
        return

    ip = sys.argv[1]
    cmd = sys.argv[2]

    sock = socket.socket()
    sock.settimeout(30)
    sock.connect((ip, PORT))
    print("Connected to", ip)

    if cmd == "list": cmd_list(sock)
    elif cmd == "upload": cmd_upload(sock, sys.argv[3])
    elif cmd == "download": cmd_download(sock, sys.argv[3], sys.argv[4] if len(sys.argv)>4 else sys.argv[3])
    elif cmd == "trim": cmd_trim(sock, sys.argv[3])

    sock.close()

if __name__ == "__main__":
    main()
