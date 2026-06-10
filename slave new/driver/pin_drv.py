"""
pin_drv.py — GPIO 腳位管理
ESP32-S3 N16R8 V1.0

已由其他 driver 佔用的腳位:
  i80_drv:  4,5,6,7,8,9,10,11,12,13,15,16,17,18,46,3 (DB0-DB15)
  i80_drv:  45(WR), 39(CS)
  i2c_drv:  1,2 (XL9555), 40,41 (GT1151Q)
  spi_drv:  47,21,48 (TF Card)

正式使用:
  tft_rs=38 (RS/DC)
  touch_int=42
  boot_btn=0

餘下自由 GPIO:
"""
from lib.hw_manager import init_pins

CONFIG = [
    # ── TFT RS/DC ──
#     {"GPIO": 38, "label": "tft_rs",     "mode": "OUT", "initial": 0},

    # ── Touch INT ──
    {"GPIO": 42, "label": "touch_int",  "mode": "IN",  "initial": 0, "pull": "UP"},

    # ── BOOT 按鍵 ──
    {"GPIO": 0,  "label": "boot_btn",   "mode": "IN",  "initial": 0, "pull": "UP"},

    # ── 自由 GPIO ──
    {"GPIO": 14, "label": "gp14",       "mode": "IN",  "initial": 0, "pull": "UP"},
    {"GPIO": 43, "label": "gp43",       "mode": "IN",  "initial": 0, "pull": "UP"},
    {"GPIO": 44, "label": "gp44",       "mode": "IN",  "initial": 0, "pull": "UP"},
]


def config():
    return init_pins(CONFIG)


def gpios():
    result = {}
    for item in CONFIG:
        gpio = item.get("GPIO")
        if gpio is not None:
            result[gpio] = item.get("label", "pin_{}".format(gpio))
    return result
