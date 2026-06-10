"""
TFT 顯示驅動配置層 — 支援 SPI / QSPI / I80 / RGB / I2C

兩種呼叫方式:
  config(spi=..., dc=..., cs=..., rst=..., driver="...", ...)   ← 工廠式，明確傳參
  boot_config(cfg)                                                ← boot 模式，接受 dict
"""

def config(spi, dc, cs, rst, driver="ST7789", width=240, height=320,
           rotation=0, color_order="RGB", invert=False,
           pixel_format="RGB565_BE", bytes_per_pixel=2, adapter=None):
    """工廠函式 — 明確傳入 SPI / pin 物件"""
    from lib.TFT import ST7789, ST7789T_Vernon, ST7735, ST7796, GC9A01, GC9D01, ILI9341, NV3030B

    driver_map = {
        "ST7789":        ST7789,
        "ST7789T_Vernon": ST7789T_Vernon,
        "ST7735":        ST7735,
        "GC9A01":        GC9A01,
        "GC9D01":        GC9D01,
        "ILI9341":       ILI9341,
        "NV3030B":       NV3030B,
        "ST7796":        ST7796,
    }

    for lazy_drv in ("RM67162", "SH8601"):
        if driver == lazy_drv:
            try:
                mod = __import__("lib.TFT", None, None, [lazy_drv])
                driver_map[lazy_drv] = getattr(mod, lazy_drv)
            except (ImportError, AttributeError):
                raise ValueError("{} not available — update lib/TFT.py on device".format(lazy_drv))

    driver_cls = driver_map.get(driver)
    if driver_cls is None:
        raise ValueError("Unsupported TFT driver: {}".format(driver))

    lcd = driver_cls(
        spi=spi,
        dc=dc,
        cs=cs,
        rst=rst,
        width=width,
        height=height,
        rotation=rotation,
        color_order=color_order,
        invert=invert,
        pixel_format=pixel_format,
        bytes_per_pixel=bytes_per_pixel,
        adapter=adapter,
    )

    return lcd


def boot_config(cfg):
    """boot 模式 — 自動偵測 bus 類型，分派到對應處理"""
    cfg = dict(cfg)
    from lib.sys_bus import bus

    # 已初始化過（同一 session 被重複執行）直接復用
    lcd = bus.get_service("lcd")
    if lcd is not None:
        bus.shared["tft_width"] = lcd.width
        bus.shared["tft_height"] = lcd.height
        print("[tft_drv] LCD already initialized, reuse")
        return lcd

    # 自動偵測：有 i80_bus 就走 I80，否則走 SPI
    i80 = bus.get_service("i80_bus")
    if i80 is not None:
        return boot_config_i80(cfg)
    return boot_config_spi(cfg)


def boot_config_spi(cfg):
    """boot 模式 — SPI / QSPI"""
    cfg = dict(cfg)
    from lib.sys_bus import bus
    from lib.bus_adapter import SpiBusAdapter

    spi_by_id = bus.get_service("spi_by_id") or {}
    pin_by_label = bus.get_service("pin_by_label") or {}

    pins = cfg.pop("pins", {})
    dc  = pin_by_label.get(pins.get("dc", ""))
    cs  = pin_by_label.get(pins.get("cs", ""))
    rst = pin_by_label.get(pins.get("rst", ""))

    missing = []
    if dc  is None: missing.append("dc={}".format(pins.get("dc")))
    if cs  is None: missing.append("cs={}".format(pins.get("cs")))
    if rst is None: missing.append("rst={}".format(pins.get("rst")))
    if missing:
        raise ValueError("TFT pins not found: {}".format(", ".join(missing)))

    bl = pin_by_label.get(pins.get("bl", ""))
    if bl is not None:
        bl.value(1)
        print("[tft_drv] power ON (GPIO={})".format(pins.get("bl", "")))

    spi_id = cfg.pop("spi_id", 1)
    spi = spi_by_id.get(spi_id) or (list(spi_by_id.values())[0] if spi_by_id else None)
    if spi is None:
        print("[tft_drv] no SPI bus available, skipping")
        return None

    fmt = cfg.get("pixel_format", "RGB565_BE")
    bpp = 3 if fmt.startswith("RGB888") else 2

    adapter = SpiBusAdapter(spi, dc, cs, rst)
    lcd = config(spi=spi, dc=dc, cs=cs, rst=rst,
                 bytes_per_pixel=bpp, adapter=adapter, **cfg)

    bus.register_service("lcd", lcd)
    bus.shared["tft_width"] = cfg["width"]
    bus.shared["tft_height"] = cfg["height"]
    bus.shared["tft_driver"] = cfg["driver"]

    black = bytearray(cfg["width"] * cfg["height"] * bpp)
    lcd.show(black)

    return lcd


def boot_config_i80(cfg):
    """boot 模式 — I80 並口"""
    cfg = dict(cfg)
    from lib.sys_bus import bus
    from lib.bus_adapter import I80BusAdapter

    i80 = bus.get_service("i80_bus")
    if i80 is None:
        print("[tft_drv] no I80 bus available, skipping")
        return None

    pin_by_label = bus.get_service("pin_by_label") or {}
    pins = cfg.pop("pins", {})

    dc = pin_by_label.get(pins.get("dc", ""))
    cs = pin_by_label.get(pins.get("cs", ""))

    # ── XL9555: LCD 復位 + 背光 ──
    xl_cfg = cfg.pop("xl9555", {})
    xl = bus.get_service("xl9555")
    if xl and xl_cfg:
        rst_pin = xl_cfg.get("rst")
        bl_pin = xl_cfg.get("bl")
        import time
        if rst_pin is not None:
            xl.pin[rst_pin].init(1); xl.pin[rst_pin].value(0)
            time.sleep_ms(10)
            xl.pin[rst_pin].value(1)
            time.sleep_ms(10)
        if bl_pin is not None:
            xl.pin[bl_pin].init(1); xl.pin[bl_pin].value(1)
        print("[tft_drv] XL9555: rst={} bl={}".format(rst_pin, bl_pin))
    else:
        print("[tft_drv] XL9555 not available")

    adapter = I80BusAdapter(i80, dc=dc, cs=cs)
    bpp = 3 if cfg.get("pixel_format", "").startswith("RGB888") else 2

    lcd = config(spi=None, dc=None, cs=None, rst=None,
                 bytes_per_pixel=bpp, adapter=adapter, **cfg)

    bus.register_service("lcd", lcd)
    bus.shared["tft_width"] = cfg["width"]
    bus.shared["tft_height"] = cfg["height"]
    bus.shared["tft_driver"] = cfg["driver"]

    black = bytearray(cfg["width"] * cfg["height"] * bpp)
    lcd.show(black)

    return lcd


def gpios():
    """TFT 不直接擁有 GPIO"""
    return {}