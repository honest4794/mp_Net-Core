#!/usr/bin/env python3
"""SD 卡工具 — 格式化 + 劃 managed area

用法:
  python3 sdcard_tool.py                        # 預設 FAT 32MB
  python3 sdcard_tool.py --offset 500000        # 自訂起始 sector
  python3 sdcard_tool.py --fat 64               # FAT 64MB
"""

import argparse, subprocess, sys, os, json, re, time

def _run(cmd, q=True):
    if not q: print("  $ "+" ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True)

def _scan():
    r = _run(["diskutil","list","external","physical"])
    out = []
    for d in re.findall(r"^(/dev/disk\d+)", r.stdout, re.M):
        info = _run(["diskutil","info",d]).stdout
        m = re.search(r"\((\d+)\s*Bytes?\)", info)
        if m:
            cap = int(m.group(1))
            if cap >= 512*1024*1024: out.append((d, cap))
    return out

def _mount(dev, label):
    for part in [dev+"s1",dev+"s2"]:
        for _ in range(15):
            time.sleep(0.3)
            r = _run(["diskutil","info",part])
            if r.returncode==0:
                m = re.search(r"Mount Point:\s+(.+)", r.stdout)
                if m: return m.group(1).strip()
    r = _run(["ls","/Volumes"])
    for v in r.stdout.strip().split("\n"):
        if v==label or v.startswith(label): return "/Volumes/"+v
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("device", nargs="?")
    p.add_argument("--offset", type=int, default=None, help="managed 起始 sector")
    p.add_argument("--fat", type=int, default=32, help="FAT 保留 MB")
    p.add_argument("--cluster", default="8K", help="Cluster 4K/8K/16K/32K/64K")
    p.add_argument("--label", default="SDCARD")
    a = p.parse_args()

    # 選裝置
    if a.device: dev = a.device
    else:
        print("🔍 掃描...")
        disks = _scan()
        if not disks: print("❌ 找不到 SD 卡"); return
        for i,(d,c) in enumerate(disks):
            print("  {}. {}  ({:.1f}GB)".format(i+1,d,c/1073741824))
        n = int(input("選擇: "))
        dev = disks[n-1][0]

    # 資訊
    info = _run(["diskutil","info",dev]).stdout
    cap = int(re.search(r"\((\d+)\s*Bytes?\)", info).group(1))
    total_sec = cap // 512
    off = a.offset if a.offset else None

    if off is None:
        print("FAT 空間建議 16~64MB (預設 32, 輸入 0=不要 managed)")
        fat_mb = input("FAT MB [32]: ").strip()
        if fat_mb == "": fat_mb = "32"
        fat_mb = int(fat_mb)
        if fat_mb <= 0:
            print("整張卡當 FAT, 不劃 managed area")
            _run(["diskutil","unmountDisk",dev])
            _run(["diskutil","partitionDisk",dev,"1","GPT","FAT32",a.label,"100%"])
            print("✅ 完成 (無 managed)"); return
        off = fat_mb * 1048576 // 512

    print("  容量: {:.1f}GB".format(cap/1073741824))
    print("  offset: sector {}  FAT: {}MB  managed: ~{:.1f}GB".format(off, off*512//1048576, (total_sec-off)*512/1073741824))

    c = input("⚠️ 確認格式化? (yes/no): ")
    if c.lower() not in ("yes","y"): print("取消"); return

    # 格式化
    _run(["diskutil","unmountDisk",dev])
    r = _run(["diskutil","partitionDisk",dev,"1","GPT","FAT32",a.label,"100%"])
    if r.returncode: print("❌ 失敗"); return

    spc = {"4K":"8","8K":"16","16K":"32","32K":"64","64K":"128"}
    if a.cluster in spc:
        _run(["diskutil","unmountDisk",dev])
        _run(["newfs_msdos","-F","32","-b","512","-c",spc[a.cluster],"-v",a.label,dev+"s1"])

    print("  ✅ FAT32")
    mount = _mount(dev, a.label)

    a_obj = {"_version":1,"_offset":off,"_total_sectors":cap//512}
    if mount:
        with open(os.path.join(mount,"alloc.json"),"w") as f: json.dump(a_obj,f,indent=2)
        print("  ✅ /alloc.json (offset={})".format(off))
        _run(["diskutil","unmountDisk",dev])
    else:
        with open("_alloc.json","w") as f: json.dump(a_obj,f,indent=2)
        print("  ⚠️ 產出 _alloc.json")
    print("  ✅ 完成")

if __name__=="__main__":
    main()
