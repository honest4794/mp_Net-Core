"""
xl9555_drv.py — XL9555 IO Expander 驅動
I2C0 (SCL=1, SDA=2), addr=0x20
"""
from lib.sys_bus import bus
from lib.log_service import get_log

DEV_ADDR = 0x20

CONFIG = [
    {"IO": 0,  "label": "tp_rst",    "mode": "OUT", "initial": 1},
    {"IO": 1,  "label": "lcd_rst",   "mode": "OUT", "initial": 1},
    {"IO": 2,  "label": "sd_cs",     "mode": "OUT", "initial": 1},
    {"IO": 3,  "label": "bl_ctr",    "mode": "OUT", "initial": 1},
    {"IO": 4,  "label": "led1",      "mode": "OUT", "initial": 0},
    {"IO": 5,  "label": "exio05",    "mode": "IN",  "initial": 0},
    {"IO": 6,  "label": "exio06",    "mode": "IN",  "initial": 0},
    {"IO": 7,  "label": "exio07",    "mode": "IN",  "initial": 0},
    {"IO": 8,  "label": "exio08",    "mode": "IN",  "initial": 0},
    {"IO": 9,  "label": "exio09",    "mode": "IN",  "initial": 0},
    {"IO": 10, "label": "exio10",    "mode": "IN",  "initial": 0},
    {"IO": 11, "label": "exio11",    "mode": "IN",  "initial": 0},
    {"IO": 12, "label": "exio12",    "mode": "IN",  "initial": 0},
    {"IO": 13, "label": "exio13",    "mode": "IN",  "initial": 0},
    {"IO": 14, "label": "exio14",    "mode": "IN",  "initial": 0},
    {"IO": 15, "label": "exio15",    "mode": "IN",  "initial": 0},
]


def config(_cfg=None):
    i2c_by_id = bus.get_service("i2c_by_id") or {}
    i2c = i2c_by_id.get(0)
    if i2c is None:
        get_log().error("xl9555: I2C0 not available")
        return None

    from lib.xl9555 import XL9555
    from lib.xl9555 import PIN_OUT
    xl = XL9555(i2c, DEV_ADDR)

    # 初始化 IO
    for item in CONFIG:
        pin = item["IO"]
        mode = item.get("mode", "IN")
        xl.pin[pin].init(PIN_OUT if mode == "OUT" else 0)
        if mode == "OUT":
            xl.pin[pin].value(item.get("initial", 0))

    bus.register_service("xl9555", xl)

    # 將 xl9555 pins 追加到 bus pin_list 統一池
    pin_list = bus.get_service("pin_list") or []
    for item in CONFIG:
        p = xl.pin[item["IO"]]
        pin_list.append(p)
    bus.register_service("pin_list", pin_list)

    # pin_by_label 也追加
    pin_by_label = bus.get_service("pin_by_label") or {}
    for item in CONFIG:
        pin_by_label[item["label"]] = xl.pin[item["IO"]]
    bus.register_service("pin_by_label", pin_by_label)

    get_log().info("xl9555: OK (addr=0x{:02X})".format(DEV_ADDR))
    return xl


def gpios():
    result = {}
    for item in CONFIG:
        io = item.get("IO")
        if io is not None:
            result[-(io + 1)] = "xl:{}".format(item.get("label", "io{}".format(io)))
    return result
