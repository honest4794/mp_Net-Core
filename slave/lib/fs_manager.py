import os
import time
import ujson
import ubinascii
import hashlib
from lib.dispatch import dprint

MANIFEST_FILE = "/manifest.json"

class FileSystemManager:
    """
    Unified File System Manager
    Responsibilities:
    1. Atomic File Write (write to .tmp -> verify -> rename)
    2. Manifest Management (load, save, update)
    3. Background Scanning (Core 1)
    4. File Reception Logic (replacing FileRx)
    """
    def __init__(self):
        self.manifest = {}
        self.scanning = False
        self._scan_files = []
        self._scan_manifest = {}
        self._scan_idx = 0

        # === 統一資料層 (RAM / SD-raw / FAT) ===
        # RAM cache：路徑前綴 /ram 的暫存區 (斷電消失)
        self._ram = {}

        # 初始化時檢查 alloc.json 決定讀寫模式
        #   alloc.json 存在 → raw 高速模式 (fast_io.Storage)
        #   alloc.json 不存在 → FAT 模式 (os.open/readinto)
        self._raw_mode = False
        self._raw = None
        try:
            os.stat("/sd/alloc.json")
            from lib.sys_bus import bus
            if bus.get_service("sd_raw") is not None:
                from lib.fast_io import Storage
                self._raw = Storage()
                self._raw_mode = True
                print("✅ [FS] SD-raw backend ready (alloc.json found)")
        except Exception:
            pass
        if not self._raw_mode:
            print("📂 [FS] FAT mode (alloc.json not found)")

        # Session State for File Upload
        self.session = {
            "active": False,
            "path": None,
            "temp_path": None,
            "fp": None,
            "file_id": 0,
            "written": 0,
            "sha_expect_hex": None,
            "last_error": None,
            "last_sha_hex": ""
        }

        # 串流讀取狀態
        self._str_kind = None

        self.load_manifest()

    def load_manifest(self):
        try:
            with open(MANIFEST_FILE, "r") as f:
                self.manifest = ujson.load(f)
            print(f"📦 [FS] Manifest loaded: {len(self.manifest)} files")
        except:
            print("⚠️ [FS] Manifest missing or corrupt, starting scan...")
            self.manifest = {}
            # Start background scan if manifest is missing
            self.scan_all()

    def _load_scan_ignore(self):
        prefixes = []
        try:
            with open("/config.json", "r") as f:
                cfg = ujson.load(f)
            raw = cfg.get("scan_ignore")
            if raw is None:
                raw = cfg.get("fs", {}).get("scan_ignore")
            if isinstance(raw, list):
                for p in raw:
                    p = str(p).rstrip("/")
                    if p:
                        prefixes.append(p)
        except Exception:
            pass
        return prefixes

    def _is_ignored(self, path, prefixes):
        for p in prefixes:
            if path == p or path.startswith(p + "/"):
                return True
        return False

    def save_manifest(self):
        try:
            with open(MANIFEST_FILE, "w") as f:
                # Custom Pretty Dump for Manifest
                f.write("{\n")
                # Sort keys for consistent order
                keys = sorted(self.manifest.keys())
                for i, k in enumerate(keys):
                    entry = self.manifest[k]
                    # Use json.dumps for key to handle escaping
                    key_str = ujson.dumps(k)
                    # Entry is small, keep it one line: {"s": 123, "h": "..."}
                    entry_str = ujson.dumps(entry)
                    
                    f.write(f'    {key_str}: {entry_str}')
                    
                    if i < len(keys) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                f.write("}")
        except Exception as e:
            print(f"❌ [FS] Save manifest failed: {e}")

    def update_manifest_entry(self, path, size, sha_hex):
        self.manifest[path] = {
            "s": size,
            "h": sha_hex
        }
        self.save_manifest()

    def remove_manifest_entry(self, path):
        if path in self.manifest:
            del self.manifest[path]
            self.save_manifest()

    # ==================== File Reception Logic ====================
    
    def _close_session(self):
        if self.session["fp"]:
            try:
                self.session["fp"].flush()
                if hasattr(os, 'sync'): os.sync()
                self.session["fp"].close()
            except:
                pass
        self.session["fp"] = None

    def begin_write(self, args: dict) -> bool:
        """FILE_BEGIN (0x2001)"""
        self._close_session()
        
        # Reset Session
        self.session.update({
            "active": False,
            "path": args.get("path"),
            "file_id": int(args.get("file_id", 0)),
            "written": 0,
            "last_error": None
        })
        
        sha_bytes = args.get("sha256")
        self.session["sha_expect_hex"] = ubinascii.hexlify(sha_bytes).decode() if sha_bytes else None
        
        if not self.session["path"]:
            self.session["last_error"] = "MISSING_PATH"
            return False

        try:
            # Create Temp Path
            self.session["temp_path"] = self.session["path"] + ".tmp"
            
            # Ensure Directory
            parent = "/".join(self.session["temp_path"].split("/")[:-1])
            if parent:
                parts = parent.split("/")
                curr = ""
                for p in parts:
                    if not p: continue
                    curr += "/" + p
                    try:
                        os.stat(curr)
                    except:
                        try:
                            os.mkdir(curr)
                        except:
                            pass
            
            # Open Temp File
            self.session["fp"] = open(self.session["temp_path"], "wb")
            self.session["active"] = True
            return True
            
        except Exception as e:
            self.session["last_error"] = f"OPEN_FAIL: {e}"
            return False

    def write_chunk(self, args: dict) -> bool:
        """FILE_CHUNK (0x2002)"""
        if not self.session["active"] or not self.session["fp"]:
            self.session["last_error"] = "NO_ACTIVE_SESSION"
            return False
            
        req_id = int(args.get("file_id", 0))
        if req_id != self.session["file_id"]:
            self.session["last_error"] = f"ID_MISMATCH {req_id}!={self.session['file_id']}"
            return False
            
        off = int(args.get("offset", 0))
        data = args.get("data", b"")
        
        try:
            if off != self.session["written"]:
                self.session["fp"].seek(off)
            
            self.session["fp"].write(data)
            self.session["written"] = off + len(data)
            return True
        except Exception as e:
            self.session["last_error"] = f"WRITE_FAIL: {e}"
            self.session["active"] = False
            return False

    def end_write(self, args: dict) -> bool:
        """FILE_END (0x2003) -> Finalize"""
        if not self.session["active"]:
            return False
            
        self._close_session()
        
        try:
            ok, result = self._finalize_atomic_write(
                self.session["path"], 
                self.session["temp_path"], 
                self.session["sha_expect_hex"]
            )
            
            if ok:
                self.session["last_sha_hex"] = result
                self.session["active"] = False
                return True
            else:
                self.session["last_error"] = f"FINALIZE_ERR: {result}"
                self.session["last_sha_hex"] = "00"*32
                self.session["active"] = False
                return False
                
        except Exception as e:
            self.session["last_error"] = f"VERIFY_ERR: {e}"
            self.session["active"] = False
            return False

    def _finalize_atomic_write(self, path, temp_path, expected_sha):
        """Internal finalize logic"""
        try:
            # 1. Calc SHA
            h = hashlib.sha256()
            buf = bytearray(2048)
            size = 0
            with open(temp_path, "rb") as f:
                while True:
                    n = f.readinto(buf)
                    if n == 0: break
                    h.update(memoryview(buf)[:n])
                    size += n
            
            got_sha = ubinascii.hexlify(h.digest()).decode()
            
            # 2. Verify
            if expected_sha and got_sha != expected_sha:
                print(f"❌ [FS] SHA Mismatch! Got: {got_sha}, Exp: {expected_sha}")
                os.remove(temp_path)
                return False, "SHA_MISMATCH"
            
            # 3. Rename (Atomic Replace)
            try:
                os.stat(path)
                os.remove(path)
            except:
                pass
                
            os.rename(temp_path, path)
            
            # 4. Update Manifest
            self.update_manifest_entry(path, size, got_sha)
            print(f"✅ [FS] Written: {path} (Size: {size})")
            return True, got_sha
            
        except Exception as e:
            print(f"❌ [FS] Finalize failed: {e}")
            try: os.remove(temp_path)
            except: pass
            return False, str(e)

    # ==================== Unified Data Layer ====================
    # 路徑前綴決定目的地：
    #   /ram/...  -> RAM cache (暫存，最快)
    #   /sd/...   -> SD 永久儲存 (依 _raw_mode 決定走 raw 或 FAT)
    #   其他/相對路徑 -> 預設補 /sd
    #
    # raw 模式 (alloc.json 存在)：讀寫直接走 fast_io.Storage
    # FAT 模式 (alloc.json 不存在)：讀寫走 os.open/readinto

    def resolve(self, path):
        """正規化路徑前綴。回傳 (kind, full_path, raw_name)
        kind: 'ram' | 'sd'
        full_path: FAT 用的完整路徑 (/ram/... 或 /sd/...)
        raw_name : SD-raw alloc 用的鍵名 (去掉 /sd 前綴)
        """
        p = str(path)
        if not p.startswith("/"):
            p = "/" + p
        if p == "/ram" or p.startswith("/ram/"):
            return ("ram", p, p[len("/ram"):].lstrip("/"))
        if p == "/sd" or p.startswith("/sd/"):
            return ("sd", p, p[len("/sd"):].lstrip("/"))
        return ("sd", "/sd" + p, p.lstrip("/"))

    def _ensure_parent(self, full_path):
        parent = "/".join(full_path.split("/")[:-1])
        if not parent:
            return
        curr = ""
        for part in parent.split("/"):
            if not part:
                continue
            curr += "/" + part
            try:
                os.stat(curr)
            except Exception:
                try:
                    os.mkdir(curr)
                except Exception:
                    pass

    def write(self, path, data):
        """統一寫入：依路由 + 模式寫入，回傳 True/False。"""
        kind, full, raw_name = self.resolve(path)

        if kind == "ram":
            self._ram[full] = bytes(data)
            return True

        if self._raw_mode and self._raw is not None and raw_name:
            try:
                self._raw.write_file(raw_name, data)
                return True
            except Exception as e:
                print("⚠️ [FS] raw write failed:", e)

        # FAT 落地
        try:
            self._ensure_parent(full)
            tmp = full + ".tmp"
            h = hashlib.sha256()
            mv = memoryview(data)
            with open(tmp, "wb") as f:
                f.write(mv)
            size = len(mv)
            h.update(mv)
            try:
                os.stat(full)
                os.remove(full)
            except Exception:
                pass
            os.rename(tmp, full)
            self.update_manifest_entry(full, size, ubinascii.hexlify(h.digest()).decode())
            return True
        except Exception as e:
            print("❌ [FS] FAT write failed:", e)
            try:
                os.remove(full + ".tmp")
            except Exception:
                pass
            return False

    def read(self, path):
        """統一讀取整個檔案。回傳 bytes 或 None。"""
        kind, full, raw_name = self.resolve(path)

        if kind == "ram":
            return self._ram.get(full)

        if self._raw_mode and self._raw is not None and raw_name:
            try:
                return bytes(self._raw.read_all(raw_name))
            except Exception:
                pass
        try:
            with open(full, "rb") as f:
                return f.read()
        except Exception:
            return None

    # ════════════════════════════════════════════════════════
    #  串流讀取 API (begin_read / read_into / seek / tell / end_read)
    #  行為類似 file object，內部根據路徑和模式自動路由。
    # ════════════════════════════════════════════════════════

    def begin_read(self, path):
        """開始串流讀取。回傳總位元組數，0 表示失敗。"""
        self._end_read()
        kind, full, raw_name = self.resolve(path)

        if kind == "ram":
            data = self._ram.get(full)
            if data is None:
                return 0
            self._str_kind = "ram"
            self._str_data = data
            self._str_pos = 0
            return len(data)

        if self._raw_mode and self._raw is not None and raw_name:
            try:
                size = self._raw.read_begin(raw_name)
                self._str_kind = "raw"
                return size
            except Exception:
                pass

        try:
            f = open(full, "rb")
            self._str_kind = "fat"
            self._str_fp = f
            try:
                st = os.stat(full)
                return st[6]
            except Exception:
                return 0
        except Exception:
            return 0

    def read_into(self, buf):
        """讀取下一塊資料到 buf。回傳位元組數，0 表示結束。"""
        k = self._str_kind
        if k == "ram":
            data = self._str_data
            pos = self._str_pos
            if pos >= len(data):
                return 0
            n = min(len(buf), len(data) - pos)
            buf[:n] = data[pos:pos + n]
            self._str_pos = pos + n
            return n
        if k == "raw":
            return self._raw.read_into(buf)
        if k == "fat":
            return self._str_fp.readinto(buf)
        return 0

    def seek(self, offset):
        """設定讀取位置 (類似 file.seek)。"""
        k = self._str_kind
        if k == "ram":
            if offset < 0:
                offset = 0
            if offset > len(self._str_data):
                offset = len(self._str_data)
            self._str_pos = offset
        elif k == "raw":
            self._raw.seek(offset)
        elif k == "fat":
            self._str_fp.seek(offset)

    def tell(self):
        """回傳目前讀取位置 (類似 file.tell)。"""
        k = self._str_kind
        if k == "ram":
            return self._str_pos
        if k == "raw":
            return self._raw.tell()
        if k == "fat":
            return self._str_fp.tell()
        return 0

    def end_read(self):
        """結束串流讀取，釋放資源。"""
        self._end_read()

    def _end_read(self):
        k = self._str_kind
        if k == "raw":
            try:
                self._raw.read_end()
            except Exception:
                pass
        elif k == "fat" and hasattr(self, "_str_fp"):
            try:
                self._str_fp.close()
            except Exception:
                pass
        self._str_kind = None

    def open_read(self, path):
        """回傳可讀的 file-like 物件供串流讀取；RAM 則回 BytesIO。
        大檔串流建議使用 begin_read / read_into / seek / tell / end_read。
        """
        kind, full, raw_name = self.resolve(path)
        if kind == "ram":
            data = self._ram.get(full)
            if data is None:
                return None
            import io
            return io.BytesIO(data)
        try:
            return open(full, "rb")
        except Exception:
            return None

    def exists(self, path):
        kind, full, raw_name = self.resolve(path)
        if kind == "ram":
            return full in self._ram
        if self._raw_mode and self._raw is not None and raw_name:
            try:
                if self._raw._alloc.find(raw_name) is not None:
                    return True
            except Exception:
                pass
        try:
            os.stat(full)
            return True
        except Exception:
            return False

    def list(self, folder="/sd"):
        kind, full, raw_name = self.resolve(folder)
        if kind == "ram":
            prefix = full.rstrip("/") + "/"
            return [k for k in self._ram if k.startswith(prefix) or k == full]
        try:
            return [full.rstrip("/") + "/" + n for n in os.listdir(full)]
        except Exception:
            return []

    def remove(self, path):
        """統一刪除：RAM / SD-raw / FAT 各自更新 table。"""
        kind, full, raw_name = self.resolve(path)
        if kind == "ram":
            self._ram.pop(full, None)
            return True
        ok = False
        if self._raw_mode and self._raw is not None and raw_name:
            try:
                if self._raw._alloc.find(raw_name) is not None:
                    self._raw.remove(raw_name)
                    ok = True
            except Exception:
                pass
        if self.delete_file(full):
            ok = True
        return ok

    # ==================== Other Operations ====================

    def delete_file(self, path):
        try:
            st = os.stat(path)
            mode = st[0]
            if (mode & 0o170000) == 0o040000: # Directory
                os.rmdir(path)
                self.remove_manifest_entry(path)
                print(f"🗑️ [FS] Dir removed: {path}")
            else: # File
                os.remove(path)
                self.remove_manifest_entry(path)
                print(f"🗑️ [FS] File removed: {path}")
            return True
        except Exception as e:
            print(f"⚠️ [FS] Delete failed: {e}")
            return False
            
    def calc_sha256(self, path):
        """Helper for external use"""
        try:
            h = hashlib.sha256()
            buf = bytearray(2048)
            with open(path, "rb") as f:
                while True:
                    n = f.readinto(buf)
                    if n == 0: break
                    h.update(memoryview(buf)[:n])
            return ubinascii.hexlify(h.digest()).decode()
        except:
            return None

    def scan_all(self):
        """
        Request background scan (set flag for Core 1)
        """
        if self.scanning: return
        from lib.sys_bus import bus
        from lib.log_service import get_log
        get_log().info("FS Scan requested (Queued for Core 1)")
        bus.shared["fs_scan_requested"] = True

    def scan_init(self):
        """
        Phase 0: collect all file paths (ilistdir only, no hashing).
        Called by Core 1 FsScanTask.
        Respects config.json scan_ignore paths.
        """
        ignore_prefixes = self._load_scan_ignore()
        file_list = []
        def _collect(dir_path):
            try:
                for entry in os.ilistdir(dir_path):
                    name = entry[0]
                    type_ = entry[1]
                    full_path = f"{dir_path}/{name}" if dir_path != "/" else f"/{name}"
                    if name == "manifest.json": continue
                    if name.endswith(".tmp"): continue
                    if name.endswith(".db"): continue
                    if self._is_ignored(full_path, ignore_prefixes):
                        continue
                    if type_ == 0x4000:
                        _collect(full_path)
                    else:
                        file_list.append(full_path)
            except Exception as e:
                get_log().error("Scan collect error {}: {}".format(dir_path, e))
        _collect("/")

        self.scanning = True
        self._scan_files = file_list
        self._scan_manifest = {}
        self._scan_idx = 0

        from lib.sys_bus import bus
        from lib.log_service import get_log
        bus.shared["fs_scan_total"] = len(file_list)
        bus.shared["fs_scan_progress"] = 0
        get_log().set_metric("fs_scan_total", len(file_list))
        get_log().set_metric("fs_scan_progress", 0)
        get_log().info("FS Scan phase 1: {} files to hash (Core 1)".format(len(file_list)))

    def scan_step(self):
        """
        Phase 1: hash the next file. Returns True when all done.
        Hashes the entire file in one call (no chunking needed during boot).
        Yields every 256KB to keep interrupts responsive.
        """
        from lib.sys_bus import bus
        from lib.log_service import get_log

        if not self.scanning or self._scan_idx >= len(self._scan_files):
            bus.shared["fs_scan_result"] = self._scan_manifest
            bus.shared["fs_scan_done"] = True
            get_log().set_metric("fs_scan_done", 1)
            self.scanning = False
            total = len(self._scan_files)
            get_log().info("FS Scan complete (Core 1). Found {} files. Handing over to Core 0...".format(total))
            return True

        path = self._scan_files[self._scan_idx]
        self._scan_idx += 1
        bus.shared["fs_scan_current"] = path

        # Fast-path abort check between files
        if not bus.shared.get("engine_run", True):
            self.scanning = False
            get_log().warn("FS Scan aborted by Core 0")
            return False

        try:
            h = hashlib.sha256()
            buf = bytearray(2048)
            size = 0
            chunk_since_yield = 0
            with open(path, "rb") as f:
                while True:
                    n = f.readinto(buf)
                    if n == 0:
                        break
                    h.update(memoryview(buf)[:n])
                    size += n
                    chunk_since_yield += n
                    if chunk_since_yield >= 262144:
                        time.sleep_ms(0)
                        chunk_since_yield = 0
                        if not bus.shared.get("engine_run", True):
                            self.scanning = False
                            get_log().warn("FS Scan aborted by Core 0")
                            return False
            sha = ubinascii.hexlify(h.digest()).decode()
            self._scan_manifest[path] = {"s": size, "h": sha}
        except Exception as e:
            get_log().error("Scan error {}: {}".format(path, e))

        bus.shared["fs_scan_progress"] = self._scan_idx
        get_log().set_metric("fs_scan_progress", self._scan_idx)
        return False

    def finalize_scan(self):
        """Called by Core 0 to save the manifest"""
        from lib.sys_bus import bus
        from lib.log_service import get_log
        if not bus.shared.get("fs_scan_done"): return

        new_manifest = bus.shared.get("fs_scan_result")
        if not new_manifest:
            bus.shared["fs_scan_done"] = False
            bus.shared["fs_scan_result"] = None
            get_log().set_metric("fs_scan_done", 0)
            return

        self.manifest = new_manifest
        self.save_manifest()

        bus.shared["fs_scan_done"] = False
        bus.shared["fs_scan_result"] = None
        get_log().set_metric("fs_scan_done", 0)
        get_log().info("FS Manifest saved by Core 0 ({} entries).".format(len(self.manifest)))

# Singleton Instance
fs = FileSystemManager()