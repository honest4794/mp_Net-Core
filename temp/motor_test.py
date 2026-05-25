"""
DC 馬達驅動測試 — HIP4081A + PinSnapTask 自動還原

接線 (ESP32 -> 驅動板):
  GPIO  8 -> IN1 (ALI)
  GPIO  9 -> IN2 (BLI)
  GPIO 10 -> EN  (DIS, 板端反相)

控制邏輯:
  正向: IN1=L, IN2=H, EN=PWM
  反向: IN1=H, IN2=L, EN=PWM
  煞車: IN1=H, IN2=H
  停止: IN1=L, IN2=L, EN=L

整合 PinSnapTask:
  啟動時自動記錄 GPIO 8/9/10 初始狀態
  每次 loop 檢查是否有變更並記錄
  超時後自動還原所有 pin 到初始狀態
"""

from machine import Pin, PWM
from time import sleep, ticks_ms, ticks_diff

# -- 參數 --
PWM_FREQ = 1000
DUTY     = 512

# -- GPIO --
in1 = Pin(21,  Pin.OUT, value=0)
in2 = Pin(14,  Pin.OUT, value=0)
en  = PWM(Pin(13), freq=PWM_FREQ, duty=0)

# -- 函數 --
def stop():
    in1.value(0); in2.value(0); en.duty(0)

def forward(duty=DUTY):
    in1.value(0); in2.value(1); en.duty(duty)

def reverse(duty=DUTY):
    in1.value(1); in2.value(0); en.duty(duty)

def brake():
    in1.value(1); in2.value(1); en.duty(DUTY)


# -- 簡易 Snapshot + 自動還原 (獨立版，不依賴 TaskManager) --
class PinSnapshot:
    """內建 snapshot / auto-restore，可不靠 TaskManager 獨立運作"""
    def __init__(self):
        self._pins = []          # list of (id, obj, is_pwm, initial)
        self._change_log = []    # list of (ticks_ms, id, from, to)
        self._start_ticks = 0
        self._timeout_ms = 0
        self._restored = False

    def register(self, pid, obj, is_pwm=False):
        self._pins.append((pid, obj, is_pwm, None))

    def set_timeout(self, ms):
        self._timeout_ms = ms

    def take_snapshot(self):
        for i, (pid, obj, is_pwm, _) in enumerate(self._pins):
            if is_pwm:
                initial = obj.duty()
            else:
                initial = obj.value()
            self._pins[i] = (pid, obj, is_pwm, initial)
        self._start_ticks = ticks_ms()
        self._restored = False

    def poll(self):
        """在 loop 中呼叫，檢查變化 + 超時還原"""
        if self._restored:
            return
        now = ticks_ms()

        for pid, obj, is_pwm, initial in self._pins:
            if initial is None:
                continue
            current = obj.duty() if is_pwm else obj.value()
            if current != initial:
                # 去重：同 pin 同值不重複記錄
                last = None
                for log in reversed(self._change_log):
                    if log[1] == pid:
                        last = log
                        break
                if last is None or last[3] != current:
                    self._change_log.append((now, pid, initial, current))
                    print("[SNAP] pin {}: {} -> {}".format(pid, initial, current))

        if self._timeout_ms > 0:
            if ticks_diff(now, self._start_ticks) >= self._timeout_ms:
                self._restore()

    def _restore(self):
        print("[SNAP] timeout, restoring all pins...")
        for pid, obj, is_pwm, initial in self._pins:
            if initial is None:
                continue
            if is_pwm:
                obj.duty(initial)
            else:
                obj.value(initial)
            print("  {} -> {}".format(pid, initial))
        self._change_log.clear()
        self._restored = True

    def get_log(self):
        return self._change_log


# ─── 主程式 ──────────────────────────────────────
print("=== HIP4081A Motor Test (with PinSnap auto-restore) ===")
print()

snap = PinSnapshot()
snap.register("in1", in1, is_pwm=False)
snap.register("in2", in2, is_pwm=False)
snap.register("en",  en,  is_pwm=True)

# 記錄初始狀態 (全部 LOW)
snap.take_snapshot()
print("[SNAP] initial state recorded")
print("  in1={}, in2={}, en.duty={}".format(in1.value(), in2.value(), en.duty()))

# 設定 20 秒後自動還原
snap.set_timeout(20000)

# -- 測試動作 --
print()
print("正向 5s -> 反向 5s -> 煞車 2s -> 停止 (等自動還原)")
print()

forward()
print("> 正向")
sleep(5)
snap.poll()  # 會記錄變化

reverse()
print("< 反向")
sleep(5)
snap.poll()  # 會記錄變化

brake()
print("| 煞車")
sleep(2)
snap.poll()

stop()
print("| 停止 (等待超時自動還原...)")
print()

# 持續 poll 直到超時還原或手動中斷
while not snap._restored:
    snap.poll()
    sleep(0.5)

print()
print("=== Log ===")
for entry in snap.get_log():
    print("  {}ms: {} {}->{}".format(ticks_diff(entry[0], snap._start_ticks), entry[1], entry[2], entry[3]))
print("=== 測試結束 ===")
