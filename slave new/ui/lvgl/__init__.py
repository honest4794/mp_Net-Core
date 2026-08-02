# ui/lvgl/ — LVGL 本地 UI 套件
#
# 移植自 mp_LVGL/tools/design/lvgl-console-ui/lvgl/ui/,import 改用 ui.lvgl.* 命名空間。
# 入口:ui.lvgl.board.run()
#
# 架構:
#   registry.py   @register 裝飾器 + PAGES dict(框架核心)
#   app.py        平台解耦路由器(不 import 任何硬體)
#   launcher.py   動態首頁(讀 registry 產生卡片)
#   ui_common.py  palette/字型/builder + declare/begin_page 控制平面 helper
#   ui_space.py   bus 空間管理(打包陣列 + bit/i32 + sync + describe)
#   board.py      板上對接層(lcd + 輸入 + 每幀 sync)
#   page/         頁面模組(每頁 @register + 宣告 widget)
#   src/          資源(字型 .bin / icon 模組 / 動效)
