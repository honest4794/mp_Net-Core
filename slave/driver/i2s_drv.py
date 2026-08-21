"""
i2s_drv.py — I2S 音訊管理

設定來源: bus.shared["I2S"]  ({enable, list})
產物:    bus.register_service("i2s_list", [I2S_obj, ...])
"""
from machine import Pin, I2S
from lib.sys.sys_bus import bus
from lib.sys.log_service import get_log


def init_i2s(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("I2S") or {}
    if not cfg.get("enable"):
        return []

    i2s_list = []
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        icfg = item.get("config", {})
        audio_i2s = I2S(
            0,
            sck=Pin(gpio["sck"]),
            ws=Pin(gpio["ws"]),
            sd=Pin(gpio["sd"]),
            mode=I2S.RX,
            bits=icfg.get("bits", 16),
            format=I2S.STEREO,
            rate=icfg.get("rate", 16000),
            ibuf=icfg.get("rate", 16000) * 4 * 2,
        )
        i2s_list.append(audio_i2s)

    sysbus.register_service("i2s_list", i2s_list)
    get_log().info("I2S: {} device(s)".format(len(i2s_list)))
    return i2s_list


def gpios(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("I2S") or {}
    if not cfg.get("enable"):
        return {}

    result = {}
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        for name in ("sck", "ws", "sd"):
            pin = gpio.get(name)
            if pin is not None:
                result[pin] = "i2s_{}".format(name)
    return result
