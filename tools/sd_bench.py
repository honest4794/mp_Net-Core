# -*- coding: utf-8 -*-
"""SD 卡速度基準測試 (MicroPython / ESP32)

測試三條路徑的讀取速度：
  F1. FAT (os.open/readinto)     — 標準 MicroPython FAT
  F2. SD-raw (fast_io.Storage)   — 繞過 FAT，直接 sector 讀寫
  F3. fs_manager (自動降級鏈)    — 優先 SD-raw，失敗降級 FAT

用法:
  import sd_bench
  sd_bench.run()           # 完整測試矩陣
  sd_bench.run_quick()     # 快速測試 (只測默認 buffer)
"""

import gc, time, os
from lib.sys_bus import bus

# ── 測試參數 ──
TEST_SIZE = 4 * 1024 * 1024   # 4 MB 總讀取量 (可調整 2/4/8 MB)
BUF_SIZES = [512, 2048, 4096, 8192, 16384, 32768, 65536]
FAT_PATH = "/sd/_sd_bench_test.bin"
RAW_NAME = "_sd_bench_raw"


def _fmt_bytes(n):
    if n >= 1048576:
        return "{:.1f} MB".format(n / 1048576)
    if n >= 1024:
        return "{:.0f} KB".format(n / 1024)
    return "{} B".format(n)


def _mb_s(total_bytes, elapsed_ms):
    if elapsed_ms <= 0:
        elapsed_ms = 1
    return (total_bytes * 1000) / (elapsed_ms * 1048576)


def _ensure_test_file_fat(path, size):
    """建立 FAT 測試檔案 (如果不存在或大小不對)"""
    try:
        st = os.stat(path)
        if st[6] == size:
            return True
    except OSError:
        pass
    print("  建立 FAT 測試檔 {} ({})...".format(path, _fmt_bytes(size)))
    try:
        buf = bytearray(32768)
        with open(path, "wb") as f:
            written = 0
            while written < size:
                n = min(len(buf), size - written)
                f.write(buf[:n])
                written += n
        return True
    except Exception as e:
        print("  ⚠️ 建立 FAT 測試檔失敗:", e)
        return False


def _ensure_test_file_raw(storage, name, size):
    """建立 SD-raw 測試檔案"""
    existing = storage.list_files()
    if name in existing and existing[name]["bytes"] >= size:
        return True
    print("  建立 raw 測試檔 {} ({})...".format(name, _fmt_bytes(size)))
    try:
        buf = bytearray(32768)
        storage.write_begin(name, size)
        written = 0
        while written < size:
            n = min(len(buf), size - written)
            storage.write(buf[:n])
            written += n
        storage.write_end()
        return True
    except Exception as e:
        print("  ⚠️ 建立 raw 測試檔失敗:", e)
        return False


# ═══════════════════════════════════════════════════════════════
#  F1: FAT 讀取測試
# ═══════════════════════════════════════════════════════════════

def _fat_read_bench(path, buf_size, total_bytes):
    """FAT readinto 基準"""
    buf = bytearray(buf_size)
    gc.collect()
    t0 = time.ticks_ms()
    total = 0
    try:
        with open(path, "rb") as f:
            while total < total_bytes:
                n = f.readinto(buf)
                if n <= 0:
                    break
                total += n
    except Exception as e:
        print("    FAT read err:", e)
        return 0, 0
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    return total, elapsed


# ═══════════════════════════════════════════════════════════════
#  F2: SD-raw (fast_io.Storage) 讀取測試
# ═══════════════════════════════════════════════════════════════

def _raw_read_bench(storage, name, buf_size, total_bytes):
    """fast_io Storage read_into 基準"""
    buf = bytearray(buf_size)
    gc.collect()
    try:
        size = storage.read_begin(name)
    except Exception as e:
        print("    raw read_begin err:", e)
        return 0, 0
    t0 = time.ticks_ms()
    total = 0
    while total < total_bytes and total < size:
        n = storage.read_into(buf)
        if n <= 0:
            break
        total += n
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    storage.read_end()
    return total, elapsed


# ═══════════════════════════════════════════════════════════════
#  F3: fs_manager 統一讀取測試
# ═══════════════════════════════════════════════════════════════

def _fs_read_bench(fs, path, total_bytes):
    """fs_manager.read() 整個讀入 benchmark"""
    gc.collect()
    t0 = time.ticks_ms()
    try:
        data = fs.read(path)
    except Exception as e:
        print("    fs read err:", e)
        return 0, 0
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    total = len(data) if data else 0
    return total, elapsed


# ═══════════════════════════════════════════════════════════════
#  格式化輸出
# ═══════════════════════════════════════════════════════════════

def _print_header(title):
    print("\n" + "=" * 62)
    print("  {}  (total: {})".format(title, _fmt_bytes(TEST_SIZE)))
    print("=" * 62)
    print("  {:>12s}  {:>10s}  {:>10s}  {:>12s}".format(
        "buf_size", "bytes_read", "elapsed_ms", "MB/s"))
    print("  " + "-" * 58)


def _print_row(buf_size, total, elapsed, mb_s):
    bar = ""
    if mb_s >= 8:
        bar = "  ████████"
    elif mb_s >= 6:
        bar = "  ██████"
    elif mb_s >= 4:
        bar = "  ████"
    elif mb_s >= 2:
        bar = "  ██"
    print("  {:>8s}  {:>10s}  {:>8d} ms  {:>8.2f} MB/s{}".format(
        _fmt_bytes(buf_size), _fmt_bytes(total), elapsed, mb_s, bar))


# ═══════════════════════════════════════════════════════════════
#  主測試函數
# ═══════════════════════════════════════════════════════════════

def run(quick=False):
    """完整基準測試"""
    print("\n" + "╔" + "=" * 60 + "╗")
    print("║  SD Card Speed Benchmark — MicroPython FAT vs SD-raw  ║")
    print("╚" + "=" * 60 + "╝")

    # ── 檢查 SD 卡 ──
    sd = bus.get_service("sd_raw")
    if sd is None:
        print("\n❌ 無法存取 SD 卡 (sd_raw 未註冊到 bus)")
        return

    sector_size = sd.info()[1]
    total_sectors = sd.info()[0]
    cap_mb = (total_sectors * sector_size) // 1048576
    print("SD 卡: {} sectors × {}B = ~{} MB".format(total_sectors, sector_size, cap_mb))

    # ── 測試前檢查分配檔案 ──
    try:
        os.stat("/sd/alloc.json")
        print("alloc.json: 已存在")
    except OSError:
        print("alloc.json: 尚未建立 (將初始化)")

    # ── 初始化 Storage ──
    try:
        from lib.fast_io import Storage
        raw_storage = Storage()
        print("fast_io Storage: ✅ 就緒 (DMA buf: {} bytes)".format(raw_storage._buf_size))
    except Exception as e:
        print("fast_io Storage: ❌", e)
        raw_storage = None

    # ── 初始化 fs_manager ──
    try:
        from lib.fs_manager import fs
        print("fs_manager: ✅ 就緒")
    except Exception as e:
        print("fs_manager: ❌", e)
        fs = None

    # ── 準備測試檔案 ──
    print("\n── 準備測試檔案 ──")
    buf_sizes_test = BUF_SIZES if not quick else [16384, 32768]

    if not _ensure_test_file_fat(FAT_PATH, TEST_SIZE):
        print("❌ 無法建立 FAT 測試檔，跳過 FAT 測試")
    else:
        gc.collect()
        _print_header("F1: FAT (os.open/readinto)")
        for bs in buf_sizes_test:
            try:
                total, elapsed = _fat_read_bench(FAT_PATH, bs, TEST_SIZE)
            except MemoryError:
                total, elapsed = 0, 0
                print("  {:>8s}  (OOM)".format(_fmt_bytes(bs)))
                gc.collect()
                continue
            if total > 0:
                _print_row(bs, total, elapsed, _mb_s(total, elapsed))
            else:
                print("  {:>8s}  (read err)".format(_fmt_bytes(bs)))
            gc.collect()

    if raw_storage:
        gc.collect()
        if _ensure_test_file_raw(raw_storage, RAW_NAME, TEST_SIZE):
            _print_header("F2: SD-raw (fast_io.Storage / read_into)")
            for bs in buf_sizes_test:
                try:
                    total, elapsed = _raw_read_bench(raw_storage, RAW_NAME, bs, TEST_SIZE)
                except MemoryError:
                    total, elapsed = 0, 0
                    print("  {:>8s}  (OOM)".format(_fmt_bytes(bs)))
                    gc.collect()
                    continue
                if total > 0:
                    _print_row(bs, total, elapsed, _mb_s(total, elapsed))
                else:
                    print("  {:>8s}  (read err)".format(_fmt_bytes(bs)))
                gc.collect()

            # F2.5: read_all 測試
            gc.collect()
            try:
                t0 = time.ticks_ms()
                data = raw_storage.read_all(RAW_NAME)
                elapsed = time.ticks_diff(time.ticks_ms(), t0)
                if data:
                    print("\n  SD-raw read_all(): {} in {} ms → {:.2f} MB/s".format(
                        _fmt_bytes(len(data)), elapsed, _mb_s(len(data), elapsed)))
            except Exception as e:
                print("  SD-raw read_all err:", e)

    # F3: fs_manager 統一讀取 (raw 路徑)
    if fs and raw_storage:
        gc.collect()
        _print_header("F3: fs_manager.read() — SD-raw 路徑")
        try:
            # fs_manager 需要 /sd 前綴
            total, elapsed = _fs_read_bench(fs, "/sd/" + RAW_NAME, TEST_SIZE)
            if total > 0:
                _print_row(0, total, elapsed, _mb_s(total, elapsed))
        except Exception as e:
            print("  fs_manager raw err:", e)

    # F3b: fs_manager 讀 FAT 路徑
    if fs:
        gc.collect()
        _print_header("F3b: fs_manager.read() — FAT 路徑")
        try:
            total, elapsed = _fs_read_bench(fs, FAT_PATH, TEST_SIZE)
            if total > 0:
                _print_row(0, total, elapsed, _mb_s(total, elapsed))
        except Exception as e:
            print("  fs_manager fat err:", e)

    # ── 寫入速度快速測試 ──
    if raw_storage:
        gc.collect()
        print("\n── 寫入速度快速測試 (SD-raw, 1 MB) ──")
        wbuf = bytearray(32768)
        wsize = 1 * 1024 * 1024
        try:
            raw_storage.write_begin("_bench_tmp", wsize)
            t0 = time.ticks_ms()
            written = 0
            while written < wsize:
                n = min(len(wbuf), wsize - written)
                raw_storage.write(wbuf[:n])
                written += n
            raw_storage.write_end()
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            print("  寫入 {}: {} ms → {:.2f} MB/s".format(
                _fmt_bytes(wsize), elapsed, _mb_s(wsize, elapsed)))
            raw_storage.remove("_bench_tmp")
        except Exception as e:
            print("  寫入測試失敗:", e)

    # ── 記憶體狀態 ──
    gc.collect()
    print("\n── 記憶體 ──")
    print("  GC free: {} bytes".format(gc.mem_free()))
    print("  GC alloc: {} bytes".format(gc.mem_alloc()))

    print("\n" + "=" * 62)
    print("  測試完成。")

    # 清理
    try:
        os.remove(FAT_PATH)
    except Exception:
        pass


def run_quick():
    """快速測試: 只測最相關的 buffer 大小"""
    global TEST_SIZE
    TEST_SIZE = 2 * 1024 * 1024
    run(quick=True)


# 可直接 import 後呼叫 run() 或作為獨立腳本執行
if __name__ == "__mp_main__":
    run()
