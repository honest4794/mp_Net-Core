"""
uart_drv.py — UART 管理

設定來源: bus.shared["UART"]  ({enable, list})
產物:    bus.register_service("uart_list", [UART_obj, ...])
"""
from machine import UART, Pin
from lib.sys_bus import bus
from lib.log_service import get_log


def init_uart(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("UART") or {}
    if not cfg.get("enable"):
        return []

    uart_list = []
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        uart = UART(
            item.get("id", 1),
            baudrate=item.get("baudrate", 115200),
            tx=Pin(gpio["tx"]) if gpio.get("tx") is not None else None,
            rx=Pin(gpio["rx"]) if gpio.get("rx") is not None else None,
        )
        uart_list.append(uart)

    sysbus.register_service("uart_list", uart_list)
    get_log().info("UART: {} port(s)".format(len(uart_list)))
    return uart_list


def gpios(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("UART") or {}
    if not cfg.get("enable"):
        return {}

    result = {}
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        uid = item.get("id", "?")
        for name in ("tx", "rx"):
            pin = gpio.get(name)
            if pin is not None:
                result[pin] = "uart{}_{}".format(uid, name)
    return result
