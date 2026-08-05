"""
pca9685_drv.py — PCA9685 PWM LED 管理 (走 I2C)

設定來源: bus.shared["PCA9685"]  ({enable, list})
         list item: {"i2c": <i2c_list index>, "address": ["0x40"]}
產物:    bus.register_service("pca9685_list", [...])
"""
from lib.log_service import get_log
from lib.pca9685 import PCA9685
from lib.sys_bus import bus


def init_pca9685(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("PCA9685") or {}
    if not cfg.get("enable"):
        return []

    from lib.LEDController import LEDController
    i2c_list = sysbus.get_service("i2c_list") or []
    pca_list = []
    for item in cfg.get("list", []):
        i2c_idx = item.get("GPIO", {}).get("i2c", 0)
        if i2c_idx < 0 or i2c_idx >= len(i2c_list):
            get_log().error("PCA9685: i2c index {} not found".format(i2c_idx))
            continue
        i2c = i2c_list[i2c_idx]
        addrs = item.get("address", [])
        if not addrs:
            try:
                addrs = [a for a in i2c.scan() if a != 112]
                get_log().info("I2C Scan: {}".format([hex(a) for a in addrs]))
            except Exception as e:
                get_log().error("PCA9685 scan error: {}".format(e))
                continue
        for addr in addrs:
            if isinstance(addr, str):
                addr = int(addr, 16)
            try:
                pca = PCA9685(i2c, address=addr)
                pca.freq(1000)
                pca_list.append(LEDController("i2c_LED", {
                    "led_IO": pca,
                    "Q": 16,
                    "order": "W",
                }))
            except Exception as e:
                get_log().error("PCA9685@{} error: {}".format(hex(addr), e))
    sysbus.register_service("pca9685_list", pca_list)
    get_log().info("PCA9685: {} device(s)".format(len(pca_list)))
    return pca_list


def gpios(sysbus=None):
    # PCA9685 走 I2C，無獨立 GPIO
    return {}
