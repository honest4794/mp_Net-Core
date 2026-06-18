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
        cmd='$v=Get-Partition -DiskNumber '+n+' -ErrorAction SilentlyContinue | Get-Volume -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter }; if ($v) { $v.DriveLetter+":" }'
        r=R(["powershell","-NoProfile","-Command",cmd])
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
        for attempt in range(2):
            print("格式化中 (diskpart)..." if attempt==0 else "重試格式化...")
            try:
                r=R(["diskpart","/s",tf])
            except OSError as e:
                try: os.unlink(tf)
                except: pass
                print("diskpart 需要管理員權限: "+str(e))
                return False
            if r.returncode==0:
                try: os.unlink(tf)
                except: pass
                time.sleep(3)
                return True
            if attempt==0:
                time.sleep(2); continue
            try: os.unlink(tf)
            except: pass
            for line in (r.stdout+r.stderr).split("\n"):
                lo=line.lower()
                if any(w in lo for w in ("error","fail","cannot","denied","invalid")):
                    print("  "+line.strip())
            return False
    return False

def _win_letters(dev):
    n=dev.replace("PhysicalDrive","")
    cmd='(Get-Partition -DiskNumber '+n+' -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter }).DriveLetter'
    r=R(["powershell","-NoProfile","-Command",cmd])
    return [c for c in r.stdout.strip().split() if c.isalpha()]

def _win_k():
    import ctypes
    from ctypes import wintypes
    k=ctypes.windll.kernel32
    k.CreateFileW.restype=wintypes.HANDLE
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    k.SetFilePointerEx.argtypes=[wintypes.HANDLE,ctypes.c_longlong,ctypes.POINTER(ctypes.c_longlong),wintypes.DWORD]
    k.ReadFile.argtypes=[wintypes.HANDLE,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.LPVOID]
    k.WriteFile.argtypes=[wintypes.HANDLE,wintypes.LPCVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.LPVOID]
    k.DeviceIoControl.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.LPVOID]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    return k

def _win_disk(dev,k):
    import ctypes
    GENERIC_READ=0x80000000; GENERIC_WRITE=0x40000000
    FILE_SHARE_RW=0x1|0x2; OPEN_EXISTING=3
    h=k.CreateFileW("\\\\.\\"+dev,GENERIC_READ|GENERIC_WRITE,FILE_SHARE_RW,None,OPEN_EXISTING,0,None)
    INVALID=ctypes.c_void_p(-1).value
    if not h or h==INVALID:
        raise OSError("無法開啟磁碟 "+dev+" (錯誤碼 {})".format(ctypes.get_last_error()))
    return h

def _win_lock(k,letters):
    """Lock volumes - keep handles alive, caller must close"""
    import ctypes
    from ctypes import wintypes
    FSCTL_LOCK_VOLUME=0x00090018; FSCTL_DISMOUNT_VOLUME=0x00090020
    ret=wintypes.DWORD(0)
    INVALID=ctypes.c_void_p(-1).value
    handles=[]
    for l in letters:
        vh=k.CreateFileW("\\\\.\\"+l+":",0x80000000|0x40000000,0x1|0x2,None,3,0,None)
        if not vh or vh==INVALID: continue
        k.DeviceIoControl(vh,FSCTL_LOCK_VOLUME,None,0,None,0,ctypes.byref(ret),None)
        k.DeviceIoControl(vh,FSCTL_DISMOUNT_VOLUME,None,0,None,0,ctypes.byref(ret),None)
        handles.append(vh)
    return handles

def _win_unlock(k,handles):
    """Close volume handles to release locks"""
    for h in handles:
        try: k.CloseHandle(h)
        except: pass

def _win_io(dev,off,buf,read_len=0,letters=""):
    import ctypes
    from ctypes import wintypes
    k=_win_k()
    h=_win_disk(dev,k)
    lock_h=None
    try:
        if letters: lock_h=_win_lock(k,letters)
        pos=ctypes.c_longlong(off*S); newpos=ctypes.c_longlong(0)
        if not k.SetFilePointerEx(h,pos,ctypes.byref(newpos),0):
            raise OSError("SetFilePointerEx 失敗 ({})".format(ctypes.get_last_error()))
        done=wintypes.DWORD(0)
        if read_len:
            outbuf=ctypes.create_string_buffer(read_len)
            if not k.ReadFile(h,outbuf,read_len,ctypes.byref(done),None):
                raise OSError("ReadFile 失敗 ({})".format(ctypes.get_last_error()))
            return outbuf.raw[:done.value]
        else:
            cbuf=ctypes.create_string_buffer(buf,len(buf))
            if not k.WriteFile(h,cbuf,len(buf),ctypes.byref(done),None):
                raise OSError("WriteFile 失敗 ({})".format(ctypes.get_last_error()))
            return done.value
    finally:
        if lock_h: _win_unlock(k,lock_h)
        k.CloseHandle(h)

CHUNK_S=8  # 4096 bytes = 8 sectors per IO call

def _w(dev,data,off):
    sz=((len(data)+S-1)//S)*S
    if OS=="Darwin":
        import shutil; pv=shutil.which("pv")
        tmp="/tmp/_ul.bin"
        open(tmp,"wb").write(data.ljust(sz,b"\x00"))
        if pv: RS("sudo dd if="+tmp+" bs=512 2>/dev/null | "+pv+" -s "+str(sz)+" 2>/dev/null | sudo dd of="+dev+" bs=512 seek="+str(off)+" 2>/dev/null")
        else: RS("sudo dd if="+tmp+" of="+dev+" bs=512 seek="+str(off)+" 2>/dev/null")
    elif OS=="Windows":
        buf=data.ljust(sz,b"\x00")
        k=_win_k()
        # lock volume once, hold throughout this file
        letters=_win_letters(dev)
        lock_handles=_win_lock(k,letters)
        try:
            for pos in range(0,sz,CHUNK_S*S):
                end=min(pos+CHUNK_S*S,sz)
                sec_off=off+pos//S
                chunk=buf[pos:end]
                h=_win_disk(dev,k)
                try:
                    import ctypes; from ctypes import wintypes
                    p=ctypes.c_longlong(sec_off*S); np=ctypes.c_longlong(0)
                    k.SetFilePointerEx(h,p,ctypes.byref(np),0)
                    cb=ctypes.create_string_buffer(chunk,len(chunk))
                    d=wintypes.DWORD(0)
                    ok=k.WriteFile(h,cb,len(chunk),ctypes.byref(d),None)
                    if not ok or d.value!=len(chunk):
                        err=ctypes.get_last_error()
                        raise OSError("WriteFile at sector {} wrote {}/{} err={}".format(sec_off,d.value,len(chunk),err))
                finally:
                    k.CloseHandle(h)
        finally:
            _win_unlock(k,lock_handles)

def _r(dev,off,cnt,out):
    sz=cnt*S
    if OS=="Darwin":
        pv=shutil.which("pv")
        if pv: RS("sudo dd if="+dev+" bs=512 skip="+str(off)+" count="+str(cnt)+" 2>/dev/null | "+pv+" -s "+str(sz)+" > "+out)
        else: RS("sudo dd if="+dev+" of="+out+" bs=512 skip="+str(off)+" count="+str(cnt)+" 2>/dev/null")
    elif OS=="Windows":
        import ctypes; from ctypes import wintypes
        k=_win_k(); letters=_win_letters(dev)
        lock_handles=_win_lock(k,letters)
        try:
            with open(out,"wb") as f:
                for sec_off in range(0,cnt,CHUNK_S):
                    n=min(CHUNK_S,cnt-sec_off)
                    h=_win_disk(dev,k)
                    try:
                        p=ctypes.c_longlong((off+sec_off)*S); np=ctypes.c_longlong(0)
                        k.SetFilePointerEx(h,p,ctypes.byref(np),0)
                        outbuf=ctypes.create_string_buffer(n*S)
                        d2=wintypes.DWORD(0)
                        k.ReadFile(h,outbuf,n*S,ctypes.byref(d2),None)
                        f.write(outbuf.raw[:d2.value])
                    finally:
                        k.CloseHandle(h)
        finally:
            _win_unlock(k,lock_handles)

def _r_mem(dev,off,cnt):
    """Read sectors to bytes (chunked, persistent lock)"""
    import ctypes; from ctypes import wintypes
    k=_win_k(); letters=_win_letters(dev)
    lock_handles=_win_lock(k,letters)
    try:
        rd=b""
        for sec_off in range(0,cnt,CHUNK_S):
            n=min(CHUNK_S,cnt-sec_off)
            h=_win_disk(dev,k)
            try:
                p=ctypes.c_longlong((off+sec_off)*S); np=ctypes.c_longlong(0)
                k.SetFilePointerEx(h,p,ctypes.byref(np),0)
                outbuf=ctypes.create_string_buffer(n*S)
                d2=wintypes.DWORD(0)
                k.ReadFile(h,outbuf,n*S,ctypes.byref(d2),None)
                rd+=outbuf.raw[:d2.value]
            finally:
                k.CloseHandle(h)
        return rd
    finally:
        _win_unlock(k,lock_handles)

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
    v=I("選擇: ")
    if v is None: return
    n=int(v)-1; name=fs[n]; sec,cnt=a[name][0],a[name][1]
    out=I("路徑 [./{}]: ".format(name),"./"+name)
    if out is None: return
    out=out.strip().strip('"').strip("'")
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
    time.sleep(1)
    for i,(p,name,sh,sec,cnt) in enumerate(plan):
        print("寫入 [{}/{}] {} ...".format(i+1,len(plan),name))
        data=open(p,"rb").read()
        sz=((len(data)+S-1)//S)*S
        buf=data.ljust(sz,b"\x00")
        fail_at=None
        rd=b""

        if OS=="Darwin":
            _w(dev,data,sec)
            _r(dev,sec,cnt,"/tmp/_chk.bin")
            rd=open("/tmp/_chk.bin","rb").read()
        else:
            import ctypes; from ctypes import wintypes
            k=_win_k()
            letters=_win_letters(dev)
            lock_h=_win_lock(k,letters)
            try:
                h=_win_disk(dev,k)
                try:
                    for pos in range(0,sz,CHUNK_S*S):
                        end=min(pos+CHUNK_S*S,sz)
                        sec_off=sec+pos//S
                        chunk=buf[pos:end]
                        p2=ctypes.c_longlong(sec_off*S); np2=ctypes.c_longlong(0)
                        k.SetFilePointerEx(h,p2,ctypes.byref(np2),0)
                        cb=ctypes.create_string_buffer(chunk,len(chunk))
                        d2=wintypes.DWORD(0)
                        ok=k.WriteFile(h,cb,len(chunk),ctypes.byref(d2),None)
                        if not ok or d2.value!=len(chunk):
                            err=ctypes.get_last_error()
                            fail_at="write sector {} wrote {}/{} err={}".format(sec_off,d2.value,len(chunk),err)
                            break
                        p3=ctypes.c_longlong(sec_off*S); np3=ctypes.c_longlong(0)
                        k.SetFilePointerEx(h,p3,ctypes.byref(np3),0)
                        outbuf=ctypes.create_string_buffer(len(chunk))
                        d3=wintypes.DWORD(0)
                        k.ReadFile(h,outbuf,len(chunk),ctypes.byref(d3),None)
                        rd+=outbuf.raw[:d3.value]
                        if outbuf.raw[:d3.value]!=chunk:
                            allff=all(b==0xFF for b in outbuf.raw[:64])
                            all00=all(b==0x00 for b in outbuf.raw[:64])
                            fail_at="verify sector {} mismatch (ff={} 00={})".format(sec_off,allff,all00)
                            break
                finally:
                    k.CloseHandle(h)
            finally:
                _win_unlock(k,lock_h)

        all_ff=all(b==0xFF for b in rd[:1024])
        all_00=all(b==0x00 for b in rd[:1024])
        if fail_at:
            print("  ❌ {}".format(fail_at))
        elif all_ff:
            print("  ❌ 寫入失敗！sector {} 讀回全 0xFF".format(sec))
        elif all_00:
            print("  ❌ 寫入失敗！sector {} 讀回全 0x00".format(sec))
        else:
            rh=hashlib.sha256(rd).hexdigest()
            if rh==sh:
                print("  ✅ SHA256 驗證通過")
            else:
                print("  ❌ SHA256 不匹配！")
                print("     expected: {}...".format(sh[:32]))
                print("     got:      {}...".format(rh[:32]))
                print("     head64B:  {}".format(rd[:64].hex()))
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
        print("\n⚠️  需要管理員權限才能格式化 / 讀寫 SD 卡。")
        print("    請『關閉此視窗』，然後：")
        print("    1) 用滑鼠右鍵點擊『命令提示字元 / PowerShell』→『以系統管理員身分執行』")
        print("    2) 在該視窗輸入: python \"{}\"".format(os.path.abspath(__file__)))
        if I("\n或按 Enter 直接嘗試自動提權 (q=取消): ") is None: return
        try:
            ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable,'"{}"'.format(os.path.abspath(__file__)),None,1)
        except Exception as e:
            print("自動提權失敗:",e)
        return
    disks=_scan()
    if not disks: print("❌ 找不到 SD 卡"); return
    for i,(d,c,lb) in enumerate(disks):
        info="  ({:.1f}GB)".format(c/1073741824)
        label=lb if lb else d
        print(" {}. {}{}".format(i+1,label,info))
    n=I("選擇: ")
    if n is None: return
    dev,cap,lb=disks[int(n)-1]
    while True:
        if OS=="Windows":
            ls=_win_letters(dev)
            dev_display=(ls[0]+": SDCARD") if ls else dev
        else:
            dev_display=lb if lb else dev
        print("\nDevice: {} ({})".format(dev_display,dev)); print("1.格式化 2.列表 3.下載 4.上傳(可批量) 5.刪除 0.離開")
        c=I("選擇: ")
        if c is None: break
        try:
            if c=="1": F(dev,cap)
            elif c=="2": P(dev)
            elif c=="3": DL(dev)
            elif c=="4": UL(dev)
            elif c=="5": TR(dev)
            elif c=="0": break
        except Exception as e:
            print("⚠️  操作發生錯誤: {}: {}".format(type(e).__name__,e))

if __name__=="__main__":
    main()
