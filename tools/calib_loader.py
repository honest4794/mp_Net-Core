"""calib_loader.py — 讀回校準 JSON 檔，依 address 填入 UartMotor 校準表

檔格式（每檔一個速度點，由 calibrate_motor.save() 產生，含 address）:
    {"address": 11, "speed": 24, "forward_ms": 15300, "reverse_ms": 16200}
      forward_ms / reverse_ms 為 null → 該方向死區（不建立該速度點）

用法:
    from lib.uart_motor import UartMotor
    from tools.calib_loader import load_calibration

    motor = UartMotor({...})
    load_calibration(motor, "/calib")            # 目錄：讀全部 *.json
    # 或
    load_calibration(motor, ["/calib/speed_024.json", ...])
"""

import os

try:
    import ujson as json
except ImportError:
    import json

from lib.uart_motor import SPEED_MAX


def _iter_files(src):
    if isinstance(src, (list, tuple)):
        return list(src)
    try:
        names = sorted(os.listdir(src))
    except OSError:
        return [src]                      # 單一檔案路徑
    return [src.rstrip("/") + "/" + n for n in names if n.endswith(".json")]


def load_calibration(motor, src):
    """讀校準 JSON（每檔一速度點）填入 motor 各台校準表。

    依檔內 address 分台；全速點（speed=128）同步該台 t_full。
    回傳載入的 (address, speed) 清單（排序、去重）。
    """
    loaded = []

    for path in _iter_files(src):
        with open(path, "r") as f:
            d = json.load(f)
        if "address" not in d:
            raise ValueError("calib: 缺少 address 欄位: {}".format(path))
        addr = int(d["address"])
        if addr not in motor.addresses:
            raise ValueError(
                "calib: address {} 不在 motor 控制列表 {}（{}）".format(
                    addr, motor.addresses, path))
        speed = int(d["speed"])
        if not 1 <= speed <= SPEED_MAX:
            raise ValueError("calib: speed 必須 1..{}: {}".format(SPEED_MAX, speed))
        fwd = d.get("forward_ms")
        rev = d.get("reverse_ms")
        if fwd is not None:
            motor.calibrate(addr, 1, speed, int(fwd))
        if rev is not None:
            motor.calibrate(addr, -1, speed, int(rev))
        loaded.append((addr, speed))

        # 全速點同步 t_full，保持線性 fallback 一致
        if speed == SPEED_MAX:
            if fwd is not None:
                motor.set_t_full(addr, 1, int(fwd))
            if rev is not None:
                motor.set_t_full(addr, -1, int(rev))

    return sorted(set(loaded))
