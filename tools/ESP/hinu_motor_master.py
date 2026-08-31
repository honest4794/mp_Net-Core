"""MicroPython black-Master NC4 sender for the Hi-Nu motor bench."""

import struct
import time

try:
    import ubinascii as binascii
except ImportError:
    import binascii

from machine import Pin, UART


SOF = b"NC"
VERSION = 4
BROADCAST = 0xFFFF
MODE_SET = 0x3105
MODE_STOP = 0x3106
REBOOT = 0x100F


def _pack(command, payload=b"", address=BROADCAST):
    header = struct.pack("<2sBHHH", SOF, VERSION, address, command, len(payload))
    crc = binascii.crc32(header[2:] + payload) & 0xFFFFFFFF
    return header + payload + struct.pack("<I", crc)


class Link:
    def __init__(self):
        self.uart = UART(1, 115200, tx=Pin(10), rx=Pin(11), rxbuf=2048, txbuf=2048)
        self.enable = Pin(9, Pin.OUT, value=0)

    def _wait_bus_quiet(self, quiet_ms=3, timeout_ms=500):
        quiet = 0
        for _ in range(int(timeout_ms)):
            waiting = self.uart.any()
            if waiting:
                self.uart.read(waiting)
                quiet = 0
            else:
                quiet += 1
                if quiet >= int(quiet_ms):
                    return
            time.sleep_ms(1)
        raise OSError("RS485 bus stayed busy")

    def send(self, frame):
        self._wait_bus_quiet()
        self.enable.value(1)
        time.sleep_ms(1)
        try:
            written = self.uart.write(frame)
            if hasattr(self.uart, "flush"):
                self.uart.flush()
            elif hasattr(self.uart, "txdone"):
                while not self.uart.txdone():
                    time.sleep_ms(0)
        finally:
            self.enable.value(0)
        return written


def send_mode(mode_id, start_delay_ms=300):
    mode_id = int(mode_id)
    if mode_id not in (0, 1, 2, 3):
        raise ValueError("mode_id must be 0, 1, 2, or 3")
    delay = max(0, min(65535, int(start_delay_ms)))
    payload = struct.pack("<BBHB", 1, mode_id, delay, 255)
    written = Link().send(_pack(MODE_SET, payload))
    print("MODE_SET mode={} delay={} bytes={}".format(mode_id, delay, written))
    return written


def stop():
    written = Link().send(_pack(MODE_STOP, b"\x01"))
    print("MODE_STOP action=1 bytes={}".format(written))
    return written


def reboot_slaves(delay_ms=100):
    delay_ms = max(0, min(0xFFFFFFFF, int(delay_ms)))
    written = Link().send(_pack(REBOOT, struct.pack("<I", delay_ms)))
    print("REBOOT delay={} bytes={}".format(delay_ms, written))
    return written
