"""
TFT 顯示驅動配置層 — 支援 SPI / QSPI / I80 / RGB / I2C

兩種呼叫方式:
  config(spi=..., dc=..., cs=..., rst=..., driver="...", ...)   ← 工廠式，明確傳參
  boot_config(cfg)                                                ← boot 模式，接受 dict
"""

def config(spi, dc, cs, rst, driver="ST7789", width=240, height=320,
           rotation=0, color_order="RGB", invert=False,
           pixel_format="RGB565_BE", bytes_per_pixel=2, adapter=None,
           variant=None):
    """工廠函式 — 明確傳入 SPI / pin 物件"""
    from lib.TFT import ST7789, ST7735, ST7796, GC9A01, GC9D01, ILI9341, NV3030B

    driver_map = {
        "ST7789":        ST7789,
        "ST7735":        ST7735,
        "GC9A01":        GC9A01,
        "GC9D01":        GC9D01,
        "ILI9341":       ILI9341,
        "NV3030B":       NV3030B,
        "ST7796":        ST7796,
        "ST7796_I80":    ST7796,   # I80 介面用 ST7796 driver
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

    kwargs = {}
    if variant is not None:
        kwargs["variant"] = variant

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
        **kwargs,
    )

    return lcd


def boot_config(cfg):
    """boot 模式 — 接受 cfg dict，從 bus service 解析 SPI / pin"""
    cfg = dict(cfg)  # 複製，避免 pop 影響 boot.py 原始 dict
    from lib.sys_bus import bus
    from lib.bus_adapter import SpiBusAdapter

    spi_by_id = bus.get_service("spi_by_id") or {}
    pin_by_label = bus.get_service("pin_by_label") or {}

    pins = cfg.pop("pins", {})
    dc  = pin_by_label.get(pins.get("dc", ""))
    cs  = pin_by_label.get(pins["cs"])
    rst = pin_by_label.get(pins["rst"])

    missing = []
    if cs  is None: missing.append("cs={}".format(pins["cs"]))
    if rst is None: missing.append("rst={}".format(pins["rst"]))
    if missing:
        raise ValueError("TFT pins not found: {}".format(", ".join(missing)))

    # ⚠️ 必須先開電源，RM67162 才能接收 init 命令
    bl = pin_by_label.get(pins.get("bl", ""))
    if bl is not None:
        bl.value(1)
        print("[tft_drv] power ON (GPIO={})".format(pins.get("bl", "")))
    else:
        print("[tft_drv] no power pin — display may not be powered")

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

    # 全黑畫面 (整幀, TFT.show 含 flush, DMA queue 確保送出)
    black = bytearray(cfg["width"] * cfg["height"] * bpp)
    lcd.show(black)

    return lcd

def boot_config_i80(cfg):
    """I80 boot 模式 — 適用 ST7796 + N16R8 (XL9555 控制 RST/背光)"""
    cfg = dict(cfg)
    from lib.sys_bus import bus
    from lib.bus_adapter import I80BusAdapter

    i80 = bus.get_service("i80_bus")
    if i80 is None:
        print("[tft_drv] no I80 bus available, skipping")
        return None

    pin_by_label = bus.get_service("pin_by_label") or {}
    pins = cfg.pop("pins", {})

    dcx = pin_by_label.get(pins.get("dcx", ""))

    # ── XL9555: LCD 復位 + 背光 (從 config 讀腳位) ──
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

    adapter = I80BusAdapter(i80, dcx=dcx, rst=None)  # RST 由 XL9555 管理
    bpp = 3 if cfg.get("pixel_format", "").startswith("RGB888") else 2

    lcd = config(spi=None, dc=None, cs=None, rst=None,
                 bytes_per_pixel=bpp, adapter=adapter, **cfg)

    bus.register_service("lcd", lcd)
    bus.shared["tft_width"] = cfg["width"]
    bus.shared["tft_height"] = cfg["height"]
    bus.shared["tft_driver"] = cfg["driver"]

    # 全黑畫面
    black = bytearray(cfg["width"] * cfg["height"] * bpp)
    lcd.show(black)

    return lcd


def gpios():
    """TFT 不直接擁有 GPIO（SPI 由 spi_drv、控制腳由 pin_drv 註冊）"""
    return {}
