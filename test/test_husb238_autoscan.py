"""
test_husb238_autoscan.py — HUSB238 全自動偵測腳本
用途: 不確定 HUSB238 接在哪組腳、哪個位址時，自動掃描並辨識。

直接在 REPL 執行:
    import test_husb238_autoscan
    test_husb238_autoscan.run()

或從檔案執行:
    exec(open("test_husb238_autoscan.py").read())
"""

import machine
import time


# ════════════════════════════════════════════════════════
# 配置: 要嘗試的 I2C 腳位組合
# 每組: (scl_pin, sda_pin, 描述)
# ════════════════════════════════════════════════════════
PIN_COMBOS = [
    # 你原本 config 裡的 37/38
#     (38, 37, "SCL=38 SDA=37 (config)"),
    # 反轉: SCL/SDA 交換
#     (37, 38, "SCL=37 SDA=38 (反轉)"),
    # boot log 顯示的 7/8
    (8, 7, "SCL=8 SDA=7 (boot log)"),
    # 反轉
    (7, 8, "SCL=7 SDA=8 (反轉)"),
    # 其他常見的 I2C 腳位 (依你的板子調整)
    # (22, 21, "SCL=22 SDA=21"),
    # (21, 22, "SCL=21 SDA=22 (反轉)"),
]

# HUSB238 官方預設位址
HUSB238_ADDR_DEFAULT = 0x08


def probe_husb238(i2c, addr):
    """
    對指定位址讀取 HUSB238 暫存器，回傳 (score, info_dict)。
    score 越高越可能是 HUSB238。
    """
    score = 0
    info = {"addr": addr, "regs": {}, "notes": []}

    try:
        # 讀取 0x00~0x09
        regs = {}
        for r in range(0x00, 0x0A):
            try:
                val = i2c.readfrom_mem(addr, r, 1)[0]
                regs[r] = val
            except Exception:
                regs[r] = None
        info["regs"] = regs

        # ── 特徵 1: 位址是否为 0x08 ──
        if addr == HUSB238_ADDR_DEFAULT:
            score += 3
            info["notes"].append("位址=0x08 (官方預設)")

        # ── 特徵 2: GO_CMD 寫入後是否讀回 ──
        # 寫 reset 命令 (0b10000 = 0x10) 到 reg 0x09
        try:
            i2c.writeto_mem(addr, 0x09, b'\x10')
            time.sleep_ms(50)
            go_cmd = i2c.readfrom_mem(addr, 0x09, 1)[0]
            info["go_cmd_after_write"] = go_cmd
            # HUSB238 的 GO_CMD 寫入後可能讀回 0x10 或 0x00
            # 如果讀回 0x10，代表暫存器可寫可讀 (像 HUSB238)
            if go_cmd == 0x10:
                score += 1
                info["notes"].append("GO_CMD 可寫可讀")
            elif go_cmd == 0x00:
                # 命令已執行並清除，也可能是 HUSB238
                score += 1
                info["notes"].append("GO_CMD 寫後歸零 (命令已執行)")
        except Exception as e:
            info["notes"].append("GO_CMD 寫入失敗: {}".format(e))

        # ── 特徵 3: PD_STATUS1 (0x01) 是否可讀 ──
        if regs.get(0x01) is not None:
            score += 1
            info["notes"].append("PD_STATUS1 可讀")
            # 檢查 bit6 (attached)
            attached = bool(regs[0x01] & 0x40)
            info["attached"] = attached
            if attached:
                score += 5
                info["notes"].append("已 ATTACHED!")

        # ── 特徵 4: PD_STATUS0 (0x00) 是否可讀 ──
        if regs.get(0x00) is not None:
            score += 1
            info["notes"].append("PD_STATUS0 可讀")

        # ── 特徵 5: PDO 暫存器 (0x02~0x07) 是否可讀 ──
        pdo_readable = sum(1 for r in range(0x02, 0x08) if regs.get(r) is not None)
        if pdo_readable >= 4:
            score += 1
            info["notes"].append("PDO 暫存器大多可讀 ({}/6)".format(pdo_readable))

    except Exception as e:
        info["notes"].append("探測異常: {}".format(e))

    return score, info


def scan_i2c(i2c):
    """掃描 I2C bus，回傳找到的位址列表"""
    try:
        return i2c.scan()
    except Exception as e:
        print("  掃描失敗: {}".format(e))
        return []


def try_pin_combo(scl, sda, desc):
    """嘗試一組腳位，回傳 (i2c_obj, found_addrs) 或 (None, [])"""
    print("\n" + "=" * 60)
    print("嘗試: {} (SCL={} SDA={})".format(desc, scl, sda))
    print("=" * 60)

    try:
        i2c = machine.I2C(0, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=400000)
    except Exception as e:
        print("  I2C 初始化失敗: {}".format(e))
        return None, []

    addrs = scan_i2c(i2c)
    if not addrs:
        print("  沒找到任何 I2C 設備")
        return i2c, []

    print("  找到 {} 個設備: {}".format(
        len(addrs), [hex(a) for a in addrs]))
    return i2c, addrs


def run(pin_combos=None):
    """主函數: 自動掃描所有腳位組合並辨識 HUSB238"""
    if pin_combos is None:
        pin_combos = PIN_COMBOS

    print("\n" + "=" * 60)
    print("HUSB238 全自動偵測")
    print("=" * 60)

    best_results = []

    for scl, sda, desc in pin_combos:
        i2c, addrs = try_pin_combo(scl, sda, desc)
        if i2c is None or not addrs:
            continue

        # 對每個找到的位址探測 HUSB238 特徵
        for addr in addrs:
            score, info = probe_husb238(i2c, addr)
            info["pins"] = desc
            info["scl"] = scl
            info["sda"] = sda
            best_results.append((score, info))

            # 印出暫存器 dump
            print("\n  ── 位址 0x{:02X} ──".format(addr))
            print("  分數: {} (越高越可能是 HUSB238)".format(score))
            for r in range(0x00, 0x0A):
                v = info["regs"].get(r)
                if v is not None:
                    print("    reg 0x{:02X} = 0x{:02X} (0b{:08b})".format(r, v, v))
                else:
                    print("    reg 0x{:02X} = ERR".format(r))
            if info["notes"]:
                print("  備註:")
                for n in info["notes"]:
                    print("    - {}".format(n))

    # ── 總結 ──
    print("\n" + "=" * 60)
    print("偵測結果總結")
    print("=" * 60)

    if not best_results:
        print("所有腳位組合都找不到 I2C 設備。")
        print("請檢查接線、上拉電阻、供電。")
        return None

    # 按分數排序
    best_results.sort(key=lambda x: x[0], reverse=True)

    print("\n按可能性排序:")
    for rank, (score, info) in enumerate(best_results[:5], 1):
        attached = info.get("attached", False)
        status = "ATTACHED" if attached else "not attached"
        print("  {}. 位址=0x{:02X} 分數={} [{}] 腳位={}".format(
            rank, info["addr"], score, status, info["pins"]))

    # 最佳候選
    best_score, best_info = best_results[0]
    print("\n最佳候選: 位址=0x{:02X} (分數={})".format(
        best_info["addr"], best_score))
    print("  腳位: SCL={} SDA={}".format(best_info["scl"], best_info["sda"]))
    print("  Attached: {}".format(best_info.get("attached", False)))

    if best_score >= 5:
        print("\n✓ 高機率找到 HUSB238!")
        print("  建議在 config.json 設定:")
        print('    "I2C": {{"enable":1, "list":[{{"id":0,"freq":400000,')
        print('       "GPIO":{{"scl":{},"sda":{}}}}}]}}'.format(
            best_info["scl"], best_info["sda"]))
        print('    "HUSB238": {{"enable":1, "addr":"0x{:02X}", "GPIO":{{"i2c":0}}}}'.format(
            best_info["addr"]))
    elif best_score >= 2:
        print("\n? 可能是 HUSB238，但信心不高。")
        print("  建議: 確認 USB-C 線接好 PD 充電器，再跑一次。")
    else:
        print("\n✗ 找到的設備不太像 HUSB238。")
        print("  可能原因: HUSB238 沒接好、不在這些腳位上、或根本沒供電。")

    return best_results


# ════════════════════════════════════════════════════════
# 單獨執行時自動跑
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    run()
