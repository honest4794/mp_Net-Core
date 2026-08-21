# lib/bus_speed.py
# 臨時提速狀態機 (協商式 + 超時回滾)
#
# 流程 (同步點 = SPEED_ACK 0x1404):
#   master 發 SPEED_SET → slave 記 old_baud/target/timeout_at → 回 SPEED_ACK(舊速)
#   → slave 送出 ACK 後立即切速 (同 handler); master 收 ACK 後立即切速
#   → master 用 STATUS_GET/IDENTIFY_REQ 敲門驗證
#   → 驗證 OK → SPEED_COMMIT 鎖定(取消回滾); 否則 timeout_at 到 → 自動回滾 old_baud
#   → 傳輸完成 → SPEED_REVERT 還原
#
# 設計要點:
#   - 唯一的「等待」是 timeout_ms (沒 COMMIT 就回滾的保險), 不是 apply delay。
#   - 「亂碼不回覆」是切速瞬間外部 bus 的自然現象, 本模組不偵測、不 auto-baud。
#   - 回滾 = 純時間檢查, 由 CircuitTask.loop 每輪呼叫 bus_speed_poll()。
#   - bus_type 沿用 hw_manager.HW 常數: UART=7 / SPI=2 / I2C=3。
#     第一階段僅實作 UART; SPI/I2C 介面預留。

import time
from lib.sys.sys_bus import bus

# 狀態
STATE_IDLE = 0
STATE_SYNCING = 1    # 已切速、待 COMMIT (回滾計時中)
STATE_COMMITTED = 2  # 已鎖定 (不回滾)

_STATE_KEY = "_bus_speed"


def _get_state():
    s = bus.shared.get(_STATE_KEY)
    if not isinstance(s, dict):
        s = {"state": STATE_IDLE}
        bus.shared[_STATE_KEY] = s
    return s


def _get_uart(bus_id):
    """依 bus_id 從 uart_list 取 UART 物件。找不到回 None。"""
    lst = bus.get_service("uart_list")
    if not lst:
        return None
    # uart_list 依 config UART.list 順序; bus_id 對應 config 的 id 欄位。
    # 這裡用 list 索引直接取 (driver 建立順序 = list 順序), 若需精確比對 id
    # 再由 caller 傳 index。為簡化, bus_id 視為 index。
    idx = int(bus_id)
    if 0 <= idx < len(lst):
        return lst[idx]
    return None


def _cur_baud(uart):
    try:
        return int(uart.baudrate) if hasattr(uart, "baudrate") else 0
    except Exception:
        return 0


def bus_speed_set(bus_type, bus_id, speed, timeout_ms):
    """SPEED_SET: 記 old/target/timeout_at, 立即切速, 進 SYNCING。
    回 (ok, cur_speed, target_speed)。SPI/I2C 尚未實作 → ok=0。"""
    if int(bus_type) != 7:  # 第一階段僅 UART
        return 0, 0, 0

    uart = _get_uart(bus_id)
    if uart is None:
        return 0, 0, 0

    old = _cur_baud(uart)
    target = int(speed)
    timeout_ms = int(timeout_ms or 0)

    try:
        uart.init(baudrate=target)  # 立即切速 (回 ACK 後同一流程)
    except Exception as e:
        print("❌ [BusSpeed] UART{} init failed: {}".format(bus_id, e))
        return 0, old, target

    s = _get_state()
    s["state"] = STATE_SYNCING
    s["bus_type"] = int(bus_type)
    s["bus_id"] = int(bus_id)
    s["old_baud"] = old
    s["target_baud"] = target
    s["timeout_at"] = time.ticks_add(time.ticks_ms(), timeout_ms) if timeout_ms > 0 else 0
    print("🔀 [BusSpeed] UART{} {} → {} (SYNCING, timeout {}ms)".format(bus_id, old, target, timeout_ms))
    return 1, old, target


def bus_speed_poll(now=None):
    """CircuitTask.loop 每輪呼叫: SYNCING 且超時未 COMMIT → 回滾 old_baud → IDLE。"""
    s = bus.shared.get(_STATE_KEY)
    if not isinstance(s, dict) or s.get("state") != STATE_SYNCING:
        return
    timeout_at = s.get("timeout_at", 0)
    if timeout_at == 0:
        return
    if now is None:
        now = time.ticks_ms()
    if time.ticks_diff(now, timeout_at) >= 0:
        _revert()


def _revert():
    """還原 old_baud (config 舊速), 進 IDLE。"""
    s = _get_state()
    uart = _get_uart(s.get("bus_id", 0))
    old = s.get("old_baud", 0)
    if uart is not None and old:
        try:
            uart.init(baudrate=old)
        except Exception as e:
            print("❌ [BusSpeed] revert failed: {}".format(e))
    print("↩️  [BusSpeed] revert UART{} → {} (IDLE)".format(s.get("bus_id"), old))
    s["state"] = STATE_IDLE


def bus_speed_commit(bus_type, bus_id):
    """SPEED_COMMIT: 鎖定新速、取消回滾。回 ok。"""
    s = _get_state()
    if s.get("state") != STATE_SYNCING:
        return 0
    if int(bus_type) != s.get("bus_type") or int(bus_id) != s.get("bus_id"):
        return 0
    s["state"] = STATE_COMMITTED
    s["timeout_at"] = 0
    print("🔒 [BusSpeed] UART{} COMMITTED @ {}".format(bus_id, s.get("target_baud")))
    return 1


def bus_speed_revert(bus_type, bus_id):
    """SPEED_REVERT: 還原 old_baud。回 ok。"""
    s = _get_state()
    if int(bus_type) != s.get("bus_type") or int(bus_id) != s.get("bus_id"):
        return 0
    _revert()
    return 1


def bus_speed_query(bus_type, bus_id):
    """SPEED_QUERY: 回 (state, bus_type, bus_id, cur_speed, target_speed, remain_ms)。"""
    s = _get_state()
    state = s.get("state", STATE_IDLE)
    uart = _get_uart(bus_id)
    cur = _cur_baud(uart) if uart is not None else 0
    target = s.get("target_baud", cur)
    remain = 0
    if state == STATE_SYNCING and s.get("timeout_at", 0):
        remain = max(0, time.ticks_diff(s.get("timeout_at"), time.ticks_ms()))
    return state, int(bus_type), int(bus_id), cur, target, remain
