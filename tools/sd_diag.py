# -*- coding: utf-8 -*-
"""SD 卡硬體診斷 — 依序嘗試不同初始化方式，找出第一個成功的組合。

ENODEV (Errno 19) = 卡片對初始化序列 (CMD0/CMD8/ACMD41) 完全沒回應，
與 freq 無關 (SD 初始化固定跑 400kHz)。此腳本逐一測試:
  (1) SDIO 4-bit     (slot=0, width=4)
  (2) SDIO 1-bit     (slot=0, width=1, 只留 D0)
  (3) SPI 模式       (slot=2, 同一組線: sck / mosi=cmd / miso=D0 / cs=D3)
  (4) SDIO 4-bit + 內建上拉 (MicroPython 的 machine_sdcard.c 把
      SDMMC_SLOT_FLAG_INTERNAL_PULLUP 註解掉了 → 板上若無外部 10k
      上拉電阻，CMD/DATA 線懸空，卡片不會回應)

用法 (裝置上):
  import sd_diag
  sd_diag.run()

成功即停止。若某一步卡住或結果怪異，soft reset 後再跑。
"""
import gc
import machine


def _try(label, kwargs):
    print("\n── {} ──".format(label))
    print("    machine.SDCard({})".format(
        ", ".join("{}={}".format(k, v) for k, v in kwargs.items())))
    try:
        sd = machine.SDCard(**kwargs)
        n, ss = sd.info()[0], sd.info()[1]
        print("    ✅ 成功: {} sectors × {}B ≈ {} MB".format(
            n, ss, (n * ss) // 1048576))
        return sd
    except Exception as e:
        print("    ❌ {}".format(e))
        return None


def _pullup(pins):
    for p in pins:
        try:
            machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP)
        except Exception:
            pass


def run():
    from lib.sys_bus import bus
    cfg = bus.shared.get("SDcard") or {}
    g = cfg.get("GPIO", {}) or {}
    c = cfg.get("config", {}) or {}
    sck, cmd = g.get("sck"), g.get("cmd")
    data = g.get("data") or []
    freq = c.get("freq", 20000000)

    print("SD 診斷: sck={} cmd={} data={} freq={}Hz".format(sck, cmd, data, freq))
    if sck is None or cmd is None or not data:
        print("❌ config.json 的 SDcard.GPIO 不完整")
        return

    steps = [
        ("SDIO 4-bit", dict(slot=0, width=4, sck=sck, cmd=cmd, data=data[:4], freq=freq)),
        ("SDIO 1-bit (只接 D0)", dict(slot=0, width=1, sck=sck, cmd=cmd, data=[data[0]], freq=freq)),
    ]
    if len(data) >= 4:
        steps.append(("SPI 模式 (mosi=cmd miso=D0 cs=D3)",
                      dict(slot=2, sck=sck, mosi=cmd, miso=data[0], cs=data[3], freq=freq)))

    for label, kw in steps:
        if _try(label, kw):
            print("\n🎯 成功組合: " + label)
            return
        gc.collect()

    # 全部失敗 → 加內建上拉再試 (板上可能缺外部上拉)
    print("\n── 重試: 先以 PULL_UP 設定 SD 腳位 ──")
    _pullup([sck, cmd] + list(data[:4]))
    if _try("SDIO 4-bit + PULL_UP", dict(slot=0, width=4, sck=sck, cmd=cmd, data=data[:4], freq=freq)):
        print("\n🎯 成功組合: SDIO 4-bit + PULL_UP (板上 SD 腳位缺外部上拉)")
        return

    print("""
全部組合都失敗 → 問題在硬體層，依序檢查:
  1. SD 卡有插好? 換一張卡 / 清潔接點
  2. 三用電錶量 SD 插槽 VDD(第 4 腳) 對 GND: 必須 ≈3.3V
     (boot 的 esp32.LDO 是 P4 API，S3 上會失敗; 若板子靠它供電 → 卡沒電)
  3. CMD / D0-D3 到 3.3V 的外部上拉電阻 (10kΩ) 是否焊接
  4. 腳位與實際接線是否一致: sck={} cmd={} data={}""".format(sck, cmd, data))
