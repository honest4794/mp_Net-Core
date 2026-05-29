"""
SDMMC 1-wire 測試 — 官方 V2 腳位
  CLK=9, CMD=42, D0=8

完全獨立於 LCD QSPI (SPI2, sck=47, data=18,7,48,5)
兩者同時運作，無須 deinit/reinit
"""

import machine, os, time

# ── 設定參數 ──
SLOT   = 1          # SDMMC slot (0/1 for SDIO, >=2 for SPI)
WIDTH  = 1          # 1-wire mode
SCK    = 9
CMD    = 42
DATA   = [8]        # 只有 D0
FREQ   = 20_000_000 # 20MHz 保守起見
MP     = "/sd"      # mount point

def test_sdmmc():
    print("\n=== SDMMC 1-wire Test ===")
    print(f"  slot={SLOT}, width={WIDTH}")
    print(f"  sck={SCK}, cmd={CMD}, data={DATA}")
    print(f"  freq={FREQ/1e6:.0f}MHz")
    print()

    # 1. 初始化 SDMMC
    print("[1/4] Initializing SDCard in SDMMC mode...")
    try:
        sd = machine.SDCard(
            slot=SLOT,
            width=WIDTH,
            sck=SCK,
            cmd=CMD,
            data=DATA,
            freq=FREQ,
        )
        print("  ✅ SDCard object created")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    # 2. 掛載
    print("[2/4] Mounting to", MP, "...")
    try:
        # 先確認沒掛過
        try:
            os.umount(MP)
        except OSError:
            pass
        os.mount(sd, MP)
        print("  ✅ Mounted successfully")
    except Exception as e:
        print(f"  ❌ Mount failed: {e}")
        return False

    # 3. 檢查檔案系統
    print("[3/4] Checking filesystem...")
    try:
        files = os.listdir(MP)
        print(f"  ✅ {len(files)} entries found:")
        for f in files:
            try:
                st = os.stat(MP + "/" + f)
                size = st[6]
                print(f"    {'📄' if st[0] & 0x8000 else '📁'} {f}  ({size} bytes)" if st[0] & 0x8000 else f"    {'📁'} {f}/")
            except:
                print(f"    {f}")
    except Exception as e:
        print(f"  ❌ List failed: {e}")

    # 4. 卸載
    print("[4/4] Unmounting...")
    try:
        os.umount(MP)
        print("  ✅ Unmounted cleanly")
    except Exception as e:
        print(f"  ⚠️  Umount warning: {e}")

    print()
    print("=== Test Complete ===")
    return True


# ── 如果直接執行 ──
if __name__ == "__main__":
    test_sdmmc()
