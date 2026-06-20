from machine import UART, Pin
from lib.sys_bus import bus
from lib.log_service import get_log

CONFIG = [
            {
                "id": 1,
                "baudrate": 115200,
                "GPIO": { "tx": 38, "rx": 38 }
            },
            {
                "id": 2,
                "baudrate": 9600,
                "GPIO": { "tx": 40, "rx": 41 }
            }
        ]


def config():
    uart_list = []
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        uart = UART(
            item.get("id", 1),
            baudrate=item.get("baudrate", 115200),
            tx=Pin(gpio["tx"]) if gpio.get("tx") is not None else None,
            rx=Pin(gpio["rx"]) if gpio.get("rx") is not None else None,
        )
        uart_list.append(uart)

    bus.register_service("uart_list", uart_list)
    get_log().info("UART: {} port(s)".format(len(uart_list)))
    return uart_list


def gpios():
    result = {}
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        for name in ("tx", "rx"):
            pin = gpio.get(name)
            if pin is not None:
                result[pin] = "uart{}_{}".format(item.get("id", "?"), name)
    return result
