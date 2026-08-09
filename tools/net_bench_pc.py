#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESP32-P4 上載極限網速基準測試 — PC 端 (CPython)

配對檔: test/bench_net.py (ESP32-P4 端, MicroPython)。

角色: 起 TCP server 等 ESP 連入 + 同時 UDP 廣播 beacon 讓 ESP 自動找到本機。
收到 ESP 的上載洪流時用預分配 buffer + conn.recv_into 計時量測 (低分配),
全程不過任何協議框架 —— 要測晶片的網路上載極限就必須裸 TCP。

協定 (與 ESP 端 test/bench_net.py 對齊, 單條 TCP 控制行 + 已知長度裸資料):
    ESP→PC:  "BEGIN <chunk> <total>\n"   控制行 (非熱路徑)
    ESP→PC:  <total bytes>               裸洪流 (PC 計時收滿)
    ESP→PC:  "RESULT <chunk> <bytes> <esp_ms> <esp_mem_delta>\n"
    ESP→PC:  "SKIP <chunk>\n"            (該 chunk 失敗時)
    ESP→PC:  "ENDALL\n"                  全部結束

自動連線: PC 啟動 → 起 TCP server(data_port) → 每 0.5s 廣播 UDP beacon
  到 255.255.255.255:disc_port, 內含本機 IP + data_port + 測試參數。
  ESP 收到後 TCP connect 過來 (從 sender addr 拿 PC IP, 不靠 beacon 文字)。

用法:
  python3 tools/net_bench_pc.py                     # 預設: 4MB×3, 全 chunk
  python3 tools/net_bench_pc.py --total 2048        # 每筆 2 MB
  python3 tools/net_bench_pc.py --runs 5            # 每 chunk 跑 5 次取最佳
  python3 tools/net_bench_pc.py --chunks 4096,16384 # 只測指定 chunk
  python3 tools/net_bench_pc.py --data-port 6001 --disc-port 9000
  python3 tools/net_bench_pc.py --once              # 只接一台就收工
"""

import argparse
import json
import os
import socket
import struct
import sys
import threading
import time

# 讓 PC 端能 import slave/lib/proto 的 Proto.pack (CPython 可用)。
# 注意: slave 的 StreamParser 用了 viper (MicroPython 專屬), CPython 跑會壞 —
# 所以 PC 端只 import Proto.pack, StreamParser 用下面的純 Python 版 PyStreamParser。
_SLAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "slave"))
if _SLAVE_DIR not in sys.path:
    sys.path.insert(0, _SLAVE_DIR)
try:
    from lib.proto import Proto
    _HAVE_PROTO = True
except Exception as _e:
    _HAVE_PROTO = False
    Proto = None
    sys.stderr.write("⚠️ 無法 import lib.proto ({}), NL3 協議模式將不可用\n".format(_e))


# NL3 幀常數 (與 slave/lib/proto.py 對齊)
_NL_SOF = b"NL"
_NL_VER = 4
_NL_HDR_LEN = 9
_NL_CRC_LEN = 4


class PyStreamParser:
    """純 Python 版 NL3 StreamParser (不依賴 viper), 供 PC 端 CPython 用。
    邏輯完全對齊 slave/lib/proto.py 的 StreamParser: 掃 SOF → 驗 ver/len → 驗 CRC32 → yield。
    用可增長的 bytearray 累積, 不像 viper 版有固定環形緩衝 (CPython 記憶體夠, 簡單就好)。"""
    import binascii as _ba

    def __init__(self, max_len=65535):
        self.max_len = max_len
        self._buf = bytearray()

    def feed(self, data):
        if data:
            self._buf.extend(data)
        # 防止無限增長: 只保留未解析部分, 超過合理上限就清 (對齊 viper 版 reset 行為)
        if len(self._buf) > self.max_len + _NL_HDR_LEN + _NL_CRC_LEN + 4096:
            self._buf = self._buf[-(self.max_len + _NL_HDR_LEN + _NL_CRC_LEN):]

    def pop(self):
        """generator: yield (ver, addr, cmd, payload)。CRC 驗證失敗的幀跳過 (對齊 slave 行為)。"""
        while (len(self._buf) - 0) >= _NL_HDR_LEN:
            idx = self._buf.find(_NL_SOF)
            if idx < 0:
                self._buf = bytearray()
                return
            if idx > 0:
                del self._buf[:idx]   # 丟掉 SOF 前的垃圾
            if len(self._buf) < _NL_HDR_LEN:
                return
            s = 0
            ver = self._buf[s + 2]
            addr = self._buf[s + 3] | (self._buf[s + 4] << 8)
            cmd = self._buf[s + 5] | (self._buf[s + 6] << 8)
            ln = self._buf[s + 7] | (self._buf[s + 8] << 8)
            if ver != _NL_VER or ln > self.max_len:
                del self._buf[:1]   # 跳 1 byte 重新同步
                continue
            total_len = _NL_HDR_LEN + ln + _NL_CRC_LEN
            if len(self._buf) < total_len:
                return   # 還沒收滿一幀, 等更多資料
            payload_start = _NL_HDR_LEN
            payload_end = payload_start + ln
            crc_recv = (self._buf[payload_end] | (self._buf[payload_end + 1] << 8)
                        | (self._buf[payload_end + 2] << 16)
                        | (self._buf[payload_end + 3] << 24))
            # CRC 範圍: ver..payload_end (不含 SOF), 對齊 slave proto.py
            crc_calc = self._ba.crc32(bytes(self._buf[2:payload_end]), 0) & 0xFFFFFFFF
            if crc_calc == crc_recv:
                payload = bytes(self._buf[payload_start:payload_end])
                del self._buf[:total_len]
                yield ver, addr, cmd, payload
            else:
                del self._buf[:1]   # CRC 錯, 跳 1 byte 重新同步

# 虛擬測試 cmd (與 ESP 端 test/bench_net.py 一致, 0x18F0 不衝突 ram_bench)
_CMD_BENCH_PROTO = 0x18F0

# ── 預設參數 (ESP 端也有同名預設, 兩邊需一致) ──
DEFAULT_CHUNK_SIZES = (2048, 4096, 8192, 16384, 32768)
DEFAULT_TOTAL_KB = 4 * 1024          # 每筆 4 MB
DEFAULT_RUNS = 3                     # 每 chunk 重複次數 (ESP 取最佳, PC 同步報中位數)
DEFAULT_DATA_PORT = 5001             # PC 資料 TCP server 埠
DEFAULT_DISC_PORT = 9000             # UDP beacon 埠 (對齊 ESP config System.discovery_port)
DEFAULT_RX_BUF = 65536               # PC 接收緩衝 (recv_into 用; 低分配, 一次配滿)
LINK_WAIT_S = 120                    # 等 ESP 連入最長秒數
BEACON_INTERVAL = 0.5                # beacon 廣播間隔 (秒)


# ═══════════════════════════════════════════════════════════════
#  helper
# ═══════════════════════════════════════════════════════════════

def fmt_bytes(n):
    if n >= 1048576:
        return "{:.1f} MB".format(n / 1048576)
    if n >= 1024:
        return "{:.0f} KB".format(n / 1024)
    return "{} B".format(n)


def mb_s(total_bytes, elapsed_s):
    if elapsed_s <= 0:
        elapsed_s = 1e-6
    return total_bytes / (elapsed_s * 1048576)


def speed_bar(mb):
    if mb >= 22:
        return "  ████████"
    if mb >= 16:
        return "  ██████"
    if mb >= 10:
        return "  ████"
    if mb >= 4:
        return "  ██"
    return ""


def get_local_ip():
    """透過 UDP connect 8.8.8.8 取本機出口 IP (不真的發送)。同 pc_test_tool.py 技巧。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
#  UDP beacon 廣播台 (背景線程)
# ═══════════════════════════════════════════════════════════════

class Beacon(threading.Thread):
    """每 BEACON_INTERVAL 秒廣播一次 beacon 到 <broadcast>:disc_port。

    ESP 從 sender addr 拿 PC IP, 故 beacon 內容主要是參數; IP 欄位只是備援。
    """

    def __init__(self, local_ip, data_port, disc_port, params):
        super().__init__(daemon=True)
        self.local_ip = local_ip
        self.data_port = data_port
        self.disc_port = disc_port
        self.params = params
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        payload = json.dumps({
            "type": "netbench",
            "ip": self.local_ip,
            "data_port": self.data_port,
            "total_kb": self.params["total_kb"],
            "chunk_sizes": list(self.params["chunk_sizes"]),
            "runs": self.params["runs"],
        }).encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            while not self._stop.is_set():
                try:
                    s.sendto(payload, ("255.255.255.255", self.disc_port))
                except OSError:
                    pass
                self._stop.wait(BEACON_INTERVAL)
        finally:
            s.close()


# ═══════════════════════════════════════════════════════════════
#  控制/資料流處理 (與 ESP test/bench_net.py 協定對齊)
# ═══════════════════════════════════════════════════════════════

class LineReader:
    """從 TCP 連線讀行 (控制路徑用)。資料洪流期不用它, 走 recv_into。"""

    def __init__(self, conn):
        self.conn = conn
        self.buf = bytearray()

    def readline(self, timeout=5.0):
        """讀一行 (含 \\n)。timeout 內沒拿到回 None。"""
        deadline = time.monotonic() + timeout
        self.conn.settimeout(0.5)
        while time.monotonic() < deadline:
            try:
                b = self.conn.recv(1)
            except socket.timeout:
                continue
            except OSError:
                return None
            if not b:
                return None
            self.buf.extend(b)
            if b == b"\n":
                line = bytes(self.buf)
                del self.buf[:]
                return line
        return None


def recv_exact(conn, total, rx_buf, crc_acc=None):
    """收滿 total bytes 進可重用 rx_buf, 回傳 (received, elapsed_s, crc)。

    用 recv_into(rx_buf, ...) 低分配 (CPython recv_into 不分配新 bytes,
    寫入既有 bytearray)。滿了即停。

    crc_acc 若傳入一個 [int] (單元素 list), 則收資料的同時增量算 CRC32
    (每次 recv_into 後 crc32(rx_buf[:n], prev)), 收完得到整段 total 的 CRC。
    用於驗證: ESP 送端也算了同一段的 CRC, 兩邊比對確認內容無誤。"""
    received = 0
    crc = 0 if crc_acc is not None else None
    t0 = time.monotonic()
    while received < total:
        want = min(len(rx_buf), total - received)
        try:
            n = conn.recv_into(rx_buf, want)
        except socket.timeout:
            continue
        except OSError as e:
            sys.stderr.write("\n  recv_into 錯誤 after {}B: {}\n".format(received, e))
            break
        if n == 0:
            sys.stderr.write("\n  對端關閉 after {}B\n".format(received))
            break
        if crc_acc is not None:
            import binascii
            crc = binascii.crc32(rx_buf[:n], crc) & 0xFFFFFFFF
        received += n
    elapsed = time.monotonic() - t0
    if crc_acc is not None:
        crc_acc[0] = crc & 0xFFFFFFFF
    return received, elapsed


def precompute_crc(tx_mv, total):
    """預算「tx_mv 重複到 total」整段的 CRC32 (串接式, 與 ESP 收端演算法一致)。
    在計時區間外呼叫, 不污染下載吞吐計時。給 ESP 收端比對驗證用。"""
    import binascii
    chunk = len(tx_mv)
    crc = 0
    sent = 0
    while sent < total:
        rem = total - sent
        seg = tx_mv if rem >= chunk else tx_mv[:rem]
        crc = binascii.crc32(seg, crc) & 0xFFFFFFFF
        sent += len(seg)
    return crc


def send_exact(conn, tx_mv, total):
    """把 tx_mv 重複送滿 total bytes (PC→ESP 下載方向)。回傳 (sent, elapsed_s)。
    用 conn.sendall(memoryview 切片) 低分配。total 夠大時 sendall 自然背壓。

    註: CRC 驗證由 precompute_crc 在計時外預算 (送端內容固定, 無需行內算);
    行內算 CRC 會把 PC 送端拖慢, 污染下載吞吐計時。"""
    chunk = len(tx_mv)
    sent = 0
    t0 = time.monotonic()
    while sent < total:
        rem = total - sent
        seg = tx_mv if rem >= chunk else tx_mv[:rem]
        try:
            conn.sendall(seg)
        except OSError as e:
            sys.stderr.write("\n  sendall 錯誤 after {}B: {}\n".format(sent, e))
            break
        sent += len(seg)
    elapsed = time.monotonic() - t0
    return sent, elapsed


# ═══════════════════════════════════════════════════════════════
#  NL3 協議模式 (與 ESP 端 test/bench_net.py 對齊)
# ═══════════════════════════════════════════════════════════════

def _make_proto_payload(seq, seg):
    """模擬 NL3 schema payload: u16 seq + bytes_rest data。與 ESP 端一致。"""
    return struct.pack("<H", seq & 0xFFFF) + bytes(seg)


def recv_proto_exact(conn, rx_buf, total, parser):
    """NL3 協議上載接收: 用 StreamParser.feed/pop 拆 ESP 送的 NL3 幀。
    回傳 (received_data_bytes, elapsed_s, frames)。
    received = 解出的 payload data 累計 (扣掉每幀 seq 2B 前綴)。"""
    received = 0
    frames = 0
    t0 = time.monotonic()
    while received < total:
        try:
            n = conn.recv_into(rx_buf)
        except socket.timeout:
            continue
        except OSError as e:
            sys.stderr.write("\n  recv_into 錯誤: {}\n".format(e))
            break
        if n == 0:
            break
        parser.feed(rx_buf[:n])
        for _ver, _addr, _cmd, payload in parser.pop():
            received += len(payload) - 2   # 扣 seq 前綴
            frames += 1
            if received >= total:
                break
    elapsed = time.monotonic() - t0
    return received, elapsed, frames


def send_proto_exact(conn, tx_mv, total):
    """NL3 協議下載發送: 用 Proto.pack 封裝每個 chunk 送給 ESP (ESP 用 StreamParser 拆)。
    回傳 (sent_data_bytes, elapsed_s, frames)。"""
    chunk = len(tx_mv)
    sent = 0
    seq = 0
    frames = 0
    t0 = time.monotonic()
    while sent < total:
        rem = total - sent
        seg = tx_mv if rem >= chunk else tx_mv[:rem]
        payload = _make_proto_payload(seq, seg)
        pkt = Proto.pack(_CMD_BENCH_PROTO, payload)
        try:
            conn.sendall(pkt)
        except OSError as e:
            sys.stderr.write("\n  sendall 錯誤: {}\n".format(e))
            break
        sent += len(seg)
        seq = (seq + 1) & 0xFFFF
        frames += 1
    elapsed = time.monotonic() - t0
    return sent, elapsed, frames


def handle_esp(conn, addr, params):
    """與一台 ESP 的完整量測對話 (上載 + 下載)。

    回傳 dict: {"up": [...], "dl": [...]}, 每筆 {chunk, total, pc_mb, esp_ms, esp_mb, esp_mem}。
    協定 (與 ESP test/bench_net.py 對齊):
      上載 BEGIN/DL_RESULT: ESP 送洪流, PC recv_into 收
      下載 DL_BEGIN/DL_RESULT: PC 送洪流 (send_exact), ESP recv_into 收
    """
    rx_buf = bytearray(DEFAULT_RX_BUF)
    # 下載方向用一塊預填的送出 buffer (與 ESP 的 max_chunk 對齊, 取最大 chunk)
    max_chunk = max(params["chunk_sizes"]) if params["chunk_sizes"] else DEFAULT_RX_BUF
    tx_buf = bytearray(max_chunk)
    for i in range(max_chunk):
        tx_buf[i] = i & 0xFF
    tx_mv = memoryview(tx_buf)
    reader = LineReader(conn)

    # 握手: 送 HELLO
    conn.settimeout(5.0)
    try:
        conn.sendall(b"HELLO\n")
    except OSError as e:
        sys.stderr.write("送 HELLO 失敗: {}\n".format(e))
        return {"up": [], "dl": []}

    # 設較長接收超時 (洪流期間中間不會有控制訊息)
    conn.settimeout(30.0)

    results = {"up": [], "dl": []}
    while True:
        line = reader.readline(timeout=60.0)
        if line is None:
            sys.stderr.write("\n  控制行讀取超時/斷線\n")
            break
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        tag = parts[0]

        if tag == b"ENDALL":
            break

        if tag == b"SKIP":
            chunk = int(parts[1]) if len(parts) > 1 else -1
            print("  {:>8s}  ─ ESP 回報失敗, 跳過".format(fmt_bytes(chunk)))
            continue

        if tag in (b"BEGIN", b"DL_BEGIN", b"P_BEGIN", b"P_DL_BEGIN"):
            proto_mode = tag.startswith(b"P_")
            direction = "dl" if tag in (b"DL_BEGIN", b"P_DL_BEGIN") else "up"
            chunk = int(parts[1])
            total = int(parts[2])

            if proto_mode:
                # NL3 協議模式: Proto.pack 封裝 + StreamParser 拆幀
                if direction == "dl":
                    sent, elapsed, frames = send_proto_exact(conn, tx_mv[:chunk], total)
                    pc_ok = (sent == total)
                    got = sent
                    verify = "{}幀".format(frames)
                else:
                    # 上載: PC 用 StreamParser 拆 ESP 送的 NL3 幀
                    parser = PyStreamParser(max_len=max(total, 65536) + 16)
                    got, elapsed, frames = recv_proto_exact(conn, rx_buf, total, parser)
                    pc_ok = (got == total)
                    verify = "{}幀".format(frames)
            else:
                # 裸 TCP 模式
                crc_box = [0] if direction == "up" else None
                if direction == "dl":
                    pc_crc = precompute_crc(tx_mv[:chunk], total)
                    sent, elapsed = send_exact(conn, tx_mv[:chunk], total)
                    pc_ok = (sent == total)
                    got = sent
                else:
                    got, elapsed = recv_exact(conn, total, rx_buf, crc_acc=crc_box)
                    pc_crc = crc_box[0]
                    pc_ok = (got == total)
                verify = None

            # 下一行應為 RESULT/DL_RESULT/P_RESULT/P_DL_RESULT
            result_tags = ([b"RESULT", b"DL_RESULT"] if not proto_mode
                           else [b"P_RESULT", b"P_DL_RESULT"])
            esp_ms = None
            esp_mem = None
            esp_extra = None   # 裸 TCP: CRC; 協議: frame_count
            rline = reader.readline(timeout=30.0)
            if rline and rline.strip().split()[:1] and rline.split()[0:1][0] in result_tags + [b"RESULT", b"DL_RESULT"]:
                rp = rline.split()
                if len(rp) >= 5:
                    esp_ms = int(rp[3])
                    esp_mem = int(rp[4])
                if len(rp) >= 6:
                    try:
                        esp_extra = int(rp[5])
                    except ValueError:
                        esp_extra = None

            if not pc_ok:
                print("  [{:>2s}] {:>8s}  ✗ 量不符: {}={} exp={}".format(
                    direction, fmt_bytes(chunk), "sent" if direction == "dl" else "got",
                    got, total))
                continue

            # 驗證標記: 裸 TCP 比 CRC; 協議比 frame_count (PC 收到的幀數 == ESP 送出的)
            if proto_mode:
                verify_ok = (esp_extra is not None and frames == esp_extra)
                verify_mark = "{}幀 {}".format(frames, "✓" if verify_ok else "✗(ESP {})".format(esp_extra))
            else:
                verify_ok = (esp_extra is not None and esp_extra == pc_crc)
                verify_mark = "CRC {}".format("✓" if verify_ok else "✗")

            pc_mb = mb_s(total, elapsed)
            esp_mb = mb_s(total, esp_ms / 1000.0) if esp_ms is not None else None
            gc_tag = "✅" if esp_mem == 0 else "⚠️+{}".format(esp_mem)

            esp_str = "{:6.2f} MB/s".format(esp_mb) if esp_mb is not None else "   ?    "
            mode_tag = "P" if proto_mode else " "
            print("  [{}{:>1s}] {:>8s}  {:>8s}  ESP {:>6d}ms {:>14s}  PC {:6.2f} MB/s  GC {} {}".format(
                mode_tag, direction, fmt_bytes(chunk), fmt_bytes(total), esp_ms or 0,
                esp_str, pc_mb, gc_tag, verify_mark))

            results[direction].append({
                "chunk": chunk, "total": total,
                "pc_elapsed_s": elapsed, "pc_mb": pc_mb,
                "esp_ms": esp_ms, "esp_mb": esp_mb, "esp_mem": esp_mem,
                "proto": proto_mode,
            })
        else:
            sys.stderr.write("  未知控制行: {!r}\n".format(line))

    return results


# ═══════════════════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(
        description="ESP32-P4 上載極限網速測試 — PC 端 (配對 test/bench_net.py)")
    ap.add_argument("--total", type=int, default=DEFAULT_TOTAL_KB,
                    help="每筆上載總量 KB (預設 {}=4MB)".format(DEFAULT_TOTAL_KB))
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                    help="每 chunk 重複次數 (預設 {})".format(DEFAULT_RUNS))
    ap.add_argument("--chunks", default=",".join(str(c) for c in DEFAULT_CHUNK_SIZES),
                    help="要測的 chunk 大小, 逗號分隔 (預設全部)")
    ap.add_argument("--data-port", type=int, default=DEFAULT_DATA_PORT,
                    help="PC 資料 TCP server 埠 (預設 {})".format(DEFAULT_DATA_PORT))
    ap.add_argument("--disc-port", type=int, default=DEFAULT_DISC_PORT,
                    help="UDP beacon 廣播埠 (對齊 ESP config System.discovery_port, 預設 {})".format(
                        DEFAULT_DISC_PORT))
    ap.add_argument("--once", action="store_true",
                    help="只接一台 ESP 就收工 (預設持續接, Ctrl+C 結束)")
    args = ap.parse_args()

    chunk_sizes = tuple(int(x) for x in args.chunks.split(",") if x.strip())
    params = {
        "total_kb": args.total,
        "chunk_sizes": chunk_sizes,
        "runs": args.runs,
    }

    local_ip = get_local_ip()
    print("\n" + "╔" + "=" * 62 + "╗")
    print("║  ESP32-P4 → PC  上載極限吞吐 (PC server / UDP 自動連線)        ║")
    print("╚" + "=" * 62 + "╝")
    print("本機 IP      : {}".format(local_ip))
    print("資料 TCP 埠  : {}".format(args.data_port))
    print("UDP beacon   : 255.255.255.255:{} (每 {}s)".format(
        args.disc_port, BEACON_INTERVAL))
    print("測試參數     : 每筆 {} × {} runs, chunk={}".format(
        fmt_bytes(params["total_kb"] * 1024), args.runs, chunk_sizes))
    print()
    print("👉 ESP 端執行: exec(open(\"test/bench_net.py\").read())")
    print("   (需先確認 config.json 的 Network.lan.enable = 1)")
    print()

    # ── 起 TCP server ──
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", args.data_port))
    srv.listen(2)
    srv.settimeout(1.0)
    print("✓ TCP server 監聽 0.0.0.0:{}".format(args.data_port))

    # ── 起 beacon 廣播 ──
    beacon = Beacon(local_ip, args.data_port, args.disc_port, params)
    beacon.start()
    print("✓ beacon 廣播中 (等 ESP 收到後 connect 過來)\n")

    print("  {:>8s}  {:>8s}  {:>22s}   {:>15s}  {}".format(
        "chunk", "total", "ESP-side (chip 推力)", "PC-side (線速真相)", "GC Δ"))
    print("  " + "-" * 78)

    grand_best = None   # 所有 ESP/所有 chunk 的最佳 PC 側吞吐
    try:
        while True:
            # 等 ESP 連入
            deadline = time.monotonic() + LINK_WAIT_S
            conn = None
            while time.monotonic() < deadline:
                try:
                    conn, addr = srv.accept()
                    break
                except socket.timeout:
                    if args.once and grand_best is not None:
                        # --once 模式下沒新連線就收工
                        break
                    continue
            if conn is None:
                if args.once and grand_best is not None:
                    break
                print("\n❌ 等待 ESP 連入超時 ({}s)。確認 ESP 端已執行 + 乙太網同網段。".format(LINK_WAIT_S))
                break

            print("\n── ESP 連入 {} ──".format(addr[0]))
            try:
                results = handle_esp(conn, addr, params)
            except Exception as e:
                sys.stderr.write("量測例外: {}\n".format(e))
                results = {"up": [], "dl": []}
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

            # 這一台的摘要 (分上下載)
            for direction, label in (("up", "上載"), ("dl", "下載")):
                rows = results.get(direction, [])
                if rows:
                    best = max(rows, key=lambda r: r["pc_mb"])
                    print("  ─ 本台最佳{} (PC 側): chunk={} → {:.2f} MB/s ({:.1f} Mbit/s)".format(
                        label, fmt_bytes(best["chunk"]), best["pc_mb"], best["pc_mb"] * 8))
                    if grand_best is None:
                        grand_best = {"up": None, "dl": None}
                    if grand_best[direction] is None or best["pc_mb"] > grand_best[direction]["pc_mb"]:
                        grand_best[direction] = best

            if args.once:
                break
            print("\n  (持續監聽下一台 ESP; Ctrl+C 結束)")
    except KeyboardInterrupt:
        print("\n\n⏹ 使用者中斷")
    finally:
        beacon.stop()
        try:
            srv.close()
        except OSError:
            pass

    # ── 總結 (分上下載) ──
    print("\n" + "─" * 62)
    any_ok = False
    if isinstance(grand_best, dict):
        for direction, label in (("up", "上載 (ESP→PC)"), ("dl", "下載 (PC→ESP)")):
            b = grand_best.get(direction)
            if b:
                any_ok = True
                print("🏆 全程最佳{} (PC 側線速): chunk={} → {:.2f} MB/s ({:.1f} Mbit/s)".format(
                    label, fmt_bytes(b["chunk"]), b["pc_mb"], b["pc_mb"] * 8))
                if b.get("esp_mb") is not None:
                    print("   對應 ESP 側: {:.2f} MB/s ({:.1f} Mbit/s)".format(
                        b["esp_mb"], b["esp_mb"] * 8))
    if not any_ok:
        print("❌ 沒有完成任何量測")
    print("─" * 62)


if __name__ == "__main__":
    main()
