#!/usr/bin/env python3
"""SD raw sector 驗證腳本 — 讀取 alloc.json 指定 sector 並校驗 SHA256"""

import os, sys, json, hashlib, ctypes
from ctypes import wintypes

S = 512

def _win_k():
    k = ctypes.windll.kernel32
    k.CreateFileW.restype = wintypes.HANDLE
    k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k.SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]
    k.ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k

def read_sectors(disk_number, start_sector, count):
    """讀取 raw sectors，返回 bytes"""
    k = _win_k()
    GENERIC_READ = 0x80000000
    FILE_SHARE_RW = 0x1 | 0x2
    OPEN_EXISTING = 3
    h = k.CreateFileW(
        "\\\\.\\PhysicalDrive{}".format(disk_number),
        GENERIC_READ, FILE_SHARE_RW, None, OPEN_EXISTING, 0, None
    )
    INVALID = ctypes.c_void_p(-1).value
    if not h or h == INVALID:
        raise OSError("無法開啟磁碟 PhysicalDrive{}".format(disk_number))

    try:
        pos = ctypes.c_longlong(start_sector * S)
        newpos = ctypes.c_longlong(0)
        k.SetFilePointerEx(h, pos, ctypes.byref(newpos), 0)

        total_bytes = count * S
        outbuf = ctypes.create_string_buffer(total_bytes)
        done = wintypes.DWORD(0)
        k.ReadFile(h, outbuf, total_bytes, ctypes.byref(done), None)
        return outbuf.raw[:done.value]
    finally:
        k.CloseHandle(h)

def scan():
    import subprocess as SP, re
    r = SP.run(["powershell", "-NoProfile", "-Command",
        'Get-Disk | ForEach-Object { $n=$_.Number; $s=$_.Size; $b=$_.BusType; $v=Get-Partition -DiskNumber $n -ErrorAction SilentlyContinue | Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter } | Select-Object -First 1; if ($v) { "$n,$s,$b,$($v.DriveLetter): $($v.FileSystemLabel)" } else { "$n,$s,$b," } }'],
        capture_output=True, text=True)
    disks = []
    for line in r.stdout.strip().split("\n"):
        line = line.strip()
        p = line.split(",")
        if len(p) >= 3:
            try: sz = int(p[1])
            except: continue
            bus = p[2].strip()
            if bus != "USB": continue
            label = p[3].strip() if len(p) >= 4 and p[3].strip() else ""
            if sz >= 512 * 1024 * 1024:
                disks.append((int(p[0]), sz, label))
    return disks

def main():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_verify_log.txt")
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("SD Raw Sector 驗證工具\n\n")

        disks = scan()
        if not disks:
            log.write("❌ 找不到 USB 磁碟\n")
            return

        for i, (n, sz, lb) in enumerate(disks):
            info = "  ({:.1f}GB)".format(sz / 1073741824)
            label = lb if lb else "PhysicalDrive{}".format(n)
            log.write(" {}. {}{}\n".format(i + 1, label, info))

        if len(disks) == 1:
            sel = "1"
        else:
            return
        disk_number = disks[int(sel) - 1][0]

        alloc_path = None
        for l in "DEFGHIJKLMNOPQRSTUVWXYZ":
            ap = l + ":/alloc.json"
            if os.path.exists(ap):
                alloc_path = ap
                break

        if not alloc_path:
            log.write("❌ 找不到 alloc.json\n")
            return

        with open(alloc_path, "r") as f:
            alloc = json.load(f)

        offset = alloc.get("_offset", 0)
        total = alloc.get("_total_sectors", 0)
        log.write("_offset: {} sectors ({} MB)\n".format(offset, offset * S / 1048576))
        log.write("_total_sectors: {} ({} GB)\n".format(total, total * S / 1073741824))
        log.write("=" * 70 + "\n")

        ok_count = 0
        fail_count = 0
        for name, entry in sorted(alloc.items(), key=lambda x: x[1][0] if isinstance(x[1], list) else 0):
            if name.startswith("_"):
                continue
            start_sec = entry[0]
            cnt = entry[1]
            expected_sha = entry[2] if len(entry) >= 3 else None
            size_bytes = cnt * S

            log.write("\n{}  sector: {}  count: {}  size: {:.1f} MB\n".format(
                name, start_sec, cnt, size_bytes / 1048576))
            log.write("  expected SHA256: {}\n".format(expected_sha))

            try:
                raw = read_sectors(disk_number, start_sec, cnt)
                hex_preview = raw[:64].hex()
                log.write("  first 64B: {}\n".format(hex_preview))

                all_ff = all(b == 0xFF for b in raw)
                all_zero = all(b == 0x00 for b in raw)
                if all_ff:
                    log.write("  ⚠️  sector 內容全為 0xFF (未寫入 / erase 狀態)\n")
                if all_zero:
                    log.write("  ⚠️  sector 內容全為 0x00\n")

                if expected_sha:
                    h = hashlib.sha256(raw).hexdigest()
                    if h == expected_sha:
                        log.write("  ✅ SHA256 匹配\n")
                        ok_count += 1
                    else:
                        log.write("  ❌ SHA256 不匹配!\n")
                        log.write("     expected: {}\n".format(expected_sha))
                        log.write("     got:      {}\n".format(h))
                        fail_count += 1
            except Exception as e:
                log.write("  ❌ 讀取失敗: {}\n".format(e))

        log.write("\n" + "=" * 70 + "\n")
        log.write("結果: {} 通過, {} 失敗\n".format(ok_count, fail_count))

    print("✅ 驗證完成，結果寫入: {}".format(log_path))


if __name__ == "__main__":
    main()
