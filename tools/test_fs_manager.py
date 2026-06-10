# -*- coding: utf-8 -*-
"""fs_manager 互動式讀寫測速

列出 SD 卡上的所有檔案，選擇後透過 fs_manager 讀取/寫入並測速。

用法:
  import test_fs_manager
  test_fs_manager.run()
"""

import gc, time, os
from lib.sys_bus import bus

PROGRESS_EVERY_BYTES = 1048576      # 每 1 MB 印一次進度


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


def _scan_files(fs):
    """掃描所有可用檔案 (FAT + raw + RAM)"""
    files = []

    # ── FAT 檔案 ──
    try:
        for name in os.listdir("/sd"):
            full = "/sd/" + name
            try:
                st = os.stat(full)
                if (st[0] & 0x4000) == 0:
                    if name in ("alloc.json", "manifest.json", "config.json"):
                        continue
                    files.append(("[FAT] " + name, full, st[6], "fat"))
            except Exception:
                pass
    except Exception:
        pass

    # ── SD-raw 檔案 ──
    try:
        if fs._raw_mode and fs._raw is not None:
            raw_files = fs._raw.list_files()
            for name, info in raw_files.items():
                files.append(("[RAW] " + name, "/sd/" + name, info["bytes"], "raw"))
    except Exception:
        pass

    # ── RAM 檔案 ──
    try:
        ram_files = fs.list("/ram")
        for f in ram_files:
            data = fs.read(f)
            if data is not None:
                files.append(("[RAM] " + f, f, len(data), "ram"))
    except Exception:
        pass

    return files


def _stream_read(fs, path, file_size):
    """透過 fs_manager 串流讀取完整檔案，附進度"""
    size = fs.begin_read(path)
    if size <= 0:
        print("  ❌ fs.begin_read 失敗")
        return 0, 0

    buf = bytearray(16384)
    gc.collect()
    t0 = time.ticks_ms()
    total = 0
    next_progress = PROGRESS_EVERY_BYTES
    while True:
        n = fs.read_into(buf)
        if n <= 0:
            break
        total += n
        if total >= next_progress:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed > 0:
                pct = total * 100 // file_size if file_size else 100
                print("  ... {:.0f}%  ({})  {:.1f} MB/s".format(
                    pct, _fmt_bytes(total), _mb_s(total, elapsed)))
            next_progress += PROGRESS_EVERY_BYTES
            if next_progress % (8 * PROGRESS_EVERY_BYTES) == 0:
                gc.collect()

    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    fs.end_read()
    return total, elapsed


def _demo_seek(fs, path, file_size):
    """示範 seek / tell 後讀取一小段資料"""
    if file_size < 2048:
        return

    size = fs.begin_read(path)
    if size <= 0:
        return

    mid = file_size // 2
    fs.seek(mid)
    pos = fs.tell()
    buf = bytearray(64)
    n = fs.read_into(buf)
    fs.end_read()

    if n > 0:
        print("  🔍 seek → {} (tell={}) → read_into {} bytes: {}".format(
            _fmt_bytes(mid), pos, n, buf[:min(n, 24)].hex()))


def _stream_write(fs, path, total_bytes):
    """透過 fs_manager 串流寫入，附進度"""
    ok = fs.begin_write(path, total_bytes)
    if not ok:
        print("  ❌ fs.begin_write 失敗")
        return 0, 0

    buf = bytearray(16384)
    gc.collect()
    t0 = time.ticks_ms()
    written = 0
    next_progress = PROGRESS_EVERY_BYTES
    while written < total_bytes:
        n = min(len(buf), total_bytes - written)
        fs.write(buf[:n])
        written += n
        if written >= next_progress:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed > 0:
                pct = written * 100 // total_bytes
                print("  ... {:.0f}%  ({})  {:.1f} MB/s".format(
                    pct, _fmt_bytes(written), _mb_s(written, elapsed)))
            next_progress += PROGRESS_EVERY_BYTES
            if next_progress % (8 * PROGRESS_EVERY_BYTES) == 0:
                gc.collect()

    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    ok = fs.end_write()
    if not ok:
        print("  ❌ end_write 失敗 (SHA256 不符或寫入錯誤)")
        return written, elapsed
    return written, elapsed


def run():
    print("\n" + "=" * 58)
    print("  fs_manager 互動式讀寫測速")
    print("=" * 58)

    from lib.fs_manager import fs

    print("  模式:", "⚡ SD-raw (高速)" if fs._raw_mode else "📂 FAT")

    sd = bus.get_service("sd_raw")
    if sd is None:
        print("❌ SD 卡不可用")
        return

    files = _scan_files(fs)
    if not files:
        print("❌ 沒有可測試的檔案")
        return

    files.sort(key=lambda x: x[2], reverse=True)

    print("\n  {:>4s}  {:>28s}  {:>10s}  {}".format("#", "name", "size", "layer"))
    print("  " + "-" * 56)
    for i, (label, path, size, kind) in enumerate(files):
        name = label[6:]
        print("  {:>4d}  {:>28s}  {:>10s}  {}".format(i + 1, name[:28], _fmt_bytes(size), label[:5]))
    print("  " + "-" * 56)

    while True:
        try:
            sel = input("\n選擇 (n=編號讀取, w=寫入測速, q=離開): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if sel.lower() in ("q", "quit", "exit", ""):
            break

        # ── 寫入測速 ──
        if sel.lower() == "w":
            try:
                size_mb = input("  寫入大小 (MB, 預設 4): ").strip()
                size_mb = int(size_mb) if size_mb else 4
            except (ValueError, EOFError):
                size_mb = 4
            if size_mb <= 0 or size_mb > 256:
                print("  範圍 1-256 MB")
                continue

            total_bytes = size_mb * 1024 * 1024
            wpath = "/sd/_fs_write_test.bin"
            print("\n  寫入: {}  ({})".format(wpath, _fmt_bytes(total_bytes)))

            written, elapsed = _stream_write(fs, wpath, total_bytes)
            if written == 0:
                continue

            speed = _mb_s(written, elapsed)
            bar = "  ████████" if speed >= 4 else "  ████" if speed >= 1 else ""
            print("  ✅ {}  |  {} ms  |  {:.2f} MB/s{}  [via {}]".format(
                _fmt_bytes(written), elapsed, speed, bar,
                "RAW" if fs._raw_mode else "FAT"))

            # 清理
            gc.collect()
            try:
                fs.remove(wpath)
            except Exception:
                pass
            # 刷新檔案列表
            files = _scan_files(fs)
            files.sort(key=lambda x: x[2], reverse=True)
            print("\n  {:>4s}  {:>28s}  {:>10s}  {}".format("#", "name", "size", "layer"))
            print("  " + "-" * 56)
            for i, (label, path, size, kind) in enumerate(files):
                name = label[6:]
                print("  {:>4d}  {:>28s}  {:>10s}  {}".format(i + 1, name[:28], _fmt_bytes(size), label[:5]))
            print("  " + "-" * 56)
            continue

        # ── 讀取測速 ──
        try:
            idx = int(sel) - 1
        except ValueError:
            print("  請輸入數字 或 w/q")
            continue

        if idx < 0 or idx >= len(files):
            print("  編號超出範圍 (1-{})".format(len(files)))
            continue

        label, path, size_bytes, kind = files[idx]

        print("\n  讀取: {}  ({})  [{}]".format(path, _fmt_bytes(size_bytes), kind))

        total, elapsed = _stream_read(fs, path, size_bytes)

        if total == 0:
            print("  ❌ 讀取失敗")
            continue

        speed = _mb_s(total, elapsed)
        bar = ""
        if speed >= 8:
            bar = "  ████████"
        elif speed >= 6:
            bar = "  ██████"
        elif speed >= 4:
            bar = "  ████"
        elif speed >= 2:
            bar = "  ██"

        print("  ✅ {}  |  {} ms  |  {:.2f} MB/s{}  [via {}]".format(
            _fmt_bytes(total), elapsed, speed, bar, kind.upper()))

        if size_bytes >= 2048:
            gc.collect()
            _demo_seek(fs, path, size_bytes)

        gc.collect()

    print("  結束。")


if __name__ == "__mp_main__":
    run()
