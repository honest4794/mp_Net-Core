"""
led_drv.py — LED 統一聚合層

將 apa1022_list + ws2812_list + pca9685_list 合併成 led_list，
並建立 LEDStreamer (st_LED)。

設定來源: 無（聚合下游 driver 結果）
產物:    bus.register_service("led_list", [...])
         bus.register_service("st_LED", LEDStreamer)
"""
from lib.sys_bus import bus
from lib.log_service import get_log
from lib.LEDController import LEDStreamer


def init_led(sysbus=None):
    sysbus = sysbus or bus
    apa_list = sysbus.get_service("apa1022_list") or []
    ws_list = sysbus.get_service("ws2812_list") or []
    pca_list = sysbus.get_service("pca9685_list") or []

    led_list = apa_list + ws_list + pca_list
    sysbus.register_service("led_list", led_list)

    try:
        st = LEDStreamer(led_list)
        st.show_all()
        sysbus.register_service("st_LED", st)
    except Exception as e:
        get_log().error("st_LED init error: {}".format(e))

    return led_list


def gpios(sysbus=None):
    # LED 本身不佔 GPIO
    return {}
