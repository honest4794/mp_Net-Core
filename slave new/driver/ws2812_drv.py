"""
ws2812_drv.py — WS2812 LED 管理

設定來源: bus.shared["WS2812"]  ({enable, list})
產物:    bus.register_service("ws2812_list", [...])
"""
import neopixel
from lib.log_service import get_log
from lib.sys_bus import bus


def init_ws2812(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("WS2812") or {}
    if not cfg.get("enable"):
        return []

    from machine import Pin
    from lib.LEDController import LEDController
    ws_list = []
    for item in cfg.get("list", []):
        pin = Pin(item["GPIO"], Pin.OUT)
        pixel = neopixel.NeoPixel(pin, item["Q"])
        ws_list.append(LEDController("WS2812", {
            "led_IO": pixel,
            "Q": item["Q"],
            "order": item.get("order", "GRB"),
        }))
    sysbus.register_service("ws2812_list", ws_list)
    get_log().info("WS2812: {} channel(s)".format(len(ws_list)))
    return ws_list


def gpios(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("WS2812") or {}
    if not cfg.get("enable"):
        return {}

    result = {}
    for i, item in enumerate(cfg.get("list", [])):
        gpio = item.get("GPIO")
        if gpio is not None:
            result[gpio] = "ws2812_{}".format(i)
    return result
