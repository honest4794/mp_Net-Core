# ui/lvgl/app.py — 動態註冊式 UI 主程式
#
# 生命週期(修掉「進出頁面幾次就 reboot」的 heap 累積):
#   go(name): on_leave 舊頁 → 全新 build 新頁 screen → screen_load →
#             刪除舊 screen(釋放全部子物件) → on_enter 新頁
# 每次進入都重建,不沿用舊實例 → 記憶體乾淨。
#
# 平台解耦:所有硬體透過 platform 物件注入,本檔不 import 任何硬體。
#   板上: ui/lvgl/board.py 用 slave new bus 組 platform
#   模擬器: 直接 import app(平級) 或 ui.lvgl.app(package) 皆可(見下方相容 import)
import lvgl as lv
try:
    import ui.lvgl.registry as registry
    import ui.lvgl.launcher as launcher
except ImportError:
    # 模擬器 wasm importer 不支援 package 目錄 → 平級 import
    import registry
    import launcher

platform = None      # {tick, take, show, enc_delta, confirm, exit}
cur = None
_last_scr = None
_run = 0
_reuse = False       # True = 沿用預建 screen(扁平模式,widget 永駐)
_screens = {}        # page_id → 預建 screen(reuse 模式)


def init(plat, reuse=False):
    """注入 platform 物件 + 載入所有頁面(集中 import 已註冊)。
    reuse=True:啟動時全部 build 一次、widget 永駐、go() 沿用(對齊扁平版設計,
    省 rebuild、避免 widget 生命週期問題)。"""
    global platform, _reuse
    platform = plat
    _reuse = reuse


def build_all():
    """預建所有頁面 screen(reuse 模式用)。build 後 declare 已全部到位,
    可供 ui_space.alloc_from_decl() 配置正確額度的 buffer。
    必須在 alloc_from_decl() 之前、page import 之後呼叫。
    不檢查 _reuse flag(呼叫者決定要不要預建),go() 才依 _reuse 決定是否沿用。"""
    global _screens
    _screens = {"launcher": launcher.build()}
    for pid in registry.PAGES:
        _screens[pid] = registry.PAGES[pid]["build"]()
    print("[app] build_all: {} screen(s) pre-built".format(len(_screens)))


def _page():
    """目前頁面模組(launcher 或註冊頁面),沒有就回 launcher。"""
    if cur == "launcher":
        return launcher
    meta = registry.get(cur)
    if meta is not None:
        return meta.get("mod")
    return launcher


def go(name, back=False):
    """切換頁面。
    reuse 模式:沿用預建 screen(扁平模式,widget 永駐,不 rebuild 不刪屏)。
    非 reuse:每次重建 screen + 刪舊屏(rebuild-on-navigate,省 heap)。"""
    global cur, _last_scr
    if name == cur:
        return
    if name != "launcher" and name not in registry.PAGES:
        return

    # 1. 離開舊頁(清編輯狀態等)
    old = _page()
    if hasattr(old, "on_leave"):
        old.on_leave()

    # 2. 取得新頁 screen
    if _reuse:
        # 沿用預建 screen(build_all 時已建好)
        scr = _screens.get(name)
        if scr is None:
            return
    else:
        # 全新 build(不沿用舊實例)
        if name == "launcher":
            scr = launcher.build()
        else:
            scr = registry.get(name)["build"]()

    # 3. 載入
    try:
        lv.screen_load(scr)
    except Exception:
        pass

    # 4. 非 reuse 模式才刪舊屏(reuse 模式 screen 要保留供下次用)
    if not _reuse and _last_scr is not None:
        try:
            _last_scr.delete()
        except Exception:
            pass
    _last_scr = scr

    cur = name
    print("[nav] ->", name)
    new = _page()
    if hasattr(new, "on_enter"):
        new.on_enter()


def run():
    """主迴圈(啟動後不返回)。板上用。"""
    while True:
        step()
        _sleep(5)


def _sleep(ms):
    try:
        import time
        time.sleep_ms(ms)
    except Exception:
        pass


def step():
    """單幀處理(模擬器事件驅動用)。回傳 1 表示處理了一幀。"""
    global _run
    d = platform["enc_delta"]()
    c = platform["confirm"]()
    ex = platform["exit"]()
    m = _page()

    if d != 0 and hasattr(m, "on_enc"):
        m.on_enc(d)
    if c and hasattr(m, "on_confirm"):
        target = m.on_confirm()
        if target:
            go(target)
    if ex and cur != "launcher":
        go("launcher", back=True)

    if hasattr(m, "update"):
        m.update(_run)
    _run += 1

    platform["tick"]()
    for rect in platform["take"]():
        platform["show"](*rect)
    return 1
