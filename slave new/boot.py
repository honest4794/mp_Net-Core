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

from driver.i2c_drv import config as init_i2c, gpios as gpios_i2c
from driver.pin_drv import config as init_pin, gpios as gpios_pin
from driver.i80_drv import config as init_i80, gpios as gpios_i80
from driver.pwm_drv import config as init_pwm, gpios as gpios_pwm
from driver.uart_drv import config as init_uart, gpios as gpios_uart
from driver.i2s_drv import config as init_i2s, gpios as gpios_i2s
from driver.sd_drv import config as init_sd, gpios as gpios_sd
from driver.ws2812_drv import config as init_ws2812, gpios as gpios_ws2812
from driver.apa102_drv import config as init_apa102, gpios as gpios_apa102
from driver.pca9685_drv import config as init_pca9685, gpios as gpios_pca9685
from driver.led_drv import config as init_led, gpios as gpios_led
from driver.xl9555_drv import config as init_xl9555, gpios as gpios_xl9555
from driver.gt1151q_drv import config as init_gt1151q, gpios as gpios_gt1151q
from driver.network_drv import config as init_network
from driver.tft_drv import boot_config as init_tft_boot, gpios as gpios_tft

# ══════════════════════════════════════════════════════
# 一級硬件初始化 (Level 1)
# ══════════════════════════════════════════════════════
LEVEL1 = [
        ("i80",      init_i80,      gpios_i80),
    ("pin",      init_pin,      gpios_pin),
    ("pwm",      init_pwm,      gpios_pwm),
    ("i2c",      init_i2c,      gpios_i2c),
    ("sd",       init_sd,       gpios_sd),
]

# ══════════════════════════════════════════════════════
# 應用硬件驅動 (Application)
# ══════════════════════════════════════════════════════
APP_DRV = [
    ("ws2812",   init_ws2812,   gpios_ws2812,   []),
    ("apa102",   init_apa102,   gpios_apa102,   []),
    ("pca9685",  init_pca9685,  gpios_pca9685,  []),
    ("led",      init_led,      gpios_led,      {}),
    ("xl9555",   init_xl9555,   gpios_xl9555,   {}),
    ("gt1151q",  init_gt1151q,  gpios_gt1151q,  {}),
    ("tft",      init_tft_boot, gpios_tft,      {
        "driver": "ST7796",
        "width": 480,
        "height": 320,
        "rotation": 0,
        "color_order": "RGB",
        "invert": False,
        "pins": {"dc": "tft_rs", "cs": "tft_cs", "rst": "lcd_rst", "bl": "bl_ctr"},
        "pixel_format": "RGB565_BE",
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

# ── Phase 3: 應用硬件驅動初始化 ──
for name, init_fn, _, cfg in APP_DRV:
    init_fn(cfg)

# ── Network ──
init_network()

