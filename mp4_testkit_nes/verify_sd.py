import os, json, ubinascii

def main():
    from machine import SDCard

    cfg = json.load(open("/config.json"))
    sdcfg = cfg.get("SDcard", {})
    slot = sdcfg.get("config", {}).get("slot", 0)
    width = sdcfg.get("config", {}).get("width", 4)
    freq = sdcfg.get("config", {}).get("freq", 40_000_000)
    gpio = sdcfg.get("GPIO", {})
    sck = gpio.get("sck"); cmd = gpio.get("cmd")
    data = tuple(int(x) for x in (gpio.get("data") or ()))

    print("init SD slot={} width={} sck={} cmd={} data={} freq={}".format(slot, width, sck, cmd, data, freq))
    sd = SDCard(slot=slot, width=width, sck=sck, cmd=cmd, data=data, freq=freq)
    info = sd.info()
    print("SD info: {} {}".format(info[0], info[1]))

    # ---- test raw sector BEFORE mount ----
    test = bytearray(512)
    print("\n--- BEFORE os.mount ---")
    for label, sec in [("MBR", 0), ("JPK", 1048576), ("RGB565", 1214484), ("RGB888", 1998384)]:
        sd.readblocks(sec, test)
        h = ubinascii.hexlify(test[:64])
        all_00 = all(b == 0x00 for b in test)
        all_ff = all(b == 0xFF for b in test)
        tag = "OK" if not all_00 and not all_ff else ("ALL00" if all_00 else "ALLFF")
        print("  sec {} {}  {}".format(sec, tag, h))

    # ---- mount ----
    os.mount(sd, "/sd")

    # ---- test raw sector AFTER mount ----
    print("\n--- AFTER os.mount ---")
    test2 = bytearray(512)
    for label, sec in [("MBR", 0), ("JPK", 1048576), ("RGB565", 1214484), ("RGB888", 1998384)]:
        sd.readblocks(sec, test2)
        h2 = ubinascii.hexlify(test2[:64])
        all_00_2 = all(b == 0x00 for b in test2)
        all_ff_2 = all(b == 0xFF for b in test2)
        tag2 = "OK" if not all_00_2 and not all_ff_2 else ("ALL00" if all_00_2 else "ALLFF")
        print("  sec {} {}  {}".format(sec, tag2, h2))

    os.umount("/sd")

main()
