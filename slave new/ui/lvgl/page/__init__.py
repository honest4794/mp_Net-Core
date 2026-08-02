# ui/lvgl/page/__init__.py — 集中 import 所有頁面（保證全部 @register + declare）
#
# 新增頁面流程:
#   1. 建立 ui/lvgl/page/xxx.py,在 build() 前加 @register(id="xxx", ...),
#      在 build() 內用 ui_common.begin_page()/declare() 宣告 widget。
#   2. 在下面 import 與「補 mod」清單各加一行。
# 動態 launcher 會自動出現該頁面,不需改其他檔。
#
# 集中 import 是為了性能:MPY 無法可靠跑 os.listdir 動態載入,
# 且凍結/複製時要有明確 import 才保證每頁都註冊。
# 「補 mod」是把頁面模組引用存進註冊表,app 才能呼叫 on_enc/on_confirm 等。
from ui.lvgl import registry
from ui.lvgl.page import control_panel, mon_time, pca9685, settings

registry.PAGES["control_panel"]["mod"] = control_panel
registry.PAGES["mon_time"]["mod"] = mon_time
registry.PAGES["pca9685"]["mod"] = pca9685
registry.PAGES["settings"]["mod"] = settings
