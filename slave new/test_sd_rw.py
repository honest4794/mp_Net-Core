"""
SDMMC 1-wire 檔案讀寫測試
掛載 /sd 後寫入一個檔案再讀回來驗證
"""

import machine, os, time

SLOT   = 1
WIDTH  = 1
SCK    = 9
CMD    = 42
DATA   = [8]
FREQ   = 20_000_000
MP     = "/sd"

def test_rw():
    print("=== SDMMC 1-wire 讀寫測試 ===\n")

    # ── 掛載 ──
    print("[掛載] Mounting /sd ...")
    try:
        os.umount(MP)
    except:
        pass
    try:
        sd = machine.SDCard(slot=SLOT, width=WIDTH, sck=SCK, cmd=CMD, data=DATA, freq=FREQ)
        os.mount(sd, MP)
        print("  ✅ /sd 已掛載")
    except Exception as e:
        print(f"  ❌ 掛載失敗: {e}")
        return

    # ── 列根目錄 ──
    print("\n[列表] /sd 內容:")
    for f in os.listdir(MP):
        print(f"    {f}")

    # ── 寫入測試 ──
    print("\n[寫入] test_hello.txt ...")
    test_content = f"Hello from ESP32-S3! Timestamp: {time.ticks_ms()}\n"
    try:
        with open(MP + "/test_hello.txt", "w") as f:
            f.write(test_content)
        print("  ✅ 寫入完成")
    except Exception as e:
        print(f"  ❌ 寫入失敗: {e}")
        os.umount(MP)
        return

    # ── 驗證內容 ──
    print("\n[驗證] 讀回 test_hello.txt ...")
    try:
        with open(MP + "/test_hello.txt", "r") as f:
            data = f.read()
        print(f"  📄 內容: {repr(data)}")
        if data == test_content:
            print("  ✅ 內容一致，讀寫正確")
        else:
            print("  ⚠️ 內容不一致!")
            print(f"     期望: {repr(test_content)}")
            print(f"     收到: {repr(data)}")
    except Exception as e:
        print(f"  ❌ 讀取失敗: {e}")
        os.umount(MP)
        return

    # ── 刪除測試檔 ──
    print("\n[清理] 刪除 test_hello.txt ...")
    try:
        os.remove(MP + "/test_hello.txt")
        print("  ✅ 已刪除")
    except Exception as e:
        print(f"  ⚠️  刪除失敗: {e}")

    # ── 卸載 ──
    print("\n[卸載] ...")
    try:
        os.umount(MP)
        print("  ✅ 卸載完成")
    except Exception as e:
        print(f"  ⚠️  卸載失敗: {e}")

    print("\n=== 測試結束 ===")

if __name__ == "__main__":
    test_rw()
