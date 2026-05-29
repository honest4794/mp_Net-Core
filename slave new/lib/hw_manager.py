from machine import Pin
from lib.sys_bus import bus
from lib.log_service import get_log

PIN  = 0
PWM  = 1
SPI  = 2
I2C  = 3
LED  = 4
LCD  = 5
SD   = 6
UART = 7
VBTN = 8

_VBTN_BYTES = 32
_PIN_CACHE = {}


def _get_pin(gpio_num):
    if gpio_num in _PIN_CACHE:
        return _PIN_CACHE[gpio_num]
    _PIN_CACHE[gpio_num] = Pin(gpio_num, Pin.OUT)
    return _PIN_CACHE[gpio_num]


def _vbtn_buf():
    key = "_vbtn"
    if key not in bus.shared:
        bus.shared[key] = bytearray(_VBTN_BYTES)
    return bus.shared[key]


def init_pins(config):
    pin_list = []
    pin_by_label = {}
    for item in config:
        gpio = item.get("GPIO")
        label = item.get("label", "pin_{}".format(gpio))
        if gpio is None:
            continue
        mode = item.get("mode", "OUT")
        initial = item.get("initial", 0)
        pull = item.get("pull")
        if mode == "IN":
            pull_mode = None
            if pull == "UP":
                pull_mode = Pin.PULL_UP
            elif pull == "DOWN":
                pull_mode = Pin.PULL_DOWN
            p = Pin(gpio, Pin.IN, pull=pull_mode)
        else:
            p = Pin(gpio, Pin.OUT, value=1 if initial else 0)
        pin_list.append(p)
        _PIN_CACHE[gpio] = p
        pin_by_label[label] = p

    bus.register_service("pin_list", pin_list)
    bus.register_service("pin_by_label", pin_by_label)
    get_log().info("PIN: {} pin(s)".format(len(pin_list)))
    return pin_list


def resolve_pin(identifier):
    if isinstance(identifier, int):
        return _get_pin(identifier)
    by_label = bus.get_service("pin_by_label") or {}
    p = by_label.get(identifier)
    if p is not None:
        return p
    raise ValueError("Pin not found: {}".format(identifier))


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
        elif dev_type == VBTN:
            if not (0 <= dev_id <= 255):
                return 0
            buf = _vbtn_buf()
            return (buf[dev_id >> 3] >> (dev_id & 0x07)) & 1
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
        elif dev_type == VBTN:
            if not (0 <= dev_id <= 255):
                return
            buf = _vbtn_buf()
            byte_idx = dev_id >> 3
            bit_idx = dev_id & 0x07
            if value:
                buf[byte_idx] = buf[byte_idx] | (1 << bit_idx)
            else:
                buf[byte_idx] = buf[byte_idx] & ~(1 << bit_idx)
    except Exception:
        pass


def vbtn_buf():
    return _vbtn_buf()


def list_all():
    rows = []
    for name in ("pin_list", "pwm_list", "spi_list", "spi_by_id", "i2c_list",
                 "led_list", "ws2812_list", "apa1022_list", "pca9685_list",
                 "lcd", "data_Phat", "circuit_bus_list", "st_LED"):
        svc = bus.get_service(name)
        if svc is not None:
            rows.append(name)
    rows.append("_PIN_CACHE ({})".format(len(_PIN_CACHE)))
    buf = bus.shared.get("_vbtn")
    if buf is not None:
        rows.append("_vbtn ({}B, Global)".format(len(buf)))
    return rows


HW = type("HW", (), {
    "PIN": PIN, "PWM": PWM, "SPI": SPI, "I2C": I2C,
    "LED": LED, "LCD": LCD, "SD": SD, "UART": UART, "VBTN": VBTN,
    "get": staticmethod(get),
    "set": staticmethod(set),
    "vbtn_buf": staticmethod(vbtn_buf),
    "list_all": staticmethod(list_all),
    "resolve_pin": staticmethod(resolve_pin),
})
