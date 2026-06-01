#!/usr/bin/env python3
"""PC 端 managed area 工具 — 需 sudo (直接讀寫 raw sector)

用法:
  python3 managed_tool.py /dev/disk4 list
  python3 managed_tool.py /dev/disk4 export frame001.jpk /tmp/
  python3 managed_tool.py /dev/disk4 import /tmp/seq.bpk
  python3 managed_tool.py /dev/disk4 trim frame001.jpk
"""

import json, os, sys, struct, tempfile, subprocess, shutil

SECTOR = 512

def _mount(dev):
    r = subprocess.run(["diskutil","info",dev], capture_output=True, text=True)
    for l in r.stdout.split("\n"):
        if "Mount Point" in l:
            m = l.split(":")[-1].strip()
            if m: return m
    return None

def _read_sectors(dev, start, count):
    """讀取 raw sector"""
    with open(dev, "rb") as f:
        f.seek(start * SECTOR)
        return f.read(count * SECTOR)

def _write_sectors(dev, start, data):
    """寫入 raw sector (長度自動對齊 sector)"""
    with open(dev, "wb") as f:
        f.seek(start * SECTOR)
        f.write(data)

def load_alloc(dev, mount):
    ap = os.path.join(mount, "alloc.json") if mount else None
    if ap and os.path.exists(ap):
        with open(ap) as f: return json.load(f)
    # 直接從 raw sector 讀 alloc.json
    # 先掛載 temp 以讀取
    d = os.path.dirname(dev)
    b = os.path.basename(dev)
    try:
        subprocess.run(["diskutil","mount",dev], capture_output=True)
        mount = _mount(dev)
        if mount:
            with open(os.path.join(mount,"alloc.json")) as f: r = json.load(f)
            subprocess.run(["diskutil","unmountDisk",dev], capture_output=True)
            return r
    except: pass
    return {"_offset": 65536, "_total_sectors": 0}

def list_files(dev, alloc):
    mount = _mount(dev)
    a = load_alloc(dev, mount)
    off = a.get("_offset", 65536)

    # 從 raw sector 讀 alloc.json 內的 entries
    # 配置檔本身在 FAT 區, 已用 load_alloc 讀取
    # managed area 檔案從 raw sector 讀取
    # 目前只支援 alloc 內的檔案

def main():
    if len(sys.argv) < 3:
        print(__doc__); return

    dev = sys.argv[1]
    cmd = sys.argv[2]

    if not os.path.exists(dev):
        print("找不到:", dev); return

    # 卸載 (才能 raw 讀寫)
    print("卸載...")
    subprocess.run(["diskutil","unmountDisk",dev], capture_output=True)

    # 讀 alloc.json
    mount = _mount(dev)  # 卸載後 = None
    alloc = {}
    # alloc.json 在 raw sector 上有目錄項目
    # 暫時手動指定
    off = 65536  # 預設

    print("alloc 預設 offset:", off)

    # 簡單測試: 讀取第一個 sector
    data = _read_sectors(dev, 0, 1)
    print("Sector 0:", data[:16].hex())

    print("重新掛載...")
    subprocess.run(["diskutil","mountDisk",dev], capture_output=True)

if __name__ == "__main__":
    main()
