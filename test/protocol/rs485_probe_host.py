# -*- coding: utf-8 -*-
"""rs485_probe_host.py — RS485 漸進式測試 PC 端（USB-RS485 轉接器當對端）

與板端 rs485_probe.py 配對使用。每階段獨立、有明確 PASS/FAIL，
每步都先人工確認再進下一步：

  Stage2  PC 當發送端 ping、板當 reflector（板上跑 run(2)）：
      python -B rs485_probe_host.py peer --port COM7 --baud 9600 --stage 2 --role ping

  Stage2  板當發送端、PC 當 reflector（板上跑 run(2, mode='ping')）：
      python -B rs485_probe_host.py peer --port COM7 --baud 9600 --stage 2 --role reflect --listen 60

  Stage3  PC 模擬顯示器：收真實 5-byte 幀、列印解析、原樣 echo 當 ack（板上跑 run(3)）：
      python -B rs485_probe_host.py peer --port COM7 --baud 9600 --stage 3 --listen 60

  部署 agent 到板（需要 mpremote；--tx/--rx 等參數不給 = 用板上 config.json/腳本常數）：
      python -B rs485_probe_host.py deploy --board COM3 --stage 1
      python -B rs485_probe_host.py deploy --board COM3 --stage 3 --tx 9 --rx 8 --en 7

port 可以是 Windows 的 COM7 或 macOS 的 /dev/cu.usbmodemXXX。
"""

import argparse
import subprocess
import sys
import time

try:
    import serial
except ImportError:
    serial = None

# ── 幀格式（與板端 rs485_probe.py 一致） ──
P_HEAD, P_TAIL, P_LEN = 0xAC, 0xFF, 10   # Stage2 probe 幀
D_SOF, D_EOF, D_LEN = 0xB4, 0xFF, 5      # Stage3 真實顯示幀


def build_probe(seq):
    f = bytearray(P_LEN)
    f[0] = P_HEAD
    f[1] = seq & 0xFF
    f[2] = (seq >> 8) & 0xFF
    f[3] = (seq >> 16) & 0xFF
    f[4] = (seq >> 24) & 0xFF
    f[5] = 0x11
    f[6] = 0x22
    f[7] = 0x33
    f[8] = 0x44
    f[9] = P_TAIL
    return bytes(f)


def seq_of(f):
    return f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)


def echo_probe(f):
    return build_probe((seq_of(f) + 1) & 0xFFFFFFFF)


def build_disp(mode, bri, t):
    return bytes([D_SOF, mode & 0xFF, bri & 0x1F, t & 0xFF, D_EOF])


def hexs(data):
    return " ".join("{:02X}".format(b) for b in data)


def scan(buf):
    """掃描緩衝開頭。一律回 (frame, 剩餘)：
    - frame 非 None       → 拿到一幀（probe 或 顯示幀）
    - (None, 較短 buf)    → 本次無幀但已丟掉垃圾/假頭（有進展）
    - (None, 同長度 buf)  → 無進展（等新資料）"""
    n = len(buf)
    if n < D_LEN:
        return None, buf
    if buf[0] == P_HEAD and n >= P_LEN and buf[P_LEN - 1] == P_TAIL:
        return bytes(buf[:P_LEN]), buf[P_LEN:]
    if buf[0] == D_SOF and buf[D_LEN - 1] == D_EOF:
        return bytes(buf[:D_LEN]), buf[D_LEN:]
    ia = buf.find(b"\xAC", 1)
    ib = buf.find(b"\xB4", 1)
    idxs = [i for i in (ia, ib) if i >= 0]
    if not idxs:
        keep = max(P_LEN, D_LEN) - 1
        if n > keep:
            return None, buf[-keep:]
        return None, buf
    return None, buf[min(idxs):]


def _drain(s, ms=300):
    """讀掉既有殘留資料。"""
    t0 = time.monotonic()
    while time.monotonic() - t0 < ms / 1000.0:
        try:
            if s.in_waiting:
                s.read(s.in_waiting)
        except Exception:
            return
        time.sleep(0.005)


def _read_frame(s, buf, deadline):
    """持續讀到一幀（probe 或 disp）回 (frame, buf)；逾時回 (None, buf)。"""
    while time.monotonic() < deadline:
        try:
            if s.in_waiting:
                chunk = s.read(s.in_waiting)
                if chunk:
                    buf.extend(chunk)
        except Exception:
            return None, buf
        out = scan(buf)
        if out is not None:
            return out[0], out[1]
        time.sleep(0.001)
    return None, buf


# ═══════════════════ peer 子命令 ═══════════════════
def cmd_peer(args):
    if serial is None:
        print("[FAIL] 需要 pyserial：pip install pyserial")
        return 1
    try:
        s = serial.Serial(args.port, args.baud, timeout=0.05)
    except Exception as e:
        print("[FAIL] 打不開 {}: {}".format(args.port, repr(e)))
        print("  檢查：port 名、驅動、是否被其他程式佔用（Thonny/Arduino 要先關）")
        return 1

    print("=" * 60)
    print("PC 對端開啟：{} @ {} baud（RS485 轉接器 A-A/B-B，GND 共地）".format(
        args.port, args.baud))
    print("=" * 60)
    _drain(s, 300)

    if args.stage == 2:
        rc = _peer_stage2(s, args)
    else:
        rc = _peer_stage3(s, args)

    try:
        s.close()
    except Exception:
        pass
    return rc


def _peer_stage2(s, args):
    if args.role == "ping":
        print("STAGE 2 — PC PING：送 {} 幀、等板回 seq+1（板上請跑 run(2)）".format(args.count))
        ok = 0
        rtts = []
        buf = bytearray()
        for i in range(args.count):
            f = build_probe(i)
            t0 = time.monotonic()
            try:
                s.write(f)
            except Exception as e:
                print("[{:>2}] 寫入失敗: {}".format(i, repr(e)))
                break
            back, buf = _read_frame(s, buf, t0 + 0.8)
            dt = (time.monotonic() - t0) * 1000.0
            if back is not None and back[0] == P_HEAD and seq_of(back) == (i + 1) & 0xFFFFFFFF:
                ok += 1
                rtts.append(dt)
                print("[{:>2}] OK   rtt={:.0f}ms".format(i, dt))
            else:
                raw = hexs(back) if back is not None else "(無回應)"
                print("[{:>2}] LOST  got={}".format(i, raw))
            time.sleep(max(0.0, args.interval - dt / 1000.0))

        print("-" * 60)
        if rtts:
            print("RTT min/avg/max = {:.0f}/{:.0f}/{:.0f} ms".format(
                min(rtts), sum(rtts) / len(rtts), max(rtts)))
        if ok == args.count:
            print("RESULT stage=2 role=ping PASS ({}/{})".format(ok, args.count))
            return 0
        print("RESULT stage=2 role=ping FAIL ({}/{})".format(ok, args.count))
        print("  0 回應 → 板上是否跑 run(2)？接線 A-A/B-B/GND？baud 一致？")
        print("  部分回應 → 檢查總線品質/終端/偏壓，或板端 settle_ms")
        return 1

    # reflect：PC 反射板的 ping（板上請跑 run(2, mode='ping')）
    print("STAGE 2 — PC REFLECT：反射板送來的 probe 幀（板上請跑 run(2, mode='ping')）")
    print("監聽 {} 秒...".format(args.listen))
    buf = bytearray()
    got = 0
    t_end = time.monotonic() + args.listen
    while time.monotonic() < t_end:
        f, buf = _read_frame(s, buf, time.monotonic() + 0.2)
        if f is not None and f[0] == P_HEAD and f[P_LEN - 1] == P_TAIL:
            try:
                s.write(echo_probe(f))
            except Exception:
                pass
            got += 1
            print("RECV seq={} → echo seq={} (total={})".format(
                seq_of(f), (seq_of(f) + 1) & 0xFFFFFFFF, got))
    print("RESULT stage=2 role=reflect frames={} (板端統計才是成敗依據)".format(got))
    return 0


def _peer_stage3(s, args):
    print("STAGE 3 — PC 模擬顯示器：收真實 5-byte 幀、列印、原樣 echo 當 ack（板上請跑 run(3)）")
    print("監聽 {} 秒...".format(args.listen))
    buf = bytearray()
    got = 0
    stray = bytearray()
    t_end = time.monotonic() + args.listen
    while time.monotonic() < t_end:
        f, buf = _read_frame(s, buf, time.monotonic() + 0.2)
        if f is not None and f[0] == D_SOF and f[D_LEN - 1] == D_EOF:
            print("RECV {} → mode={} bri={} time={} (total={})".format(
                hexs(f), f[1], f[2], f[3], got + 1))
            time.sleep(0.03)                    # 模擬顯示器處理時間
            try:
                s.write(f)                      # 原樣 echo = ack
            except Exception:
                pass
            got += 1
            print("      → ack 已回傳 {}".format(hexs(f)))
        elif f is not None:
            print("RECV 其他幀 {}".format(hexs(f)))
    if got == 0:
        print("RESULT stage=3 peer frames=0（無任何 5-byte 幀）")
        print("  檢查：板上跑 run(3) 了嗎？本 port 接的是 RS485 轉接器嗎？")
        return 1
    print("RESULT stage=3 peer frames={}（板端 run(3) 的 PASS/FAIL 才是結論）".format(got))
    return 0


# ═══════════════════ deploy 子命令（mpremote） ═══════════════════
def _mpremote_cmd():
    return [sys.executable, "-B", "-m", "mpremote"]


def cmd_deploy(args):
    import os
    agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rs485_probe.py")
    if not os.path.exists(agent_path):
        print("[FAIL] 找不到 {}".format(agent_path))
        return 1

    call_args = ["stage={}".format(args.stage)]
    for key in ("tx", "rx", "en", "baud", "en_active", "settle_ms"):
        v = getattr(args, key)
        if v is not None:
            call_args.append("{}={}".format(key, v))
    if args.mode and args.stage == 2:
        call_args.append("mode={!r}".format(args.mode))
    call_code = "exec(open('rs485_probe.py').read())\nrun({})\n".format(", ".join(call_args))

    steps = [
        ("上傳 agent", ["connect", args.board, "cp", agent_path, ":rs485_probe.py"]),
        ("執行 run({})".format(args.stage), ["connect", args.board, "exec", call_code]),
    ]
    for label, tail in steps:
        cmd = _mpremote_cmd() + tail
        print("$ {} {}".format(" ".join(cmd[:3]), " ".join(cmd[3:])))
        try:
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except FileNotFoundError:
            print("[FAIL] 沒有 mpremote（pip install mpremote），或改用手動方式：")
            print("  1) 把 rs485_probe.py 傳到板上根目錄（Thonny / mpremote cp）")
            print("  2) REPL 執行：")
            print(call_code)
            return 1
        except Exception as e:
            print("[FAIL] {}: {}".format(label, repr(e)))
            return 1
        out = (cp.stdout or "").strip()
        err = (cp.stderr or "").strip()
        if out:
            print(out)
        if err:
            print("[stderr] {}".format(err))
        if cp.returncode != 0:
            print("[FAIL] {} 失敗（rc={}）→ 可改用手動方式：".format(label, cp.returncode))
            print("  1) 把 rs485_probe.py 傳到板上根目錄")
            print("  2) REPL 執行：")
            print(call_code)
            return 1
    print("[OK] 已部署並啟動 Stage{}，請看板端輸出逐項確認".format(args.stage))
    return 0


# ═══════════════════ 入口 ═══════════════════
def main(argv=None):
    ap = argparse.ArgumentParser(description="RS485 漸進式測試 — PC 端對端/部署")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("peer", help="USB-RS485 轉接器當對端")
    p.add_argument("--port", required=True, help="RS485 轉接器序列埠（COM7 或 /dev/cu.usbmodemXXX）")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--stage", type=int, choices=(2, 3), required=True)
    p.add_argument("--role", choices=("ping", "reflect"), default="ping",
                   help="stage2 才用：ping=PC 發送端；reflect=PC 當反射端")
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--interval", type=float, default=0.3, help="ping 間隔（秒）")
    p.add_argument("--listen", type=int, default=60, help="reflect/監聽秒數")
    p.set_defaults(fn=cmd_peer)

    d = sub.add_parser("deploy", help="用 mpremote 部署並啟動板端 stage")
    d.add_argument("--board", required=True, help="板端 REPL 序列埠（COM3 或 /dev/cu.usbmodemXXX）")
    d.add_argument("--stage", type=int, choices=(1, 2, 3, 9), required=True)
    d.add_argument("--tx", type=int, default=None, help="不給 = 用板上 config.json(Stage3)/腳本常數(其餘)")
    d.add_argument("--rx", type=int, default=None)
    d.add_argument("--en", type=int, default=None)
    d.add_argument("--baud", type=int, default=None)
    d.add_argument("--en_active", type=int, default=None)
    d.add_argument("--settle_ms", type=int, default=None)
    d.add_argument("--mode", choices=("reflect", "ping"), default=None, help="stage2 才用")
    d.set_defaults(fn=cmd_deploy)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
