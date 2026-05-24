from lib.ESP_Boot import *
from lib.LEDController import *
from lib.ConfigManager import *
from lib.sys_bus import bus
from lib.log_service import get_log
import machine, os, ubinascii

try:
    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
except Exception:
    try:
        bus.slave_id = "".join("{:02X}".format(b) for b in machine.unique_id())
    except Exception:
        bus.slave_id = "UNKNOWN"


def exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True


def init_bus(sysBus):
    
    SPI_config = sysBus.shared['SPI']
    spi_list = []
    spi_by_id = {}
    if SPI_config['enable']:
        for i in SPI_config['list']:
            spi = machine.SPI(i['id'],
                baudrate=i['baudrate'],
                polarity=i['polarity'],
                phase=i['phase'],
                sck=machine.Pin(i['GPIO']['sck']) if i['GPIO']['sck'] else None ,
                mosi=machine.Pin(i['GPIO']['mosi']) if i['GPIO']['mosi'] else None ,
                miso=machine.Pin(i['GPIO']['miso']) if i['GPIO']['miso'] else None
            )
            spi_list.append(spi)            
            spi_by_id[i['id']] = spi
        sysBus.register_service("spi_list", spi_list)
        sysBus.register_service("spi_by_id", spi_by_id)
        
    I2C_config = sysBus.shared['I2C']
    i2c_list = []
    if I2C_config['enable']:
        for i in I2C_config['list']:
            i2c = machine.I2C(i['id'],
                freq=i['freq'] if i['freq'] else None,
                scl=machine.Pin(i['GPIO']['scl']) if i['GPIO']['scl'] else None ,
                sda=machine.Pin(i['GPIO']['sda']) if i['GPIO']['sda'] else None 
            )
            i2c_list.append(i2c)            
        sysBus.register_service("i2c_list", i2c_list)
        
        
    return

def init_led(sysBus):
    
    PCA9685_config = sysBus.shared['PCA9685']
    pca9685_list = []
    if PCA9685_config['enable']:
        for i in PCA9685_config['list']:
            if sysBus.shared['I2C']['enable']:
                try:
                    i2c_list = sysBus.get_service("i2c_list")
                    for i2c in i2c_list:
                        devices = i2c.scan()
                        get_log().info(f"I2C Scan found: {[hex(d) for d in devices]}")
                        for addr in devices:
                            try:
                                if addr != 112:
                                    pca = PCA9685(i2c, address=addr)
                                    pca.freq(1000)
                                    pca9685_list.append(LEDController('i2c_LED', {'led_IO': pca, 'Q': 16, 'order': 'W'}))
                            except Exception as e:
                                get_log().error(f"❌ PCA9685 at {hex(addr)} error: {e}")
                except Exception as e:
                    get_log().error(f"❌ PCA9685 at {hex(i['address'])} error: {e}")
        sysBus.register_service("pca9685_list", pca9685_list)
    
    
    WS2812_config = sysBus.shared['WS2812']
    ws2812_list = []
    if WS2812_config['enable']:
        import neopixel
        for i in WS2812_config['list']:
            pixel = neopixel.NeoPixel(machine.Pin(i['GPIO'], machine.Pin.OUT),i['Q'])
            ws2812_list.append(LEDController('WS2812', {'led_IO': pixel, 'Q': i['Q'], 'order': i['order']}))
            
        sysBus.register_service("ws2812_list", ws2812_list)
        
        
    APA102_config = sysBus.shared['APA102']
    apa1022_list = []
    if APA102_config['enable']:
        if sysBus.shared['SPI']['enable']:
            for i in APA102_config['list']:
                try:
                    spi_list = sysBus.get_service("spi_list")
                    apa = APA102(spi_list[i['GPIO']['spi']], num_leds=i['Q'])
                    apa1022_list.append(LEDController('APA102', {'led_IO': apa, 'Q': i['Q'], 'order': i['order']}))
                except Exception as e:
                    get_log().error(f"❌ APA102 at SPI ID {i['GPIO']['spi']} error: {e}")
                        
        sysBus.register_service("apa1022_list", apa1022_list)
            
    sysBus.register_service("led_list", apa1022_list + ws2812_list + pca9685_list)
    return

def init_st(sysBus):
    try:
        st_LED = LEDStreamer(sysBus.get_service("led_list"))
        st_LED.show_all()
        sysBus.register_service("st_LED", st_LED)
    except Exception as e:
        get_log().error(f"❌ st_LED init error: {e}")
    return


def init_pwm(sysBus):
    pwm_cfg = sysBus.shared.get('PWM', {})
    if not pwm_cfg.get('enable', 0):
        return
    try:
        from machine import Pin, PWM
        pwm_list = []
        for item in pwm_cfg.get('list', []):
            gpio = item.get('GPIO')
            if gpio is None:
                continue
            pwm = PWM(Pin(gpio), freq=1000, duty=0)
            pwm_list.append(pwm)
        sysBus.register_service("pwm_list", pwm_list)
        get_log().info(f"PWM initialized: {len(pwm_list)} channel(s)")
    except Exception as e:
        get_log().error(f"❌ PWM init error: {e}")
    return


def init_pin(sysBus):
    pin_cfg = sysBus.shared.get('PIN', {})
    if not pin_cfg.get('enable', 0):
        return
    try:
        from machine import Pin
        pin_list = []
        for item in pin_cfg.get('list', []):
            gpio = item.get('GPIO')
            if gpio is None:
                continue
            mode = item.get('mode', 'OUT')
            initial = item.get('initial', 0)
            pull = item.get('pull')
            if mode == 'IN':
                pull_mode = None
                if pull == 'UP':
                    pull_mode = Pin.PULL_UP
                elif pull == 'DOWN':
                    pull_mode = Pin.PULL_DOWN
                p = Pin(gpio, Pin.IN, pull=pull_mode)
            else:
                p = Pin(gpio, Pin.OUT, value=1 if initial else 0)
            pin_list.append(p)
        sysBus.register_service("pin_list", pin_list)
        from lib.hw_manager import _init_pin_from_list
        _init_pin_from_list()
        get_log().info("PIN initialized: {} pin(s)".format(len(pin_list)))
    except Exception as e:
        get_log().error("PIN init error: {}".format(e))
    return


def _init_sd_spi(config, _phat):
    sd = machine.SDCard(
        slot=config['config'].get('slot', 2),
        sck=config['GPIO']['sck'],
        mosi=config['GPIO']['cmd'],
        miso=config['GPIO']['data'][0],
        cs=config['GPIO']['data'][3],
        freq=config['config'].get('freq', 20_000_000),
    )
    os.mount(sd, _phat)


def _init_sd_sdio(config, _phat):
    sd = machine.SDCard(slot=config['config']['slot'], width=config['config']['width'],
    sck=config['GPIO']['sck'], cmd=config['GPIO']['cmd'],
    data=config['GPIO']['data'],
    freq=config['config']['freq'])
    os.mount(sd, _phat)


def init_sd(sysBus):
    config = sysBus.shared['SDcard']
    _phat = ''
    if config['enable'] and not exists(config["phat"]):
        _phat = config["phat"]
        try:
            from esp32 import LDO
            ldo = LDO(config['LDO']['id'], config['LDO']['mv'], adjustable=True)

        except Exception as e:
            get_log().error(f"LEO error: {e}")

        slot = config['config'].get('slot', 0)
        try:
            if slot >= 2:
                _init_sd_spi(config, _phat)
            else:
                _init_sd_sdio(config, _phat)
        except Exception as e:
            get_log().error(f"❌ SD card init error: {e}")

    sysBus.register_service("data_Phat", _phat)
    return

# 網路初始化已移至 NetworkTask.on_start()
init_bus(bus)
init_led(bus)
init_st(bus)
init_pwm(bus)
init_pin(bus)
init_sd(bus)

# LCD 初始化已移至 DisplayTask.on_start()
