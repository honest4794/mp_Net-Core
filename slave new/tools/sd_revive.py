"""SD 卡復甦工具

嘗試用不同參數喚醒卡片。如果成功，清空前 8MB 重置卡。
"""

import machine, os, time

def probe(slot, width, freq, sck, cmd, data):
    try:
        sd = machine.SDCard(
            slot=slot, width=width, freq=freq,
            sck=sck, cmd=cmd, data=data
        )
        info = sd.info()
        cap = info[0]; ss = info[1]
        print("  slot={} width={} freq={}M  -> {} sector={}".format(
            slot, width, freq // 1000000, _sz(cap), ss))
        return sd
    except Exception as e:
        print("  slot={} width={} freq={}M  -> {}".format(
            slot, width, freq // 1000000, e))
        return None


def _sz(b):
    for u in ("B","KB","MB","GB"):
        if b < 1024: return "{}{}".format(b, u)
        b //= 1024
    return "{}{}".format(b, "GB")


def wipe(sd, n_sectors=16384):
    ss = sd.info()[1]
    buf = bytearray(512)
    print("\n清除前 {} 個 sector ({} KB)...".format(n_sectors, n_sectors * ss // 1024))
    t0 = time.ticks_ms()
    for i in range(n_sectors):
        sd.writeblocks(i, buf)
        if i % 2000 == 0:
            print("  {}/{} sectors".format(i, n_sectors))
    t = time.ticks_diff(time.ticks_ms(), t0)
    print("  完成  {} ms  {:.1f} MB/s".format(t, n_sectors * ss / 1048576 / (t / 1000)))


def revive():
    print("\n" + "=" * 50)
    print("  SD 卡復甦工具")
    print("=" * 50)

    base = {"sck": 7, "cmd": 6, "data": [15, 16, 4, 5]}

    combos = [
        (0, 1, 10000000),
        (0, 1, 5000000),
        (0, 1, 2000000),
        (0, 4, 10000000),
        (0, 4, 5000000),
        (1, 1, 10000000),
        (1, 1, 5000000),
    ]

    sd = None
    for slot, width, freq in combos:
        sd = probe(slot, width, freq, base["sck"], base["cmd"], base["data"])
        if sd:
            break

    if not sd:
        print("\n所有參數組合都失敗。")
        print("請檢查 GPIO 接線，或換一張卡交叉測試。")
        return

    wipe(sd)

    print("\n卡已清除。重新插拔 USB，然後：")
    print("  diskutil eraseDisk FAT32 SDCARD MBR /dev/diskX")
    print("或在 ESP32 上用 Allocator.format()")


revive()
