from machine import Pin, SPI
from lib.sys_bus import bus

# ESP32-S3 N16R8 V1.0 — TF Card SPI
# SCK=47, MOSI=21, MISO=48
CONFIG = [
    {
        "id": 1,
        "baudrate": 20000000,
        "phase": 0,
        "polarity": 0,
        "GPIO": {"sck": 47, "mosi": 21, "miso": 48},
    },
]

try:
    import lcd_bus
    _LCD_BUS = True
except ImportError:
    _LCD_BUS = False


def _make_machine_spi(item, gpio, data):
    sid = item["id"]
    try:
        old = SPI(sid)
        old.deinit()
    except:
        pass
    sck = gpio.get("sck")
    mosi = gpio.get("mosi")
    miso = gpio.get("miso")
    return SPI(
        sid,
        baudrate=item.get("baudrate", 20000000),
        polarity=item.get("polarity", 0),
        phase=item.get("phase", 0),
        sck=Pin(sck) if sck is not None else None,
        mosi=Pin(mosi) if mosi is not None else None,
        miso=Pin(miso) if miso is not None else None,
    )


def config():
    spi_list = []
    spi_by_id = {}
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        data = item.get("data_pins")
        is_qspi = data is not None and len(data) > 1

        if _LCD_BUS and is_qspi:
            try:
                spi = lcd_bus.SPIBus(
                    data=data, clk=gpio["sck"],
                    freq=item.get("baudrate", 20000000),
                    host=item["id"],
                )
            except Exception as e:
                print("[spi_drv] SPI{} lcd_bus fail: {} → machine.SPI".format(item["id"], e))
                if 'spi' in locals():
                    try: spi.deinit()
                    except: pass
                spi = _make_machine_spi(item, gpio, data)
        else:
            spi = _make_machine_spi(item, gpio, data)

        spi_list.append(spi)
        spi_by_id[item["id"]] = spi

    bus.register_service("spi_list", spi_list)
    bus.register_service("spi_by_id", spi_by_id)
    # 統一 lcd_bus 池
    lst = bus.get_service("lcd_bus") or []
    for s in spi_list:
        lst.append(s)
    bus.register_service("lcd_bus", lst)
    return spi_list, spi_by_id


def gpios():
    result = {}
    for item in CONFIG:
        gpio = item.get("GPIO", {})
        for name in ("sck", "mosi", "miso"):
            pin = gpio.get(name)
            if pin is not None:
                result[pin] = "spi{}_{}".format(item.get("id", "?"), name)
        data = item.get("data_pins")
        if data:
            for i, d in enumerate(data):
                result[d] = "spi{}_d{}".format(item.get("id", "?"), i)
    return result
