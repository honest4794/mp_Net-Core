"""
ESP-NOW 發送測試 — 每隔 2 秒廣播一封包
exec(open("esp_tx.py").read())
"""

import network, espnow, time

CHANNEL = 6

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=CHANNEL)
time.sleep_ms(200)

e = espnow.ESPNow()
e.active(True)
e.add_peer(b'\xff\xff\xff\xff\xff\xff')
print("ESPNow TX ch", CHANNEL)

try:
    n = 0
    while True:
        n += 1
        msg = b"test_" + str(n).encode()
        e.send(b'\xff\xff\xff\xff\xff\xff', msg)
        print("[TX]", msg)
        time.sleep(2)
except KeyboardInterrupt:
    print("stop")
finally:
    e.active(False)
    sta.active(False)
