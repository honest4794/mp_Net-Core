from lib.ConfigManager import *
from lib.sys_bus import bus
from lib.log_service import get_log
import machine
import ubinascii

try:
    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
except Exception:
    try:
        bus.slave_id = "".join("{:02X}".format(b) for b in machine.unique_id())
    except Exception:
        bus.slave_id = "UNKNOWN"

from driver.spi_drv import config as init_spi, gpios as gpios_spi
from driver.i2c_drv import config as init_i2c, gpios as gpios_i2c
from driver.pin_drv import config as init_pin, gpios as gpios_pin
from driver.pwm_drv import config as init_pwm, gpios as gpios_pwm
from driver.uart_drv import config as init_uart, gpios as gpios_uart
from driver.i2s_drv import config as init_i2s, gpios as gpios_i2s
from driver.sd_drv import config as init_sd, gpios as gpios_sd
from driver.ws2812_drv import config as init_ws2812, gpios as gpios_ws2812
from driver.apa102_drv import config as init_apa102, gpios as gpios_apa102
from driver.pca9685_drv import config as init_pca9685, gpios as gpios_pca9685
from driver.led_drv import config as init_led, gpios as gpios_led
from driver.network_drv import config as init_network
from driver.tft_drv import boot_config as init_tft_boot, gpios as gpios_tft

# ══════════════════════════════════════════════════════
# 一級硬件初始化 (Level 1) — 底層匯流排、GPIO、周邊
#   config 寫在 driver/_drv.py 的 CONFIG 中
#   要啟用 → 加入 tuple，要停用 → 註解整行
# ══════════════════════════════════════════════════════
LEVEL1 = [
    ("spi",      init_spi,      gpios_spi),
    ("pin",      init_pin,      gpios_pin),
    ("pwm",      init_pwm,      gpios_pwm),
    ("i2c",      init_i2c,      gpios_i2c),
    ("sd",       init_sd,       gpios_sd),
    ("uart",   init_uart,     gpios_uart),
    # ("i2s",    init_i2s,      gpios_i2s),
]

# ══════════════════════════════════════════════════════
# 應用硬件驅動 (Application) — config 寫在這裡
#   格式: (name, init_fn, gpios_fn, CONFIG)
# ══════════════════════════════════════════════════════
APP_DRV = [
#     ("ws2812",   init_ws2812,   gpios_ws2812,   []),
#     ("apa102",   init_apa102,   gpios_apa102,   []),
#     ("pca9685",  init_pca9685,  gpios_pca9685,  []),
#     ("led",      init_led,      gpios_led,      {}),
    ("tft",      init_tft_boot, gpios_tft,      {
        "driver": "ST7789",
        "width": 240,
        "height": 320,
        "rotation": 0,
        "color_order": "RGB",
        "invert": 1,
        "spi_id": 1,
        "pins": {"dc": "tft_dc", "cs": "tft_cs", "rst": "tft_rst", "bl": "tft_bl"},
        "pixel_format": "RGB565_BE",
        "variant": 0,
    }),
]

# ── Phase 1: GPIO claim ──
for name, _, gpios_fn, *_ in LEVEL1 + APP_DRV:
    for gpio, label in gpios_fn().items():
        bus.gpio_claim(gpio, name, label)

bus.gpio_validate()
bus.gpio_dump()

# ── Phase 2: 一級硬件初始化 ──
for name, init_fn, *_ in LEVEL1:
    init_fn()

# ── Phase 3: 應用硬件驅動初始化 (傳入 config) ──
for name, init_fn, _, cfg in APP_DRV:
    init_fn(cfg)

# ── Network (需排在最末) ──
init_network()

# ── 統一資料層 (fs)：永遠確保 /sd 存在 + 註冊成 service "data" ──
import os as _os
try:
    _os.stat("/sd")
except Exception:
    try:
        _os.mkdir("/sd")
    except Exception:
        pass
from lib.fs_manager import fs
bus.register_service("data", fs)
