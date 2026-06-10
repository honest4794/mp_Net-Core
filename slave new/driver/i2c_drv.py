from machine import Pin, I2C
from lib.sys_bus import bus

# ESP32-S3 N16R8 V1.0
# I2C0 — XL9555 IO Expander (SDA=2, SCL=1)
# I2C1 — GT1151Q Touch (SDA=41, SCL=40)
CONFIG = [
    {
        "id": 0,
        "freq": 400000,
        "GPIO": {"scl": 1, "sda": 2},
    },
    {
        "id": 1,
        "freq": 400000,
        "GPIO": {"scl": 40, "sda": 41},
    },
]


def config():
    i2c_list = []
    i2c_by_id = {}
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        i2c = I2C(
            item["id"],
            freq=item.get("freq"),
            scl=Pin(gpio["scl"]) if gpio.get("scl") is not None else None,
            sda=Pin(gpio["sda"]) if gpio.get("sda") is not None else None,
        )
        i2c_list.append(i2c)
        i2c_by_id[item["id"]] = i2c

    bus.register_service("i2c_list", i2c_list)
    bus.register_service("i2c_by_id", i2c_by_id)
    return i2c_list


def gpios():
    result = {}
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        for name in ("scl", "sda"):
            pin = gpio.get(name)
            if pin is not None:
                result[pin] = "i2c{}_{}".format(item.get("id", "?"), name)
    return result
