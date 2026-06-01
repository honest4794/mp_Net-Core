# -*- coding: utf-8 -*-
"""測試: ESP Managed Area Web Server

用法: 上傳到 ESP 後:
  import managed_web
  managed_web.run()

瀏覽器: http://<esp_ip>:8080/
  首頁         /          檔案列表 + 上傳表單
  下載    /dl/name       下載檔案
  刪除    /trim/name     刪除此檔案(往後全刪)
  上傳    /up            POST multipart
"""

import socket, gc, re, time
from tools.alloc import Allocator
from tools.fast_io import FastReader, FastWriter

def _h(t,b):
    return ("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n"
        "<html><head><meta charset=utf-8><title>{}</title>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<style>body{{font-family:sans-serif;max-width:800px;margin:20px auto}}"
        "table{{width:100%;border-collapse:collapse}}"
        "td,th{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}"
        "a{{color:#06f;text-decoration:none}}"
        ".b{{display:inline-block;padding:6px 14px;background:#06f;color:#fff;border-radius:4px;margin:3px}}"
        ".r{{background:#c33}}"
        "form{{margin:20px 0}}input{{padding:6px;margin:4px}}"
        "</style></head><body><h1>{}</h1>{}</body></html>").format(t,t,b)

def _d(a,r,w,sd,m,p,body):
    if m=="GET" and p=="/":
        rows="";t=0
        for n,i in sorted(a.list_files().items(),key=lambda x:x[1]["sector"]):
            rows+="<tr><td>{}</td><td>{:.1f}MB</td><td><a href=/dl/{} class=b>下載</a> <a href=/trim/{} class='b r'>刪除</a></td></tr>".format(n,i["mb"],n,n)
            t+=i["bytes"]
        if not rows: rows="<tr><td colspan=3>無檔案</td></tr>"
        return _h("Managed","<table><tr><th>檔名</th><th>大小</th><th></th></tr>{}</table><p>合計 {:.1f}MB</p><h3>上傳</h3><form action=/up method=post enctype=multipart/form-data><input type=file name=f required><input type=submit value=上傳></form>".format(rows,t/1048576))

    z=re.match(r"^/dl/(.+)$",p)
    if z and m=="GET":
        i=a.find(z.group(1))
        if not i: return b"HTTP/1.0 404\r\n\r\n"
        d=r.read(i[0],i[1])
        return b"HTTP/1.0 200 OK\r\nContent-Disposition: attachment\r\nContent-Length: "+str(len(d)).encode()+b"\r\n\r\n"+d

    z=re.match(r"^/trim/(.+)$",p)
    if z and m=="GET":
        r2=a.trim_from(z.group(1))
        if r2: a.save()
        return b"HTTP/1.0 302 Found\r\nLocation: /\r\n\r\n"

    if p=="/up" and m=="POST":
        t0=time.ticks_ms()
        try:
            # boundary 在 HTTP header, filename 在 multipart body
            bd=None
            for l in head.split("\r\n"):
                if "boundary=" in l: bd=l.split("boundary=")[1].split(";")[0].strip(); break
            if not bd: return _h("Err","boundary?")
            part_hdr=body[:body.find(b"\r\n\r\n")].decode()
            fn=re.search(r'filename="([^"]+)"',part_hdr)
            if not fn: return _h("Err","filename?")
            name=fn.group(1)
            sep=body.find(b"\r\n\r\n")
            if sep<0: return _h("Err","bad")
            data=body[sep+4:]
            for n in (b"--"+bd.encode()+b"--",b"--"+bd.encode()+b"\r\n"):
                j=data.find(n)
                if j>=0: data=data[:j]
            data=data.rstrip(b"\r\n- ")

            ss=sd.info()[1]; cnt=(len(data)+ss-1)//ss
            sec=a.append(name,cnt); w.write(sec,data); a.save()
            return _h("OK","<p>✅ {} ({} bytes)</p><a href=/ class=b>返回</a>".format(name,len(data)))
        except Exception as e: return _h("Error",str(e))

    return b"HTTP/1.0 404\r\n\r\n"

def _wifi():
    import network,time
    w=network.WLAN(network.STA_IF)
    if w.active() and w.isconnected():
        ip=w.ifconfig()[0];print("WiFi:",ip);return ip
    try:
        import json
        with open("/config.json")as f:c=json.load(f)
        s=c["Network"]["wifi"]["ssid"];p=c["Network"]["wifi"].get("ssid_pw","")
        w.active(True);w.connect(s,p)
        for _ in range(30):
            if w.isconnected():ip=w.ifconfig()[0];print("IP:",ip);return ip
            time.sleep(0.5)
    except:pass
    ap=network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP-Managed",authmode=0)
    time.sleep(2)
    if ap.active():
        ip=ap.ifconfig()[0];print("AP: ESP-Managed  IP:",ip);return ip
    print("AP fail");return None

def run(port=8080):
    try:
        from lib.sys_bus import bus
        sd=bus.get_service("sd_raw")
        if not sd: raise ValueError
        a=Allocator(); r=FastReader(sd); w=FastWriter(sd)
    except Exception as e: print("init:",e); return
    ip=_wifi()
    if not ip: return
    s=socket.socket()
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind(("0.0.0.0",port)); s.listen(3)
    print("http://{}:{}".format(ip,port))

    while True:
        try:
            cl,_=s.accept()
            d=b""
            while b"\r\n\r\n" not in d:
                more=cl.recv(4096)
                if not more: break
                d+=more
            if not d: cl.close(); continue
            parts=d.split(b"\r\n")[0].decode().split()
            m,p=parts[0],parts[1]
            hdr_end=d.find(b"\r\n\r\n")
            head=d[:hdr_end].decode()
            body=d[hdr_end+4:]
            for l in head.split("\r\n"):
                if l.lower().startswith("content-length"):
                    n=int(l.split(":")[1])
                    while len(body)<n:
                        more=cl.recv(4096)
                        if not more: break
                        body+=more
                    break
            resp=_d(a,r,w,sd,m,p,body)
            if isinstance(resp,str): resp=resp.encode()
            cl.sendall(resp); cl.close()
        except KeyboardInterrupt: break
        except: pass
    s.close(); w.close(); r.close()
    print("done")
