"""
i80_drv.py — 8080 並口總線管理
ESP32-S3 N16R8 V1.0 — ST7796, 16-bit I80
"""
from lib.sys_bus import bus

# DB0-DB15, WR=45, CS=39, freq=10MHz
CONFIG = {
    "data": (13, 12, 11, 10, 9, 46, 3, 8, 18, 17, 16, 15, 7, 6, 5, 4),
    "wr": 45,
    "cs": 39,
    "freq": 10000000,
}


def config():
    import lcd_bus
    data = CONFIG["data"]
    wr = CONFIG["wr"]
    cs = CONFIG["cs"]
    freq = CONFIG["freq"]

    print("[i80_drv] data pins:", data)
    print("[i80_drv] wr={} cs={} freq={}".format(wr, cs, freq))
    # 先清理殘留資源 (參考 lcd_bus SPI 模式)
    try:
        # 嘗試建立新的 I80 bus (如果先前有用, ESP-IDF 會替我們清理)
        pass  # lcd_bus.I80Bus 內部已經有 cleanup
    except:
        pass

    print("[i80_drv] data pins:", data)
    print("[i80_drv] wr={} cs={} freq={}".format(wr, cs, freq))

    # 建立 I80 Bus + Panel IO (一步到位, lcd_bus 內部處理 cleanup)
    i80 = lcd_bus.I80Bus(data=data, wr=wr, cs=cs, freq=freq)

    # 統一 lcd_bus 池
    lst = bus.get_service("lcd_bus") or []
    lst.append(i80)
    bus.register_service("lcd_bus", lst)
    bus.register_service("i80_bus", i80)
    return i80


def gpios():
    result = {}
    for i, d in enumerate(CONFIG["data"]):
        result[d] = "i80_d{}".format(i)
    result[CONFIG["wr"]] = "i80_wr"
    if CONFIG["cs"] >= 0:
        result[CONFIG["cs"]] = "i80_cs"
    return result
