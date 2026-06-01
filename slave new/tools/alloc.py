# -*- coding: utf-8 -*-
"""Managed area 分配器 — sector 表

用法:
  from tools.alloc import Allocator
  a=Allocator()
  sec=a.append("f.jpk",100)
  a.find("f.jpk")
  a.trim_from("f.jpk")
"""

import json,os

ALLOC="/sd/alloc.json"

class Allocator:
    def __init__(self,path=ALLOC,offset=None,sector_size=512):
        self._p=path;self._ss=sector_size
        self._off=offset or 0
        self._e={};self._d=False
        self._load()

    @classmethod
    def format(cls,sd,fat_mb=32):
        c=sd.info()[0];ss=sd.info()[1];t=c//ss
        off=(fat_mb*1048576)//ss
        import vfs_fat,os
        vfs_fat.mkfs(sd);os.mount(sd,"/sd")
        a=cls(offset=off);a.save()
        return a

    def append(self,name,cnt):
        tail=self._off
        for _,(s,c) in self._e.items():tail=max(tail,s+c)
        self._e[name]=(tail,cnt);self._d=True
        return tail

    def trim_from(self,name):
        if name not in self._e:return[]
        s=self._e[name][0];rem=[]
        for n,(st,c) in list(self._e.items()):
            if st>=s:del self._e[n];rem.append(n)
        self._d=True;return rem

    def find(self,name):
        e=self._e.get(name)
        if e:return e
        for k,v in self._e.items():
            if k.endswith(name) or name.endswith(k):return v
        return None

    def list_files(self):
        return{k:{"sector":v[0],"count":v[1],"bytes":v[1]*self._ss,"mb":v[1]*self._ss/1048576}
               for k,v in self._e.items()}

    def save(self):
        if self._d:self._save()

    def _load(self):
        try:
            with open(self._p)as f:r=json.load(f)
            if"_offset"in r:self._off=r["_offset"]
            for k,v in r.items():
                if k.startswith("_") and not isinstance(v,list):continue
                self._e[k]=(v[0],v[1])
        except Exception as e:
            print("alloc load err:", e)

    def _save(self):
        try:
            r={"_version":1,"_offset":self._off}
            for k,v in self._e.items():r[k]=[v[0],v[1]]
            with open(self._p,"w")as f:
                json.dump(r,f)
                f.flush()
            self._d=False
        except Exception as e:print("save:",e)
