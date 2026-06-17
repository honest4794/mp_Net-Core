#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SD 卡管理工具 (Mac / Windows)

用法: python3 storage_tool.py
"""

import subprocess as SP, os, sys, json, re, time, hashlib, platform, shutil, ctypes
S=512; OS=platform.system()

def I(msg,defv=""):
    """input: enter=預設, q=取消"""
    r=input(msg).strip()
    if r.lower() in ("q","cancel"): return None
    return r if r else defv

def R(c): return SP.run(c,capture_output=True,text=True)
def RS(c): return SP.run(c,capture_output=True,text=True,shell=True)

def _sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def _save_json(p,obj):
    try:
        with open(p,"w") as f:
            json.dump(obj,f,indent=2)
        return True
    except PermissionError:
        if OS!="Darwin": raise
        tmp="/tmp/_alloc.json"
        with open(tmp,"w") as f:
            json.dump(obj,f,indent=2)
        r=R(["sudo","cp",tmp,p])
        try: os.unlink(tmp)
        except: pass
        if r.returncode==0: return True
        msg=(r.stderr or r.stdout or "sudo cp failed").strip()
        print("⚠️ alloc.json 更新失敗: {}".format(msg))
        return False

# ── 平台層 ──
def _scan():
    d=[]
    if OS=="Darwin":
        r=R(["diskutil","list","external","physical"])
        for dev in re.findall(r"^(/dev/disk\d+)",r.stdout,re.M):
            i=R(["diskutil","info",dev]).stdout
            m=re.search(r"\((\d+)\s*Bytes?\)",i)
            nm=re.search(r"Media Name:\s*(.+)",i)
            name=nm.group(1).strip() if nm else dev
            if m and int(m.group(1))>=512*1024*1024: d.append((dev,int(m.group(1)),name))
    elif OS=="Windows":
        r=R(["powershell","-NoProfile","-Command",
             'Get-Disk | ForEach-Object { $n=$_.Number; $s=$_.Size; $b=$_.BusType; $v=Get-Partition -DiskNumber $n -ErrorAction SilentlyContinue | Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter } | Select-Object -First 1; if ($v) { "$n,$s,$b,$($v.DriveLetter): $($v.FileSystemLabel)" } else { "$n,$s,$b," } }'])
        for line in r.stdout.strip().split("\n"):
            line=line.strip()
            p=line.split(",")
            if len(p)>=3:
                try: sz=int(p[1])
                except: continue
                bus=p[2].strip()
                if bus!="USB": continue
                label=p[3].strip() if len(p)>=4 and p[3].strip() else ""
                if sz>=512*1024*1024: d.append(("PhysicalDrive"+p[0],sz,label))
    return d

def _mp(dev):
    if OS=="Darwin":
        part=dev+"s1"
        def _mounted_path():
            i=R(["diskutil","info",part]).stdout
            m=re.search(r"Mount Point:\s*(.+)",i)
            if not m: return None
            p=m.group(1).strip()
            if not p or p=="Not mounted": return None
            return p if os.path.ismount(p) else None
        p=_mounted_path()
        if p: return p
        R(["diskutil","mountDisk",dev]);R(["diskutil","mount",part]);time.sleep(1)
        return _mounted_path()
    elif OS=="Windows":
        for l in "DEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(l+":/alloc.json"): return l+":"
        n=dev.replace("PhysicalDrive","")
        r=R(["powershell","-NoProfile","-Command",
             '$v=Get-Partition -DiskNumber {} -ErrorAction SilentlyContinue | Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter }; if ($v) { $v.DriveLetter+\":\" }'.format(n)])
        dl=r.stdout.strip()
        if dl and os.path.exists(dl+"\\"):
            return dl.rstrip("\\")
    return None

def _unmount(dev):
    if OS=="Darwin": R(["diskutil","unmountDisk",dev])

def _fmt(dev):
    if OS=="Darwin":
        R(["diskutil","unmountDisk",dev])
        return R(["diskutil","eraseDisk","FAT32","SDCARD","MBRFormat",dev]).returncode==0
    elif OS=="Windows":
        n=dev.replace("PhysicalDrive","")
        scr="select disk {n}\nclean\nconvert mbr\ncreate partition primary\nformat fs=fat32 quick label=SDCARD\nactive\nassign\nexit\n".format(n=n)
        tf=os.path.join(os.environ.get("TEMP",os.getcwd()),"_sdfmt.txt")
        open(tf,"w").write(scr)
        print("格式化中 (diskpart)...")
        try:
            r=R(["diskpart","/s",tf])
        except OSError as e:
            try: os.unlink(tf)
            except: pass
            print("diskpart 需要管理員權限: "+str(e))
            return False
        try: os.unlink(tf)
        except: pass
        if r.returncode!=0:
            for line in (r.stdout+r.stderr).split("\n"):
                lo=line.lower()
                if any(w in lo for w in ("error","fail","cannot","denied","invalid")):
                    print("  "+line.strip())
            return False
        time.sleep(3)
        return True
    return False

def _w(dev,data,off):
    sz=((len(data)+S-1)//S)*S
    if OS=="Darwin":
        import shutil; pv=shutil.which("pv")
        tmp="/tmp/_ul.bin"
        open(tmp,"wb").write(data.ljust(sz,b"\x00"))
        if pv: RS("sudo dd if="+tmp+" bs=512 2>/dev/null | "+pv+" -s "+str(sz)+" 2>/dev/null | sudo dd of="+dev+" bs=512 seek="+str(off)+" 2>/dev/null")
        else: RS("sudo dd if="+tmp+" of="+dev+" bs=512 seek="+str(off)+" 2>/dev/null")
    elif OS=="Windows":
        with open("\\\\.\\"+dev,"wb") as f: f.seek(off*S); f.write(data.ljust(sz,b"\x00"))

def _r(dev,off,cnt,out):
    sz=cnt*S
    if OS=="Darwin":
        pv=shutil.which("pv")
        if pv: RS("sudo dd if="+dev+" bs=512 skip="+str(off)+" count="+str(cnt)+" 2>/dev/null | "+pv+" -s "+str(sz)+" > "+out)
        else: RS("sudo dd if="+dev+" of="+out+" bs=512 skip="+str(off)+" count="+str(cnt)+" 2>/dev/null")
    elif OS=="Windows":
        with open("\\\\.\\"+dev,"rb") as f: f.seek(off*S); d=f.read(sz)
        open(out,"wb").write(d)

# ── 功能 ──
def A(dev):
    m=_mp(dev)
    p=os.path.join(m,"alloc.json") if m else None
    return json.load(open(p)) if p and os.path.exists(p) else None

def _tail(a):
    t=a["_offset"]
    for k,v in a.items():
        if k.startswith("_"): continue
        t=max(t,v[0]+v[1])
    return t

def _split_upload_paths(raw):
    ps=[]
    for x in re.split(r"[\n,]+",raw):
        x=x.strip().strip('"').strip("'").strip()
        if not x: continue
        ps.append(os.path.expanduser(x))
    return ps

def _pick_name(a,p,fs,sh,ask_name):
    name=os.path.basename(p)
    while True:
        dup=None
        for k,v in a.items():
            if k.startswith("_"): continue
            if len(v)>=3 and v[2]==sh: dup=k; break
            if v[1]*S==fs: dup=dup or k
        if dup:
            print("⚠️ 與 {} 重複".format(dup))
            v=I("跳過? (enter=yes, r=rename): ")
            if v is None: return None
            if v.lower().startswith("r"):
                v2=I("新名: ")
                if v2 is None: return None
                name=v2
            else:
                return None
        elif ask_name:
            v=I("名 [{}]: ".format(name),name)
            if v is None: return None
            name=v or name
        if name not in a: return name
        v=I("覆蓋? (enter=yes, r=rename, q=cancel): ")
        if v is None: return None
        v=v.lower()
        if v.startswith("r"):
            v2=I("新名: ")
            if v2 is None: return None
            name=v2
            ask_name=False
            continue
        if v in ("yes","y",""): return name
        return None

def F(dev,cap):
    v=I("FAT MB [512]: ","512")
    if v is None: return
    f=int(v)
    if f<=0: _fmt(dev); print("✅"); return
    off=f*1048576//512; t=cap//512
    print("sector:{} FAT:{}MB managed:~{:.1f}GB".format(off,off*512/1048576,(t-off)*512/1073741824))
    if I("確認? (yes): ") is None: return
    if not _fmt(dev): print("❌"); return
    print("✅ FAT32 格式化完成")
    m=None
    for _ in range(6):
        time.sleep(1); m=_mp(dev)
        if m: break
    a={"_version":1,"_offset":off,"_total_sectors":t}
    if m:
        if _save_json(os.path.join(m,"alloc.json"),a):
            print("✅ alloc.json (offset={})".format(off))
        else:
            print("⚠️ alloc.json 寫入失敗")
    else:
        print("⚠️  無法取得掛載點，請重新插拔 SD 卡後再試")
    _unmount(dev)

def P(dev):
    a=A(dev)
    if not a: print("❌"); return
    off=a.get("_offset","?"); t=a.get("_total_sectors",0)
    print(" Managed Area sector:{}  ({:.1f}MB)".format(off,off*512/1048576))
    if t: print("  總容量: {} sectors ({:.1f}GB)".format(t,t*512/1073741824))
    print("─"*72)
    i=1; u=0
    for k,v in sorted(a.items(),key=lambda x:x[1][0] if isinstance(x[1],list) else 0):
        if k.startswith("_"): continue
        sz="{:.0f}K".format(v[1]*512/1024) if v[1]*512<1048576 else "{:.1f}M".format(v[1]*512/1048576)
        pct="{:>5.1f}".format(v[1]*100/t) if t else "?"
        sh=" "+v[2][:10] if len(v)>=3 and v[2] else ""
        print(" {:>2d}. {:24s} sec{:>8,d} {:>8s} {:>5s}%{:>12s}".format(i,k[:24],v[0],sz,pct,sh[:10]))
        u+=v[1]; i+=1
    print("─"*72)
    print(" 合計: {} 檔案, {} sectors, {:.1f}M, {:.1f}%".format(i-1,u,u*512/1048576,u*100/t if t else 0))

def DL(dev):
    a=A(dev)
    if not a: return
    fs=[k for k in a if not k.startswith("_")]
    if not fs: return
    for i,n in enumerate(fs): print(" {}. {} (sec{})".format(i+1,n,a[n][0]))
    v=I("選擇: "); 
    if v is None: return
    n=int(v)-1; name=fs[n]; sec,cnt=a[name][0],a[name][1]
    out=I("路徑 [./{}]: ".format(name),"./"+name)
    if out is None: return
    if os.path.exists(out):
        if I("⚠️ 覆蓋? (yes/no): ") is None: return
    _unmount(dev); _r(dev,sec,cnt,out)
    abspath=os.path.abspath(out)
    d=open(out,"rb").read()
    print("\n✅ {} bytes".format(len(d)))
    print("📁 {}".format(abspath))
    if len(a[name])>=3 and a[name][2]:
        h=hashlib.sha256(d).hexdigest()
        if h==a[name][2]: print("✅ SHA256 ok")
        else: print("⚠️ SHA256 mismatch")

def UL(dev):
    a=A(dev)
    if not a: return
    raw=I("檔案路徑（可多個，以逗號分隔）: ")
    if raw is None: return
    srcs=[]; bad=[]
    for p in _split_upload_paths(raw):
        if not os.path.exists(p): bad.append((p,"不存在"))
        elif not os.path.isfile(p): bad.append((p,"不是檔案"))
        else: srcs.append(p)
    for p,msg in bad: print("⚠️ 跳過 {}: {}".format(p,msg))
    if not srcs: return
    plan=[]; work=dict(a); tail=_tail(work); total=work.get("_total_sectors",0)
    for i,p in enumerate(srcs):
        fs=os.path.getsize(p); sh=_sha256_file(p)
        print("\n[{} / {}] {}".format(i+1,len(srcs),os.path.basename(p)))
        print("SHA256:",sh[:24],fs)
        name=_pick_name(work,p,fs,sh,True)
        if not name: continue
        cnt=(fs+S-1)//S
        if total and tail+cnt>total:
            free=max(0,total-tail)
            print("❌ 空間不足: {} 需要 {} sectors, 剩餘 {} sectors".format(name,cnt,free))
            continue
        plan.append((p,name,sh,tail,cnt))
        work[name]=[tail,cnt,sh]
        tail+=cnt
    if not plan: return
    _unmount(dev)
    for i,(p,name,sh,sec,cnt) in enumerate(plan):
        print("寫入 [{}/{}] {} ...".format(i+1,len(plan),name))
        data=open(p,"rb").read()
        _w(dev,data,sec)
    m=_mp(dev)
    if m:
        if _save_json(os.path.join(m,"alloc.json"),work):
            chk=A(dev)
            ok=chk and all(name in chk and chk[name][:2]==[sec,cnt] for _,name,_,sec,cnt in plan)
            if ok:
                print("\n✅ 完成上傳 {} 個檔案".format(len(plan)))
                for name,sec,cnt in [(x[1],x[3],x[4]) for x in plan]:
                    print("  - {} sector{}~{}".format(name,sec,sec+cnt))
            else:
                print("⚠️ alloc.json 已嘗試更新，但重新讀回驗證失敗")
        else:
            print("⚠️ 已寫入資料區，但 alloc.json 更新失敗")
    else:
        print("⚠️ 已寫入資料區，但無法掛載回 FAT 分區更新 alloc.json，請重新插拔 SD 卡後檢查")

def TR(dev):
    a=A(dev)
    if not a: return
    fs=[k for k in a if not k.startswith("_")]
    if not fs: return
    for i,n in enumerate(fs): print(" {}. {}".format(i+1,n))
    v=I("選擇: ")
    if v is None: return
    n=int(v)-1; name=fs[n]
    if I("確認? (yes): ") is None: return
    s=a[name][0]; m=_mp(dev)
    if m:
        r=json.load(open(os.path.join(m,"alloc.json")))
        rm=[k for k,v in r.items() if not k.startswith("_") and v[0]>=s]
        for k in rm: del r[k]
        if _save_json(os.path.join(m,"alloc.json"),r):
            print("✅ 刪除:",", ".join(rm))
        else:
            print("⚠️ 刪除清單已計算，但 alloc.json 更新失敗")

def _is_admin():
    if OS!="Windows": return True
    try: return ctypes.windll.shell32.IsUserAnAdmin()!=0
    except: return False

def main():
    print("\nSD 卡工具 (OS: {})\n{}".format(OS,"="*50))
    if OS=="Windows" and not _is_admin():
        print("正在以管理員身份重新啟動...")
        ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable,__file__,None,1)
        os._exit(0)
    disks=_scan()
    if not disks: print("❌ 找不到 SD 卡"); return
    for i,(d,c,lb) in enumerate(disks):
        info="  ({:.1f}GB)".format(c/1073741824)
        label=lb if lb else d
        print(" {}. {}{}".format(i+1,label,info))
    n=I("選擇: ")
    if n is None: return
    dev,cap,lb=disks[int(n)-1]
    dev_display=lb if lb else dev
    while True:
        print("\nDevice: {} ({})".format(dev_display,dev)); print("1.格式化 2.列表 3.下載 4.上傳(可批量) 5.刪除 0.離開")
        c=I("選擇: ")
        if c is None: break
        if c=="1": F(dev,cap)
        elif c=="2": P(dev)
        elif c=="3": DL(dev)
        elif c=="4": UL(dev)
        elif c=="5": TR(dev)
        elif c=="0": break

if __name__=="__main__":
    main()
