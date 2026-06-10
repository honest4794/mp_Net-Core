"""
i80_drv.py — 8080 並口總線管理
ESP32-S3 N16R8 V1.0 — ST7796, 16-bit I80
"""
from machine import Pin
from lib.sys_bus import bus

# DB0-DB15, WR=45, DC=38, CS=39, freq=10MHz
# 腳位對應: 參閱 ESP32-S3 N16R8 V1.0 用戶手冊 表 1.1
CONFIG = {
    "data": (13, 12, 11, 10, 9, 46, 3, 8, 18, 17, 16, 15, 7, 6, 5, 4),
    "wr": 45,
    "dc": 38,   # 必須！ GPIO 38 = LCD_RS, ESP-IDF I2S-I80 驅動強制要求 dc >= 0
    "cs": 39,
    "freq": 10000000,
}


def config():
    import lcd_bus
    data = CONFIG["data"]
    wr = CONFIG["wr"]
    dc = CONFIG["dc"]
    cs = CONFIG["cs"]
    freq = CONFIG["freq"]

    # 建立 I80 Bus（C 層配置 dc=38 滿足 ESP-IDF 驗證）
    i80 = lcd_bus.I80Bus(data=data, wr=wr, dc=dc, cs=cs, freq=freq)

    # 統一 lcd_bus 池
    lst = bus.get_service("lcd_bus") or []
    lst.append(i80)
    bus.register_service("lcd_bus", lst)
    bus.register_service("i80_bus", i80)

    # DC/CS 由 C 層 lcd_bus.I80Bus 內部管理（建構時已傳入 dc=38, cs=39）
    # Python 層不應再建立 Pin 物件操作同一 GPIO，否則造成衝突

    print("[i80_drv] I80 bus ready (dc=GPIO{}, wr=GPIO{})".format(dc, wr))
    return i80


def gpios():
    result = {}
    for i, d in enumerate(CONFIG["data"]):
        result[d] = "i80_d{}".format(i)
    result[CONFIG["wr"]] = "i80_wr"
    result[CONFIG["dc"]] = "i80_dc"
    if CONFIG["cs"] >= 0:
        result[CONFIG["cs"]] = "i80_cs"
    return result