# thread_gil_split.py — 驗證「工作分流」在 GIL 下的有效邊界
#
# 目的：用數據證明兩件事（這決定你的分流架構怎麼排）：
#   (A) blocking C I/O（socket 等待）放 core1 → core0 幾乎不受影響
#       → 有效分流（C 層等待時會釋放 GIL）
#   (B) Python 密集運算放 core1 → core0 被 GIL 拖慢
#       → 無效分流（GIL 序列化，只是把卡從 core0 搬到 core1）
#
# 方法：
#   core0（主線程）跑合成「UI 幀」迴圈（dict/字串/格式化 + sleep 1ms，
#   模擬 app.step 的成本），每幀量耗時。
#   core1（_thread）依序跑 4 種負載，每種 3 秒：
#     idle     : core1 沒做事（基線）
#     socket   : accept 等待（blocking C I/O，會釋放 GIL）
#     cpu      : 純 Python 迴圈（不釋放 GIL）
#     sleep    : 只 sleep_ms（排程 overhead 基線）
#   每種負載期間量 core0 的 avg/max 幀時間。
#
# 判讀：
#   socket ≈ idle  → blocking C I/O 可以放心丟 core1（有效分流）
#   cpu >> idle    → 該工作不能丟 core1；留 core0，或用 C module
#                    在長運算時自己 mp_thread_gil_release()
#
# 用法（soft reboot 後）：
#   import thread_gil_split
#   thread_gil_split.run(phase_s=3)

import time, _thread

_PHASE_S = 3


# ── core0 合成 UI 幀（不依賴 LVGL，獨立可測） ──
def _frame(n=8):
    """模擬 app.step 一幀的成本：dict 處理 + 字串格式化。"""
    items = [{"name": "task{}".format(i), "us": i * 137} for i in range(n)]
    total = 0
    for it in items:
        s = "[{}] {:<12} {:>6}us  ({}%)".format(
            it["name"], it["name"], it["us"], (it["us"] * 100) // 1000)
        total += len(s) + it["us"]
    return total


def _core0_loop(metrics, stop):
    """core0 幀迴圈：一直跑到 stop 旗標被設。記錄每幀 us。"""
    while not stop[0]:
        t0 = time.ticks_us()
        _frame()
        dt = time.ticks_diff(time.ticks_us(), t0)
        metrics.append(dt)
        time.sleep_ms(1)


# ── core1 四種負載 ──
def _load_idle(stop):
    while not stop[0]:
        time.sleep_ms(10)


def _load_socket(stop):
    """blocking socket accept 等待（C 層等待 → 釋放 GIL）"""
    import socket
    try:
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(socket.getaddrinfo("0.0.0.0", 8198)[0][-1])
        srv.listen(1)
        srv.settimeout(0.2)
        while not stop[0]:
            try:
                srv.accept()           # blocking → GIL 釋放
            except OSError:
                pass                   # timeout = 正常
        srv.close()
    except Exception as e:
        print("[core1] socket load err: {}".format(e))


def _load_cpu(stop):
    """純 Python 密集運算（不釋放 GIL）"""
    acc = 0
    while not stop[0]:
        for i in range(2000):
            acc = (acc * 31 + i) % 104729
    stop[1] = acc


def _load_sleep(stop):
    while not stop[0]:
        time.sleep_ms(5)


LOADS = [
    ("idle",   _load_idle),
    ("socket", _load_socket),
    ("cpu",    _load_cpu),
    ("sleep",  _load_sleep),
]


def _stats(metrics):
    if not metrics:
        return (0, 0)
    return (sum(metrics) // len(metrics), max(metrics))


def run(phase_s=_PHASE_S):
    """跑 4 相測試，輸出 core0 幀時間表。"""
    _thread.stack_size(16 * 1024)          # core1 負載 thread 的 stack

    print("=" * 62)
    print("GIL 分流有效性測試（core0 合成幀 @ {}s/相）".format(phase_s))
    print("=" * 62)

    results = []
    for name, load in LOADS:
        stop = [False, 0]
        metrics = []
        th = _thread.start_new_thread(load, (stop,))
        t_end = time.ticks_ms() + phase_s * 1000
        while time.ticks_diff(time.ticks_ms(), t_end) < 0:
            t0 = time.ticks_us()
            _frame()
            dt = time.ticks_diff(time.ticks_us(), t0)
            metrics.append(dt)
            time.sleep_ms(1)
        stop[0] = True
        time.sleep_ms(50)                  # 讓 core1 收尾

        avg, mx = _stats(metrics)
        results.append((name, avg, mx, len(metrics)))
        print("  [{:<6}] core0 幀: avg={:>6}us  max={:>6}us  ({} 幀)".format(
            name, avg, mx, len(metrics)))
        time.sleep_ms(200)

    print("-" * 62)
    base = results[0][1]
    print("Summary (core0 基線 avg={}us):".format(base))
    for name, avg, mx, cnt in results:
        if name == "idle":
            continue
        ratio = avg * 100 // base if base else 0
        verdict = "有效分流(釋放 GIL)" if ratio <= 120 else "無效分流(GIL 被搶)"
        print("  {:<6} avg={:>6}us  x{:<3}  → {}".format(name, avg, ratio, verdict))
    print()
    print("判讀：")
    print("  socket 那欄如果 ≈ idle → 網路/通訊/等待類工作放心丟 core1")
    print("  cpu 那欄如果明顯變慢 → Python 運算留 core0，")
    print("    或改寫成 C module 並在長運算前 mp_thread_gil_release()")
    print("done.")
