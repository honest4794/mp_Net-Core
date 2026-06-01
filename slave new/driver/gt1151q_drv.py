"""
gt1151q_drv.py — GT1151Q 觸控驅動
ESP32-S3 N16R8 V1.0
I2C1 (SCL=40, SDA=41), INT=42
"""
from lib.sys_bus import bus
from lib.log_service import get_log

I2C_BUS = 1
I2C_ADDR = 0x5D  # 嘗試 0x5D, 若失敗自動掃描


def config(_cfg=None):
    i2c_by_id = bus.get_service("i2c_by_id") or {}
    i2c = i2c_by_id.get(I2C_BUS)
    if i2c is None:
        get_log().error("gt1151q: I2C{} not available".format(I2C_BUS))
        return None

    # 從 pin_by_label 拿到 INT pin
    pin_by_label = bus.get_service("pin_by_label") or {}
    int_pin = pin_by_label.get("touch_int")  # GPIO 42

    from lib.gt1151q import GT1151Q

    # 自動掃描位址
    addr = I2C_ADDR
    found = i2c.scan()
    if addr not in found:
        get_log().info("gt1151q: addr 0x{:02X} not in scan {}, trying auto".format(addr, [hex(a) for a in found]))
        # 嘗試常見的觸控位址
        for try_addr in (0x5D, 0x14, 0x38, 0x5D >> 1):
            if try_addr in found:
                addr = try_addr
                break
        else:
            get_log().error("gt1151q: touch IC not found on I2C{}".format(I2C_BUS))
            return None

    tp = GT1151Q(i2c, addr, int_pin)
    if not tp.init():
        return None

    bus.register_service("touch", tp)
    bus.shared["touch_vendor"] = "GT1151Q"
    get_log().info("gt1151q: OK (addr=0x{:02X}, int=GPIO{})".format(addr, int_pin is not None))
    return tp


def gpios():
    # GT1151Q 不佔主控 GPIO (INT 在 pin_drv 已註冊)
    return {}


def read_touch():
    """便利函數: 從 bus 取得 touch 並讀取"""
    tp = bus.get_service("touch")
    if tp is None or not tp.available():
        return []
    return tp.read_points()
