"""
統一硬體資源管理器

整合所有硬體資源的初始化查找與讀寫，取代各處分散的 cache 和直接存取。

使用方式:
  from lib.hw_manager import HW
  HW.get(HW.PWM, 0)        # 讀取 pwm_list[0] 的 duty
  HW.set(HW.PWM, 0, 512)   # 寫入 pwm_list[0] 的 duty
  HW.get(HW.PIN, 8)        # 讀取 GPIO 8 的值（自動快取 Pin 物件）
  HW.set(HW.PIN, 8, 1)     # 寫入 GPIO 8
  HW.list_all()             # 列出所有已註冊的硬體資源
"""

from machine import Pin
from lib.sys_bus import bus

# -- 設備類型常數 --
PIN = 0
PWM = 1
SPI = 2
I2C = 3
LED = 4
LCD = 5
SD  = 6
UART = 7

# -- Pin 快取 (單例) --
#   優先使用 boot 註冊的 pin_list（已設好 mode/pull/initial），
#   否則才自行建立 Pin(gpio, OUT)。
_PIN_CACHE = {}

def _get_pin(gpio_num):
    if gpio_num in _PIN_CACHE:
        return _PIN_CACHE[gpio_num]
    _PIN_CACHE[gpio_num] = Pin(gpio_num, Pin.OUT)
    return _PIN_CACHE[gpio_num]


def _init_pin_from_list():
    """由 boot 呼叫，把 pin_list 中的 Pin 物件填入快取"""
    plist = bus.get_service("pin_list")
    if plist is None:
        return
    cfg = bus.shared.get("PIN", {}) or {}
    items = cfg.get("list", []) or []
    for i, entry in enumerate(items):
        gpio = entry.get("GPIO")
        if gpio is not None and i < len(plist):
            _PIN_CACHE[gpio] = plist[i]


def get(dev_type, dev_id=None):
    try:
        if dev_type == PIN:
            return _get_pin(dev_id).value()
        elif dev_type == PWM:
            lst = bus.get_service("pwm_list")
            if lst and 0 <= dev_id < len(lst):
                return lst[dev_id].duty()
        elif dev_type == SPI:
            by_id = bus.get_service("spi_by_id")
            if by_id and dev_id in by_id:
                return by_id[dev_id]
            lst = bus.get_service("spi_list")
            if lst and 0 <= dev_id < len(lst):
                return lst[dev_id]
        elif dev_type == I2C:
            lst = bus.get_service("i2c_list")
            if lst and 0 <= dev_id < len(lst):
                return lst[dev_id]
        elif dev_type == LED:
            lst = bus.get_service("led_list")
            if lst and 0 <= dev_id < len(lst):
                return lst[dev_id]
        elif dev_type == LCD:
            return bus.get_service("lcd")
    except Exception:
        pass
    return None


def set(dev_type, dev_id, value):
    try:
        if dev_type == PIN:
            _get_pin(dev_id).value(1 if value else 0)
        elif dev_type == PWM:
            lst = bus.get_service("pwm_list")
            if lst and 0 <= dev_id < len(lst):
                lst[dev_id].duty(int(value))
    except Exception:
        pass


def list_all():
    rows = []
    for name in ("pin_list", "pwm_list", "spi_list", "spi_by_id", "i2c_list",
                 "led_list", "ws2812_list", "apa1022_list", "pca9685_list",
                 "lcd", "data_Phat", "circuit_bus_list", "st_LED"):
        svc = bus.get_service(name)
        if svc is not None:
            rows.append(name)
    rows.append("_PIN_CACHE ({})".format(len(_PIN_CACHE)))
    return rows


# -- 單例物件 --
HW = type("HW", (), {
    "PIN": PIN, "PWM": PWM, "SPI": SPI, "I2C": I2C,
    "LED": LED, "LCD": LCD, "SD": SD, "UART": UART,
    "get": staticmethod(get),
    "set": staticmethod(set),
    "list_all": staticmethod(list_all),
})
