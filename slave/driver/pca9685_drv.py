"""
pca9685_drv.py — PCA9685 PWM pixel 管理 (走 I2C)

設定來源: bus.shared["PCA9685"]  ({enable, list})
         list item: {"i2c": <i2c_list index>, "address": ["0x40"]}
產物:    bus.register_service("pca9685_list", [...])

address 特殊值:
  "0xFF" (255) — 自動掃描: i2c.scan() 找匯流排上所有 PCA9685, 排除 0x70
                廣播位址, 逐個真實位址各建一個 controller, 對所有板子送出
                相同內容 (之後加板子不用改 config)。
  "0x70" (112) — PCA9685 ALLCALL 廣播位址, 不建議作為一般裝置位址。
"""
from lib.sys.log_service import get_log
from lib.hw.pca9685 import PCA9685
from lib.sys.sys_bus import bus

# PCA9685 ALLCALL 廣播位址 (112 = 0x70)。所有 writeto_mem 寫到 0x70 都是
# 廣播: 匯流排上所有啟用 ALLCALL 的 PCA9685 同時收到。因此 0x70 不該當
# 一般裝置註冊 — scan 掃到要排除, 只有明確要用「單一廣播」才註冊它。
_PCA_ALL_CALL = 0x70
# config address 清單中的魔法值: 自動掃描註冊匯流排上全部 PCA9685。
_PCA_AUTO_SCAN = 0xFF


def _make_controller(pca, item):
    """用 PCA9685 實體建立 PixelController (與串流渲染格式一致)。"""
    from lib.sw.PixelController import PixelController
    return PixelController("i2c_pixel", {
        "pixel_IO": pca,
        "Q": 16,
        "order": "W",
        "dStay": item.get("dStay", 0),
    })


def _register_pca(i2c, addr, item, pca_list):
    """建立單一 PCA9685(位址 addr)並加入 pca_list。回傳 True/False。

    每個位址各自一個 controller, 每幀 show() 對該位址個別寫入 64 bytes。
    掃到就註冊 (只接 PCA9685, 不需 probe 擋其他 I2C 裝置)。
    """
    try:
        pca = PCA9685(i2c, address=addr)
        pca.freq(1000)
    except Exception as e:
        get_log().error("PCA9685@{} init error: {}".format(hex(addr), e))
        return False
    pca_list.append(_make_controller(pca, item))
    return True


def _scan_and_register(i2c, item, pca_list):
    """0xFF: 掃描匯流排, 逐個真實位址各建一個 controller (排除 0x70)。

    每個掃到的位址一個 controller, 每幀 show() 對該位址個別寫入相同內容,
    對所有板子送出相同 16 通道 (12-bit) 資料。這是「對所有板子下同一道命令」
    最可靠的做法: 每個位址有 ACK、保證送達, 不依賴 ALLCALL 廣播。

    不採用 0x70 ALLCALL 廣播的原因: 廣播要能生效, 每顆晶片的 ALLCALL 位元
    (MODE1 bit0) 都必須是 1。此位元上電預設 1, 但只要先前任何一次開機流程
    對晶片寫過 MODE1=0x00/0x10 (例如舊版 setup()), 又沒斷電重啟, ALLCALL 就
    會被關掉 → 0x70 不再 ACK (ENODEV), 廣播靜默失效。逐位址寫不受此影響。
    """
    try:
        found = [a for a in i2c.scan() if a != _PCA_ALL_CALL]
    except Exception as e:
        get_log().error("PCA9685 scan error: {}".format(e))
        return
    get_log().info("I2C Scan (excl 0x70): {}".format([hex(a) for a in found]))
    n_ok = 0
    for addr in found:
        if _register_pca(i2c, addr, item, pca_list):
            n_ok += 1
    get_log().info("PCA9685: registered {} via scan".format(n_ok))


def init_pca9685(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("PCA9685") or {}
    if not cfg.get("enable"):
        return []

    from lib.sw.PixelController import PixelController
    i2c_list = sysbus.get_service("i2c_list") or []
    pca_list = []
    for item in cfg.get("list", []):
        i2c_idx = item.get("GPIO", {}).get("i2c", 0)
        if i2c_idx < 0 or i2c_idx >= len(i2c_list):
            get_log().error("PCA9685: i2c index {} not found".format(i2c_idx))
            continue
        i2c = i2c_list[i2c_idx]
        addrs = item.get("address", [])
        if not addrs:
            # 無 address → 沿用舊 fallback: 掃描並排除 0x70
            try:
                addrs = [a for a in i2c.scan() if a != _PCA_ALL_CALL]
                get_log().info("I2C Scan: {}".format([hex(a) for a in addrs]))
            except Exception as e:
                get_log().error("PCA9685 scan error: {}".format(e))
                continue
        for addr in addrs:
            if isinstance(addr, str):
                addr = int(addr, 16)
            if addr == _PCA_AUTO_SCAN:
                _scan_and_register(i2c, item, pca_list)
            else:
                _register_pca(i2c, addr, item, pca_list)
    sysbus.register_service("pca9685_list", pca_list)
    get_log().info("PCA9685: {} device(s)".format(len(pca_list)))
    return pca_list


def gpios(sysbus=None):
    # PCA9685 走 I2C，無獨立 GPIO
    return {}
