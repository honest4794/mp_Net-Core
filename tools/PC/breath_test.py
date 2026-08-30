#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# breath_test.py — 純網絡串流「紅色呼吸」測試（頭 N 粒燈）
#
# 不依賴 NetBusMaster 主工具，直接以 NC4 協議驅動 slave 的「純網絡串流 Action」，
# 做一段紅色呼吸動畫，只點亮頭 N 粒燈（預設 10），其餘全熄。
#
# 兩條路徑（--mode）：
#   ram    產生 N 幀呼吸動畫 → 上傳 /ram/live.bin（RAM 緩衝區，不落 SD）→
#          0x3009 準備 + 0x300A 播放（play_mode=1 循環）。現行韌體即可用。
#   direct 0x3003 STREAM_FRAME 逐幀直推 pixel_data（真正的「純網絡 Action」）。
#          需要 slave 韌體含 stream.json 的 0x3003 定義，且 stream_actions._direct_mode
#          已把 streaming 旗標架起（本 repo 已同步補上，需重新燒錄韌體）。
#
# 用法範例：
#   python3 -B breath_test.py --target 80F1B2D1F63B --leds 10 --mode ram
#   python3 -B breath_test.py --target 192.168.8.225 --leds 10 --mode direct --fps 30
#
import argparse
import base64
import hashlib
import json
import math
import os
import socket
import struct
import sys
import threading
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SLAVE_DIR = os.path.join(PROJECT_ROOT, "slave")
if SLAVE_DIR not in sys.path:
    sys.path.insert(0, SLAVE_DIR)

from lib.sys.proto import Proto, StreamParser          # noqa: E402
from lib.sys.schema_loader import SchemaStore          # noqa: E402
from lib.sys.schema_codec import SchemaCodec           # noqa: E402

CONFIG_PATH = os.path.join(SCRIPT_DIR, "slave_map.json")
SCHEMA_DIR = os.path.join(SLAVE_DIR, "schema")

CMD_STREAM_FRAME = 0x3003
CMD_STREAM_INFO = 0x3001
CMD_STREAM_STATE_SET = 0x3009
CMD_STREAM_PLAY = 0x300A
CMD_STREAM_STOP = 0x3002
CMD_READY_ACK = 0x3008
CMD_DISCOVER = 0x1001
CMD_FILE_BEGIN = 0x2001
CMD_FILE_QUERY = 0x2005
CMD_FILE_CHUNK = 0x2002
CMD_FILE_END = 0x2003
CMD_FILE_ACK = 0x2004
CMD_FILE_QUERY_RSP = 0x2006
CMD_FILE_READ = 0x2007
CMD_FILE_PROMOTE = 0x2011
CMD_FILE_CONFIRM = 0x2008
CMD_REBOOT = 0x100F
CMD_STATUS_GET = 0x1101
CMD_STATUS_RSP = 0x1102

# 上傳到 /sd 暫存後才 promote 到 root（root 檔 = 韌體，如 /action/*.py、/schema/*.json）
ROOT_PREFIXES = ("/action/", "/schema/", "/lib/", "/pixel/", "/tasks/", "/boot.py",
                 "/app.py", "/Core_Manager.py")

def is_junk_name(name):
    return (name in (".DS_Store", "Thumbs.db", "desktop.ini")
            or name.startswith(("._", "~$"))
            or name.endswith((".pyc", ".pyo", ".swp", ".swo", ".tmp")))


def is_junk_dir(name):
    return name in ("__pycache__", "__MACOSX", ".Spotlight-V100", ".Trashes",
                    ".fseventsd", "$RECYCLE.BIN", "System Volume Information")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        finally:
            s.close()
    except Exception:
        pass
    return "127.0.0.1"


def load_config():
    cfg = {"ws_port": 8005, "upt_port": 9000, "mapping": {}}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg["ws_port"] = int(data.get("ws_port", 8005))
            cfg["upt_port"] = int(data.get("upt_port", 9000))
            cfg["mapping"] = data.get("mapping", {}) or {}
        except Exception as e:
            print(f"⚠️ config 載入失敗: {e}")
    return cfg


# ─────────────────── WS 接收重組（unmasked 為主，容錯 masked）───────────────────
class WSRx:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf += data
        out = []
        while True:
            n = len(self.buf)
            if n < 2:
                break
            b0 = self.buf[0]
            b1 = self.buf[1]
            plen = b1 & 0x7F
            idx = 2
            if plen == 126:
                if n < 4:
                    break
                plen = (self.buf[2] << 8) | self.buf[3]
                idx = 4
            elif plen == 127:
                if n < 10:
                    break
                plen = int.from_bytes(self.buf[2:10], "big")
                idx = 10
            masked = bool(b1 & 0x80)
            mlen = 4 if masked else 0
            if n < idx + mlen + plen:
                break
            mask = self.buf[idx:idx + mlen] if masked else None
            payload = bytes(self.buf[idx + mlen:idx + mlen + plen])
            if masked:
                payload = bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
            del self.buf[:idx + mlen + plen]
            out.append(payload)
        return out


def ws_send(conn, payload):
    payload = bytes(payload)
    l = len(payload)
    hdr = bytearray([0x82])
    if l <= 125:
        hdr.append(l)
    elif l <= 65535:
        hdr.append(126)
        hdr.extend(struct.pack(">H", l))
    else:
        hdr.append(127)
        hdr.extend(struct.pack(">Q", l))
    conn.sendall(hdr + payload)


def ws_handshake(conn):
    """讀 HTTP 握手、回 101，並解析 path 最後一段為 cid。"""
    conn.settimeout(5.0)
    data = b""
    try:
        while b"\r\n\r\n" not in data and len(data) < 8192:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    conn.settimeout(None)
    if not data or b"Upgrade: websocket" not in data:
        conn.close()
        return None

    text = data.decode(errors="ignore")
    key = None
    path = ""
    first = text.split("\r\n")[0]
    parts = first.split(" ")
    if len(parts) >= 2:
        path = parts[1].strip("/")
    for line in text.split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()

    cid = path.split("/")[-1] if path else ""
    accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="  # 對應 sample key，slave 端固定使用
    if key:
        accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode()
    resp = ("HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n")
    conn.sendall(resp.encode())
    return cid


# ─────────────────── 設備連線封裝 ───────────────────
class Device:
    def __init__(self, cid, conn, store):
        self.cid = cid
        self.conn = conn
        self.store = store
        self.parser = StreamParser()
        self.ws = WSRx()
        self.lock = threading.Lock()
        self.alive = True

        self.query_event = threading.Event()
        self.query = None          # 0x2006 回應 args
        self.ack_event = threading.Event()
        self.ack_offset = -1       # 0x2004 回應 offset
        self.ready_event = threading.Event()
        self.ready_block = None
        self.status = None         # 0x1102 status_json (dict)
        self.status_event = threading.Event()
        self.read_event = threading.Event()
        self.read_data = None
        self.read_offset = -1

    def pack(self, cmd, args):
        c_def = self.store.get(cmd)
        if c_def is None:
            raise RuntimeError(f"schema 缺少 0x{cmd:04X}")
        payload = SchemaCodec.encode(c_def, args)
        # Proto.pack 回傳共享 memoryview → 立即拷貝成 bytes 避免被覆蓋
        return bytes(Proto.pack(cmd, payload))

    def send(self, cmd, args):
        ws_send(self.conn, self.pack(cmd, args))

    def _dispatch(self, cmd, payload):
        c_def = self.store.get(cmd)
        args = SchemaCodec.decode(c_def, payload, store=self.store) if c_def else {}
        if cmd == CMD_READY_ACK:
            with self.lock:
                self.ready_block = args.get("block_id", 0)
                self.ready_event.set()
        elif cmd == 0x1102:
            try:
                with self.lock:
                    self.status = json.loads(args.get("status_json", "{}"))
                    self.status_event.set()
            except Exception:
                pass
        elif cmd == CMD_FILE_ACK:
            with self.lock:
                self.ack_offset = int(args.get("offset", -1))
                self.ack_event.set()
        elif cmd == CMD_FILE_CHUNK:   # 0x2002: 下載讀回的回應（on_file_read 回 FILE_CHUNK）
            with self.lock:
                self.read_data = args.get("data", b"")
                self.read_offset = int(args.get("offset", -1))
                self.read_event.set()
        elif cmd == CMD_FILE_QUERY_RSP:
            with self.lock:
                self.query = args
                self.query_event.set()
        elif cmd == 0x100B:
            pass  # 延遲量測回應，本測試不需
        elif cmd == 0x2010:
            with self.lock:
                self.query = args
                self.query_event.set()

    def recv_loop(self):
        try:
            while self.alive:
                raw = self.conn.recv(4096)
                if not raw:
                    break
                for frame in self.ws.feed(raw):
                    self.parser.feed(frame)
                    while True:
                        r = self.parser.pop_frame()
                        if r is None:
                            break
                        _ver, _addr, cmd, payload = r
                        self._dispatch(cmd, bytes(payload))
        except Exception:
            pass
        finally:
            self.alive = False
            try:
                self.conn.close()
            except Exception:
                pass

    def wait_query(self, timeout=5.0):
        self.query_event.clear()
        ok = self.query_event.wait(timeout)
        return (self.query, ok)


# ─────────────────── WS 服務器（收設備連回）──────────────────
class WSServer:
    def __init__(self, port, store):
        self.port = port
        self.store = store
        self.devices = {}
        self.lock = threading.Lock()
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(8)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            try:
                conn, addr = self.sock.accept()
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

    def _handle(self, conn, addr):
        cid = ws_handshake(conn)
        if not cid:
            return
        dev = Device(cid, conn, self.store)
        with self.lock:
            self.devices[cid] = dev
        print(f"👋 [Connect] {cid} 已連線 ({addr[0]})")
        dev.recv_loop()
        with self.lock:
            if self.devices.get(cid) is dev:
                del self.devices[cid]
        print(f"🔌 [Disconnect] {cid} 離線")

    def get(self, cid=None):
        with self.lock:
            if cid and cid in self.devices:
                return self.devices[cid]
            if self.devices:
                return next(iter(self.devices.values()))
        return None

    def wait_device(self, cid=None, timeout=12.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            dev = self.get(cid)
            if dev is not None:
                return dev
            time.sleep(0.2)
        return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ─────────────────── 動畫產生 ───────────────────
def build_frames(num_leds, num_pixels, num_frames, rgb=(255, 0, 0)):
    """產生 num_frames 幀紅色呼吸 (RGBA 每像素 4 bytes)。頭 num_leds 亮，其餘熄。"""
    frames = []
    r0, g0, b0 = rgb
    for i in range(num_frames):
        # (1-cos)/2: 0→1→0 平滑呼吸
        v = int(round(127.5 * (1.0 - math.cos(2.0 * math.pi * i / num_frames))))
        r = (r0 * v) // 255
        g = (g0 * v) // 255
        b = (b0 * v) // 255
        buf = bytearray(num_pixels * 4)
        for k in range(num_leds):
            o = k * 4
            buf[o] = r
            buf[o + 1] = g
            buf[o + 2] = b
            buf[o + 3] = 0
        frames.append(bytes(buf))
    return frames


# ─────────────────── 上傳 /ram (RAM 緩衝區) ───────────────────
def upload_ram(dev, data, remote_path, chunk_size=4096):
    total = len(data)
    local_sha = hashlib.sha256(data).digest()
    dev.send(CMD_FILE_BEGIN, {
        "file_id": 1,
        "total_size": total,
        "chunk_size": chunk_size,
        "sha256": local_sha,
        "path": remote_path,
    })
    # begin 握手：FILE_QUERY 回 0x2006 即表示 slave 就緒（/ram 查不到檔，exists=0 正常）
    dev.query_event.clear()
    dev.send(CMD_FILE_QUERY, {"path": remote_path})
    if not dev.query_event.wait(5.0):
        raise TimeoutError("FILE_BEGIN handshake timeout")

    for off in range(0, total, chunk_size):
        chunk = data[off:off + chunk_size]
        for _ in range(3):
            dev.ack_event.clear()
            dev.ack_offset = -1
            dev.send(CMD_FILE_CHUNK, {"file_id": 1, "offset": off, "data": chunk})
            if dev.ack_event.wait(5.0) and dev.ack_offset == off:
                break
        else:
            raise TimeoutError(f"upload ACK timeout @ {off}")
        print(f"    ↥ {min(off + len(chunk), total)}/{total} bytes")

    dev.query_event.clear()
    dev.query = None
    dev.send(CMD_FILE_END, {"file_id": 1})
    if not dev.query_event.wait(10.0):
        raise TimeoutError("FILE_END validation timeout")
    remote_sha = dev.query.get("sha256", b"")
    if remote_sha != local_sha:
        raise RuntimeError(f"SHA mismatch: {remote_sha[:8].hex()} != {local_sha[:8].hex()}")
    print(f"✅ 上傳完成 {remote_path} ({total} bytes) sha={local_sha[:8].hex()}")


# ─────────────────── 下載讀回（ram 驗證用）───────────────────
def download_readback(dev, remote_path, chunk_size=2048):
    """依 0x2007 FILE_READ 逐段讀回 remote_path。回傳 bytes。"""
    dev.query_event.clear()
    dev.query = None
    dev.send(CMD_FILE_QUERY, {"path": remote_path})
    if not dev.query_event.wait(5.0) or dev.query is None:
        raise TimeoutError("查詢檔案大小逾時")
    size = int(dev.query.get("size", 0) or 0)
    buf = bytearray()
    offset = 0
    while offset < size:
        req_len = min(chunk_size, size - offset)
        got = None
        for _ in range(3):
            dev.read_event.clear()
            dev.read_data = None
            dev.read_offset = -1
            dev.send(0x2007, {"path": remote_path, "offset": offset, "length": req_len})
            if dev.read_event.wait(5.0) and dev.read_offset == offset:
                got = bytes(dev.read_data or b"")
                break
        if got is None:
            raise TimeoutError(f"readback timeout @ {offset}")
        if not got:
            break
        buf.extend(got)
        offset += len(got)
    return bytes(buf)


# ─────────────────── 串流控制 ───────────────────
def stream_prepare(dev, file_name, play_mode):
    dev.ready_event.clear()
    dev.send(CMD_STREAM_STATE_SET, {"file_name": file_name, "block_id": 0, "play_mode": play_mode})
    dev.ready_event.wait(3.0)   # 0x3008 READY_ACK（不強制等，最好都發了）


def stream_play(dev, start_frame=0, fps=None):
    if fps and fps > 0:
        dev.send(CMD_STREAM_INFO, {"total_blocks": 0, "frames_per_block": 0, "fps": int(fps)})
    dev.send(CMD_STREAM_PLAY, {"start_frame": start_frame})


# ─────────────────── OTA 部署：上傳 → promote → confirm ───────────────────
def upload_bytes(dev, data, remote_path, file_id=1, chunk_size=4096, quiet=False):
    """上傳 bytes 到 remote_path（/ram 或 /sd 暫存）。回傳本地 sha256 digest bytes。"""
    total = len(data)
    local_sha = hashlib.sha256(data).digest()
    dev.send(CMD_FILE_BEGIN, {
        "file_id": file_id, "total_size": total, "chunk_size": chunk_size,
        "sha256": local_sha, "path": remote_path,
    })
    dev.query_event.clear()
    dev.send(CMD_FILE_QUERY, {"path": remote_path})
    if not dev.query_event.wait(5.0):
        raise TimeoutError(f"FILE_BEGIN handshake timeout ({remote_path})")
    for off in range(0, total, chunk_size):
        chunk = data[off:off + chunk_size]
        for _ in range(3):
            dev.ack_event.clear()
            dev.ack_offset = -1
            dev.send(CMD_FILE_CHUNK, {"file_id": file_id, "offset": off, "data": chunk})
            if dev.ack_event.wait(5.0) and dev.ack_offset == off:
                break
        else:
            raise TimeoutError(f"upload ACK timeout @ {off}")
    dev.query_event.clear()
    dev.query = None
    dev.send(CMD_FILE_END, {"file_id": file_id})
    if not dev.query_event.wait(10.0):
        raise TimeoutError(f"FILE_END validation timeout ({remote_path})")
    remote_sha = dev.query.get("sha256", b"")
    if remote_sha != local_sha:
        raise RuntimeError(f"SHA mismatch {remote_path}: {remote_sha[:8].hex()} != {local_sha[:8].hex()}")
    if not quiet:
        print(f"    ✅ {remote_path} ({total} bytes)")
    return local_sha


def deploy_firmware(dev, changed_files, quiet=False):
    """把「變更檔案」上傳並 promote 到 root（只傳差異，會先下載設備 manifest 比對）。

    changed_files: None = 自動比對（下載 /manifest.json）; 或 [(local_path, remote_path), ...]
    回傳 promote 成功的 root 路徑清單（尚未 confirm）。
    """
    if changed_files is None:
        # 下載設備 manifest → 比對本地 slave/ 目錄
        man = download_manifest(dev)
        files = collect_firmware_files()
        changed_files = []
        for l_path, r_path in files:
            if man is None or man.get(r_path) != sha_hex(l_path):
                changed_files.append((l_path, r_path))
        print(f"📊 比對: 設備 {'無 manifest(全傳)' if man is None else '有 manifest'}，"
              f"{len(changed_files)}/{len(files)} 個檔需要更新")

    if not changed_files:
        print("✅ 固件與本地一致，無需更新")
        return []

    promoted = []
    for idx, (l_path, r_path) in enumerate(changed_files, 1):
        print(f"  ↥ [{idx}/{len(changed_files)}] {r_path}")
        with open(l_path, "rb") as f:
            data = f.read()
        # root 檔先上傳到 /sd 暫存再 promote；/sd/... 直接留在 SD
        if r_path.startswith("/sd"):
            upload_bytes(dev, data, r_path, file_id=idx + 1)
        else:
            upload_bytes(dev, data, "/sd" + r_path, file_id=idx + 1)
            dev.query_event.clear()
            dev.query = None
            dev.send(CMD_FILE_PROMOTE, {"src": "/sd" + r_path, "dst": r_path})
            if dev.query_event.wait(5.0):
                print(f"    📦 promote → {r_path}")
                promoted.append(r_path)
            else:
                print(f"    ⚠️ promote 逾時: {r_path}")

    # 全部 promote 完後 confirm（刪 .bak + 清 pending，正式生效）
    for r_path in promoted:
        dev.query_event.clear()
        dev.send(CMD_FILE_CONFIRM, {"path": r_path})
        dev.query_event.wait(3.0)
    print(f"✅ 部署完成: 上傳 {len(changed_files)} / promote+confirm {len(promoted)}")
    return promoted


def collect_firmware_files():
    """掃描本地 slave/ 目錄 → [(local_path, remote_path)]（過濾垃圾檔與 config.json）。"""
    files = []
    for root, dirs, names in os.walk(SLAVE_DIR):
        dirs[:] = [d for d in dirs if not is_junk_dir(d)]
        for name in names:
            if name == "config.json" or is_junk_name(name):
                continue
            lp = os.path.join(root, name)
            rp = "/" + os.path.relpath(lp, SLAVE_DIR).replace(os.sep, "/")
            files.append((lp, rp))
    return files


def sha_hex(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_manifest(dev):
    """下載設備 /manifest.json → {path: sha_hex}。失敗回 None。"""
    try:
        data = download_readback(dev, "/manifest.json")
        obj = json.loads(data.decode("utf-8"))
        out = {}
        for p, info in obj.items():
            if isinstance(info, dict) and "h" in info:
                out[p] = info["h"]
            elif isinstance(info, dict) and "sha256" in info:
                out[p] = info["sha256"]
        return out
    except Exception:
        return None


def reboot_and_wait(server, cid, ip, wait=90, ws_port=None, upt_port=None):
    """0x100F 軟重啟 → 等設備自動連回。回傳重連後的 Device 或 None。"""
    dev = server.get(cid)
    if dev is None:
        print("❌ 設備已離線，無法送出重啟指令")
        return None
    print(f"🔁 [Reboot] {cid} 送出 0x100F ...")
    dev.send(CMD_REBOOT, {"delay_ms": 500})

    print(f"⏳ 等待設備重啟回連（最多 {wait}s）...")
    deadline = time.time() + wait
    old_conn = id(dev.conn)
    while time.time() < deadline:
        time.sleep(0.5)
        cur = server.get(cid)
        if cur is not None and id(cur.conn) != old_conn:
            print(f"   ✅ {cid} 已回連（新連線）")
            time.sleep(1.0)   # 讓 slave 開機初始化完
            return cur
    # 回連前可能連線已斷、server 已移除舊 device；若同 cid 重新註冊即視為新連線
    cur = server.get(cid)
    if cur is not None and id(cur.conn) != old_conn:
        print(f"   ✅ {cid} 已回連（新連線）")
        return cur
    print(f"   ⚠️ {cid} 未在 {wait}s 內回連（可再敲門嘗試）")
    return None


def query_status(dev, timeout=3.0):
    dev.status_event.clear()
    dev.status = None
    dev.send(CMD_STATUS_GET, {"query_type": 0})
    if dev.status_event.wait(timeout):
        return dev.status
    return None


def knock(ips, upt_port, local_ip, ws_port, store):
    """0x1001 DISCOVER 敲門，叫設備連回。"""
    d_def = store.get(CMD_DISCOVER)
    disc = bytes(Proto.pack(CMD_DISCOVER, SchemaCodec.encode(
        d_def, {"server_ip": local_ip, "ws_url": f"ws://{local_ip}:{ws_port}"})))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for ip in ips:
            try:
                s.sendto(disc, (ip, upt_port))
                print(f"    → DISCOVER {ip}:{upt_port}")
            except Exception as e:
                print(f"    ⚠️ {ip} 發送失敗: {e}")
        s.close()
    except Exception as e:
        print(f"⚠️ knock 失敗: {e}")


def broadcast_discover(upt_port, local_ip, ws_port, store, rounds=3, gap=0.6):
    """廣播 0x1001 DISCOVER 到全域 + 子網廣播，叫同網段設備全部連回（不看 slave_map 舊紀錄）。"""
    d_def = store.get(CMD_DISCOVER)
    disc = bytes(Proto.pack(CMD_DISCOVER, SchemaCodec.encode(
        d_def, {"server_ip": local_ip, "ws_url": f"ws://{local_ip}:{ws_port}"})))
    parts = local_ip.split(".")
    parts[-1] = "255"
    subnet_bcast = ".".join(parts)
    targets = ["255.255.255.255", subnet_bcast]
    print(f"📡 廣播 DISCOVER → {targets} (UDP {upt_port}, ws_url ws://{local_ip}:{ws_port})")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for r in range(rounds):
            for ip in targets:
                try:
                    s.sendto(disc, (ip, upt_port))
                    print(f"    → {ip}:{upt_port} (round {r+1}/{rounds})")
                except Exception as e:
                    print(f"    ⚠️ {ip} 發送失敗: {e}")
            time.sleep(gap)
    except Exception as e:
        print(f"❌ 廣播失敗: {e}")
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser(description="純網絡串流紅色呼吸測試（頭 N 粒）")
    ap.add_argument("--target", help="設備 cid 或 ip（省略則敲所有已記錄 IP 並接受第一台）")
    ap.add_argument("--leds", type=int, default=10, help="點亮的頭幾粒燈（預設 10）")
    ap.add_argument("--pixels", type=int, default=676, help="整機像素數 = 幀長/4（預設 676 = P4）")
    ap.add_argument("--frames", type=int, default=60, help="每段呼吸的幀數（預設 60）")
    ap.add_argument("--fps", type=int, default=30, help="幀率（預設 30）")
    ap.add_argument("--duration", type=float, default=12.0, help="測試秒數（預設 12）")
    ap.add_argument("--mode", choices=["ram", "direct"], default="ram",
                    help="ram=上傳 /ram 循環播放（現行韌體可用）; direct=0x3003 逐幀直推")
    ap.add_argument("--verify", action="store_true",
                    help="ram 模式上傳後先讀回 /ram 內容做位元組比對，再開始播放")
    ap.add_argument("--deploy", action="store_true",
                    help="先 OTA 部署變更的固件（上傳+promote+confirm）並 0x100F 重啟，再開始測試")
    ap.add_argument("--files", default=None,
                    help="--deploy 時只推指定遠端路徑（逗號分隔，例 /schema/stream.json,/action/stream_actions.py）；"
                         "省略則自動比對設備 manifest 傳差異")
    ap.add_argument("--no-reboot", action="store_true",
                    help="--deploy 部署後不重啟（僅推送檔案）")
    ap.add_argument("--scan", action="store_true",
                    help="只廣播發現並列舉回連設備，不做任何測試")
    ap.add_argument("--ws-port", type=int, default=None, help="本機 WS 埠（預設讀 slave_map）")
    ap.add_argument("--upt-port", type=int, default=None, help="UDP discovery 埠（預設讀 slave_map）")
    args = ap.parse_args()

    cfg = load_config()
    ws_port = args.ws_port or cfg["ws_port"]
    upt_port = args.upt_port or cfg["upt_port"]
    local_ip = get_local_ip()

    store = SchemaStore(dir_path=SCHEMA_DIR)
    store.finalize()
    # 防呆：schema 若缺 0x3003（舊韌體），PC 端仍可編碼
    if store.get(CMD_STREAM_FRAME) is None:
        store.cmd_map[CMD_STREAM_FRAME] = {
            "cmd": "0x3003", "name": "STREAM_FRAME",
            "payload": [{"name": "pixel_data", "type": "bytes_rest"}],
        }
        store.finalize()

    # ── 目標解析 ──
    target_cid = None
    knock_ips = []
    mapping = cfg.get("mapping", {})
    if args.target:
        if args.target in mapping:
            target_cid = args.target
            ip = (mapping[args.target] or {}).get("ip", "")
            if ip:
                knock_ips = [ip]
            print(f"🎯 目標: {target_cid} (ip={ip or '?'})")
        else:
            knock_ips = [args.target]
            print(f"🎯 目標 ip: {args.target}")

    # ── 起 WS 服務器 ──
    server = WSServer(ws_port, store)
    server.start()
    print(f"🌐 WS 監聽 0.0.0.0:{ws_port} (本機 {local_ip})")

    # ── 發現 (DISCOVER)：有指定目標走 unicast；否則廣播同網段，不看 slave_map 舊紀錄 ──
    if args.target:
        knock(knock_ips, upt_port, local_ip, ws_port, store)
    else:
        broadcast_discover(upt_port, local_ip, ws_port, store)

    # 等設備回連並列舉
    if args.scan:
        deadline = time.time() + 15.0
        shown = set()
        while time.time() < deadline:
            with server.lock:
                cids = list(server.devices.keys())
            for c in cids:
                if c not in shown:
                    shown.add(c)
                    print(f"   ✅ 設備回連: {c}")
            time.sleep(0.5)
        with server.lock:
            cids = list(server.devices.keys())
        print(f"\n📊 共 {len(cids)} 台設備在線: {', '.join(cids) if cids else '(無)'}")
        server.close()
        return 0

    dev = server.wait_device(target_cid, timeout=15.0)
    if dev is None:
        print(f"❌ 15 秒內沒有設備回連 (cid={target_cid or 'any'})")
        server.close()
        return 1
    if target_cid is None:
        target_cid = dev.cid
    print(f"🎯 使用設備: {target_cid}")

    # ── 可選：OTA 部署固件 + 重啟（全部走網絡，不需 USB）──
    if args.deploy:
        if args.files:
            changed = []
            for p in args.files.split(","):
                p = p.strip()
                if not p:
                    continue
                lp = os.path.join(SLAVE_DIR, p.lstrip("/").replace("/", os.sep))
                if not os.path.isfile(lp):
                    print(f"❌ 本地找不到 {lp}")
                    server.close()
                    return 1
                changed.append((lp, p))
            print(f"\n🔧 [Deploy] 指定 {len(changed)} 個檔案 ...")
            deploy_target = changed
        else:
            print("\n🔧 [Deploy] 下載設備 manifest 並比對本地 slave/ 目錄 ...")
            deploy_target = None
        try:
            promoted = deploy_firmware(dev, deploy_target)
        except Exception as e:
            print(f"❌ 部署失敗: {e}")
            server.close()
            return 1
        if promoted and not args.no_reboot:
            dev_ip = knock_ips[0] if knock_ips else None
            dev = reboot_and_wait(server, target_cid, dev_ip, ws_port=ws_port, upt_port=upt_port)
            if dev is None:
                print("⚠️ 重啟後未回連；嘗試再敲門一次 ...")
                if dev_ip:
                    knock([dev_ip], upt_port, local_ip, ws_port, store)
                else:
                    broadcast_discover(upt_port, local_ip, ws_port, store, rounds=1)
                dev = server.wait_device(target_cid, timeout=20.0)
                if dev is None:
                    print("❌ 設備仍未回連，無法繼續測試")
                    server.close()
                    return 1
        elif promoted and args.no_reboot:
            print("ℹ️ --no-reboot：已推送檔案但未重啟（新韌體未生效）")

    frames = build_frames(args.leds, args.pixels, args.frames)

    try:
        if args.mode == "ram":
            data = b"".join(frames)
            print(f"🚀 [RAM] 產生 {args.frames} 幀 × {args.pixels}px = {len(data)} bytes，上傳 /ram/live.bin ...")
            upload_ram(dev, data, "/ram/live.bin")
            if args.verify:
                print("🔍 讀回 /ram/live.bin 驗證 ...")
                back = download_readback(dev, "/ram/live.bin")
                if back == data:
                    print(f"✅ 讀回驗證 OK ({len(back)} bytes 完全一致)")
                else:
                    print(f"⚠️ 讀回長度 {len(back)} != 上傳 {len(data)}，播放仍會進行")
            print("▶ prepare + play (play_mode=1 循環)")
            stream_prepare(dev, "/ram/live.bin", play_mode=1)
            stream_play(dev, start_frame=0, fps=args.fps)
        else:
            print(f"🚀 [Direct] 0x3003 逐幀直推 {args.frames} 幀 @ {args.fps}fps")
            # 先停止既有串流，確保 StreamTask 回到 IDLE、direct mode 獨佔
            dev.send(CMD_STREAM_STOP, {})
            time.sleep(0.3)
            dev.send(CMD_STREAM_INFO, {"total_blocks": 0, "frames_per_block": 0, "fps": args.fps})
            interval = 1.0 / args.fps

        print(f"⏱ 呼吸測試進行中（{args.duration}s），Ctrl+C 中斷")
        t0 = time.time()
        i = 0
        try:
            while time.time() - t0 < args.duration and dev.alive:
                if args.mode == "direct":
                    dev.send(CMD_STREAM_FRAME, {"pixel_data": frames[i % args.frames]})
                    time.sleep(interval)
                    i += 1
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass

        dev.send(CMD_STREAM_STOP, {})
        print("🛑 已停止 (0x3002)")
    finally:
        server.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
