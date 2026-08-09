"""
apa102_drv.py — APA102 LED 管理 (走 SPI)

設定來源: bus.shared["APA102"]  ({enable, list})
         list item: {"spi": <spi_list index>, "Q": N, "order": "BGRW"}
產物:    bus.register_service("apa1022_list", [...])
"""
from lib.log_service import get_log
from lib.apa102 import APA102
from lib.sys_bus import bus


def init_apa102(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("APA102") or {}
    if not cfg.get("enable"):
        return []

    from lib.LEDController import LEDController
    spi_list = sysbus.get_service("spi_list") or []
    apa_list = []
    for item in cfg.get("list", []):
        spi_idx = item.get("GPIO", {}).get("spi", 0)
        if spi_idx < 0 or spi_idx >= len(spi_list):
            get_log().error("APA102: spi index {} not found".format(spi_idx))
            continue
        apa = APA102(spi_list[spi_idx], num_leds=item["Q"])
        apa_list.append(LEDController("APA102", {
            "led_IO": apa,
            "Q": item["Q"],
            "order": item.get("order", "BGRW"),
        }))
    sysbus.register_service("apa1022_list", apa_list)
    get_log().info("APA102: {} channel(s)".format(len(apa_list)))
    return apa_list


def gpios(sysbus=None):
    # APA102 走 SPI，無獨立 GPIO
    return {}
