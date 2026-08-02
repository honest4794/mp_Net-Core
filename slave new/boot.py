# boot.py
# 硬體初始化 — config.json (扁平 {enable, list}) → driver init_xxx(bus) → bus service
#
# 流程:
#   Phase 1: 各 driver gpios() 回報腳位 → bus.gpio_claim → validate (衝突檢查)
#   Phase 2: 線性呼叫 init_xxx(bus) 建立硬體 Object 並註冊到 bus
#
# 要停用某 driver：註解 Phase 1 與 Phase 2 對應兩行即可。

from lib.ConfigManager import *
from lib.sys_bus import bus
import ubinascii, machine

try:
    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
except Exception:
    try:
        bus.slave_id = "".join("{:02X}".format(b) for b in machine.unique_id())
    except Exception:
        bus.slave_id = "UNKNOWN"

from driver.spi_drv      import init_spi,      gpios as g_spi
from driver.pin_drv      import init_pin,      gpios as g_pin
from driver.i2c_drv      import init_i2c,      gpios as g_i2c
from driver.uart_drv     import init_uart,     gpios as g_uart
from driver.pwm_drv      import init_pwm,      gpios as g_pwm
from driver.i2s_drv      import init_i2s,      gpios as g_i2s
from driver.sd_drv       import init_sd,       gpios as g_sd
from driver.tft_drv      import init_tft,      gpios as g_tft
from driver.enc_drv      import init_enc,      gpios as g_enc
from driver.network_drv  import init_network


# ══════════════════════════════════════════════════════
# Phase 1: GPIO claim + 衝突檢查
#   (name, gpios_fn) — driver 透過 gpios(bus) 回報自己用的腳位
# ══════════════════════════════════════════════════════
DRIVERS = [
    ("spi",  g_spi),
    ("pin",  g_pin),
    ("i2c",  g_i2c),
    ("uart", g_uart),
    ("pwm",  g_pwm),
    ("i2s",  g_i2s),
    ("sd",   g_sd),
    ("tft",  g_tft),
    ("enc",  g_enc),
]

for name, gpios_fn in DRIVERS:
    for gpio, label in gpios_fn(bus).items():
        bus.gpio_claim(gpio, name, label)

bus.gpio_validate()
bus.gpio_dump()


# ══════════════════════════════════════════════════════
# Phase 2: 線性硬體初始化
#   順序: 匯流排 (spi/pin/i2c/uart) → sd → tft → network
#   driver 內部會檢查 bus.shared["XXX"]["enable"]，未啟用即跳過
# ══════════════════════════════════════════════════════
init_spi(bus)
init_pin(bus)
init_i2c(bus)
init_uart(bus)
# init_pwm(bus)
# init_i2s(bus)
init_sd(bus)
init_tft(bus)
init_enc(bus)
init_network(bus)


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
