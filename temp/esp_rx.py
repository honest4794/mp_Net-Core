"""
ESP-NOW 接收測試
exec(open("esp_rx.py").read())
"""

import network, espnow, time

CHANNEL = 6

sta = network.WLAN(network.STA_IF)
sta.active(True)
print("STA active:", sta.active())
sta.config(channel=CHANNEL)
print("STA channel:", sta.config("channel"))
time.sleep_ms(200)

e = espnow.ESPNow()
e.active(True)
print("ESPNow active:", e.active())
print("Listening ch", CHANNEL)
print()

try:
    n = 0
    while True:
        peer, msg = e.recv(5000)
        if peer is None:
            n += 1
            print("[{}] waiting...".format(n))
            continue

        print("---")
        print("from:", "".join("{:02X}".format(b) for b in peer))
        print("len:", len(msg))
        print("hex:", " ".join("{:02X}".format(b) for b in msg))
        try:
            print("txt:", msg.decode())
        except Exception:
            print("txt: <bin>")

        if len(msg) >= 9 and msg[:2] == b"NL":
            v = msg[2]
            a = msg[3] | (msg[4] << 8)
            c = msg[5] | (msg[6] << 8)
            pl = msg[7] | (msg[8] << 8)
            pay = msg[9:9+pl] if pl > 0 else b""
            print("Proto v={} a=0x{:04X} c=0x{:04X} pl={}".format(v, a, c, pl))
            if pay:
                print("pay:", " ".join("{:02X}".format(b) for b in pay))
        print()
except KeyboardInterrupt:
    print("stop")
finally:
    e.active(False)
    sta.active(False)
