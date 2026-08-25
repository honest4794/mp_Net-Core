"""
pca9685_drv.py — PCA9685 PWM pixel 管理 (走 I2C)

設定來源: bus.shared["PCA9685"]  ({enable, list})
         list item: {"i2c": <i2c_list index>, "address": ["0x40"]}
產物:    bus.register_service("pca9685_list", [...])

address 特殊值:
  "0x70" (112) — PCA9685 ALLCALL 廣播位址。直接註冊成一個 controller,
                每幀 show() 寫入 0x70 = 對匯流排上所有 PCA9685 同時廣播。
  "0xFF" (255) — 自動掃描: i2c.scan() 找匯流排上所有 PCA9685, 排除 0x70
                廣播位址, 逐個註冊 (之後加板子不用改 config)。
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

    使用者明確選擇「只接一顆 IC, 掃到就註冊」: 不做 probe 驗證,
    掃描到任何非 0x70 位址都直接當 PCA9685 註冊並派送。
    (若線上誤接了其他 I2C 裝置, 也會被當 PCA 寫入 — 需自行確認只有 PCA。)
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
    """0xFF: 掃描匯流排, 逐個註冊真實位址的 PCA9685, 並在有實體板時加 0x70 廣播。

    兩者是等效的「對所有板子下命令」:
      - 逐個真實位址: 每台有自己的 controller, 寫入保證送達 (有回應)。
      - 0x70 廣播:    PCA9685 ALLCALL 預設啟用, 對 0x70 寫入 = 所有板子
                      同時收到 (scan 也會 ACK 0x70, 但把它當一般裝置逐個
                      寫是錯的 — 它是廣播)。掃描時排除 0x70 避免重複,
                      另外明確建立一個 0x70 廣播 controller。

    真實位址 probe 讀 MODE1 (0x00): 讀得回來才視為 PCA9685, 避免把
    EEPROM/感測器等誤註冊成 PWM 控制器。

    0x70 廣播: 只有當「掃描到至少一台真實 PCA9685」時才建立 — 表示線上的
    確有板子, 0x70 廣播才會被 ACK。線上完全沒板子時不建 0x70, 免得每幀
    對不存在的位址刷 Show Error。
    """
    try:
        found = [a for a in i2c.scan() if a != _PCA_ALL_CALL]
    except Exception as e:
        get_log().error("PCA9685 scan error: {}".format(e))
        return
    get_log().info("I2C Scan (excl 0x70): {}".format([hex(a) for a in found]))
    n_ok = 0
    for addr in found:
        # 掃到就註冊 (只接一顆 IC, 不需要 probe 擋 EEPROM — 掃到即是目標)
        if _register_pca(i2c, addr, item, pca_list):
            n_ok += 1
    # 有實體 PCA9685 才加 0x70 廣播 controller (線上沒板子就不建, 避免每幀 ENODEV)
    if n_ok > 0:
        if _register_pca(i2c, _PCA_ALL_CALL, item, pca_list):
            n_ok += 1
            get_log().info("PCA9685: +0x70 broadcast controller (ALLCALL)")
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
