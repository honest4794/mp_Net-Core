class BusAdapter:
    def write_cmd(self, cmd):
        raise NotImplementedError

    def write_data(self, data):
        return self.write_data_async(data)

    def write_cmd_data(self, cmd, data=None):
        self.write_cmd(cmd)
        if data:
            self.write_data(data)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        self.write_data(bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self.write_cmd(0x2B)
        self.write_data(bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self.write_cmd(0x2C)

    def reset(self):
        raise NotImplementedError

    def write_data_async(self, data):
        raise NotImplementedError

    def flush(self):
        pass

    def wait(self, handle):
        pass


class SpiBusAdapter(BusAdapter):
    def __init__(self, spi, dc=None, cs=None, rst=None):
        self._spi = spi
        self._dc = dc
        self._cs = cs
        self._rst = rst
        self._dma = hasattr(spi, 'wait') and hasattr(spi, 'pending')
        self._qspi = hasattr(spi, 'lane_count') and spi.lane_count() > 1

    def write_cmd(self, cmd):
        if self._qspi:
            self._cs.value(0)
            self._spi.write(b'\x00', cmd=0x02, addr=cmd << 8)
            self._spi.wait_all()
            self._cs.value(1)
        elif self._dma:
            self._dc.value(0)
            self._cs.value(0)
            self._spi.write(bytearray([cmd]))
            self._spi.wait_all()
        else:
            self._dc.value(0)
            self._cs.value(0)
            self._spi.write(bytearray([cmd]))
            self._cs.value(1)

    def write_cmd_data(self, cmd, data=None):
        if self._qspi:
            self._cs.value(0)
            payload = data if data else b'\x00'
            self._spi.write(payload, cmd=0x02, addr=cmd << 8)
            self._spi.wait_all()
            self._cs.value(1)
        elif self._dma:
            self._dc.value(0)
            self._cs.value(0)
            self._spi.write(bytearray([cmd]))
            self._spi.wait_all()
            if data:
                self._dc.value(1)
                self._spi.write(data)
                self._spi.wait_all()
        else:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)

    def write_data_async(self, data):
        if self._qspi:
            self._cs.value(0)
            try:
                return self._spi.write(data)
            except RuntimeError:
                return None
        if self._dma:
            self._dc.value(1)
            while self._spi.pending() >= 4:
                self._spi.wait_all()
            try:
                return self._spi.write(data)
            except RuntimeError:
                return None
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(data)
        self._cs.value(1)
        return True

    def flush(self):
        if self._qspi:
            self._spi.wait_all()
            self._cs.value(1)
        elif self._dma:
            self._spi.wait_all()
            self._cs.value(1)

    def write_frame(self, data):
        if self._qspi:
            self._cs.value(0)
            self._spi.write(b'', cmd=0x32, addr=0x002C00, multiline=False)
            mv = memoryview(data)
            off, rem = 0, len(mv)
            while rem > 0:
                n = min(rem, 32768)
                tid = self._spi.write(mv[off:off + n])
                self.wait(tid)
                rem -= n; off += n
            self._cs.value(1)
        elif self._dma:
            self._dc.value(1); self._cs.value(0)
            mv = memoryview(data)
            off, rem = 0, len(mv)
            while rem > 0:
                n = min(rem, 32768)
                tid = self._spi.write(mv[off:off + n])
                self.wait(tid)
                rem -= n; off += n
            self._cs.value(1)
        else:
            self._dc.value(1); self._cs.value(0); self._spi.write(data); self._cs.value(1)

    def wait(self, handle):
        if self._qspi and handle is not None:
            self._spi.wait(handle)
        elif self._dma and handle is not None:
            self._spi.wait(handle)

    def set_window(self, x0, y0, x1, y1):
        if self._qspi:
            self._cs.value(0)
            self._spi.write(
                bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]),
                cmd=0x02, addr=0x2A << 8)
            self._spi.wait_all()
            self._cs.value(1)
            self._cs.value(0)
            self._spi.write(
                bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]),
                cmd=0x02, addr=0x2B << 8)
            self._spi.wait_all()
            self._cs.value(1)
            self._cs.value(0)
            self._spi.write(b'', cmd=0x32, addr=0x002C00, multiline=False)
            self._spi.wait_all()
        elif self._dma:
            self._cs.value(0)
            self._dc.value(0); self._spi.write(bytearray([0x2A])); self._spi.wait_all()
            self._dc.value(1); self._spi.write(bytes([x0>>8,x0&0xFF,x1>>8,x1&0xFF])); self._spi.wait_all()
            self._dc.value(0); self._spi.write(bytearray([0x2B])); self._spi.wait_all()
            self._dc.value(1); self._spi.write(bytes([y0>>8,y0&0xFF,y1>>8,y1&0xFF])); self._spi.wait_all()
            self._dc.value(0); self._spi.write(bytearray([0x2C])); self._spi.wait_all(); self._dc.value(1)
        else:
            super().set_window(x0, y0, x1, y1)

    def reset(self):
        # I80 bus C level handles DC/CS; no external RST pin needed
        pass


class I2cBusAdapter(BusAdapter):
    def __init__(self, i2c, addr, rst=None, cmd_ctrl=0x00, data_ctrl=0x40):
        self._i2c = i2c
        self._addr = addr
        self._rst = rst
        self._cmd_ctrl = cmd_ctrl
        self._data_ctrl = data_ctrl
        self._dma = hasattr(i2c, 'wait') and hasattr(i2c, 'pending')

    def write_cmd(self, cmd):
        buf = bytearray([self._cmd_ctrl, cmd])
        if self._dma:
            self._i2c.write(buf)
            self._i2c.wait_all()
        else:
            self._i2c.writeto(self._addr, buf)

    def write_data_async(self, data):
        buf = bytearray(len(data) + 1)
        buf[0] = self._data_ctrl
        buf[1:] = data
        if self._dma:
            try:
                return self._i2c.write(buf)
            except RuntimeError:
                return None
        self._i2c.writeto(self._addr, buf)
        return True

    def reset(self):
        if self._rst is None:
            return
        self._rst.value(0)
        import time
        time.sleep_ms(50)
        self._rst.value(1)
        time.sleep_ms(50)


class I80BusAdapter(BusAdapter):
    def __init__(self, bus, dc=None, cs=None, rst=None):
        self._bus = bus
        self._spi = None  # 統一 API：SPI/I2C/I80 都有 _spi
        self._dc = dc
        self._cs = cs
        self._rst = rst

    def write_cmd(self, cmd):
        self._bus.wait_all()
        self._bus.write(cmd=cmd)

    def write_cmd_data(self, cmd, data=None):
        self._bus.wait_all()
        if data:
            self._bus.write(buf=data, cmd=cmd)
        else:
            self._bus.write(cmd=cmd)
        self._bus.wait_all()

    def write_data_async(self, data):
        while self._bus.pending() >= 4:
            self._bus.wait_all()
        try:
            return self._bus.write(buf=data)
        except RuntimeError:
            return None

    def set_window(self, x0, y0, x1, y1):
        self._bus.wait_all()
        self._bus.write(cmd=0x2A)
        self._bus.write(buf=bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._bus.write(cmd=0x2B)
        self._bus.write(buf=bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._bus.write(cmd=0x2C)
        self._bus.wait_all()

    def flush(self):
        self._bus.wait_all()

    def wait(self, handle):
        self._bus.wait(handle)

    def write_frame(self, data):
        # I80: DMA 非同步寫，含 backpressure
        mv = memoryview(data)
        off, rem = 0, len(mv)
        while rem > 0:
            while self._bus.pending() >= 4:
                self._bus.wait_all()
            n = min(rem, 32768)
            self._bus.write(buf=mv[off:off + n])
            rem -= n; off += n
        self._bus.wait_all()

    def reset(self):
        if self._rst is None:
            return
        self._rst.value(0)
        import time
        time.sleep_ms(50)
        self._rst.value(1)
        time.sleep_ms(50)


class RgbBusAdapter(BusAdapter):
    def __init__(self, bus, width, height):
        self._bus = bus
        self._width = width
        self._height = height
        self._dma = hasattr(bus, 'wait') and hasattr(bus, 'pending')

    def write_cmd(self, cmd):
        pass

    def write_data_async(self, data):
        if self._dma:
            try:
                return self._bus.write(buf=data)
            except RuntimeError:
                return None
        self._bus.write(data)
        return True

    def set_window(self, x0, y0, x1, y1):
        pass

    def write_cmd_data(self, cmd, data=None):
        pass

    def flush(self):
        if self._dma:
            self._bus.wait_all()

    def wait(self, handle):
        if self._dma and handle is not None:
            self._bus.wait(handle)

    def reset(self):
        pass
