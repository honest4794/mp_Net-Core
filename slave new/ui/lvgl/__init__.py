# ui/lvgl/ — LVGL 本地 UI 套件
#
# 入口:ui.lvgl.board.run()(受 config System.lcd_mode 閘門)
#      或 ui_test_tool.start()(獨立測試,不受閘門)
#
# 架構(對齊 mp_LVGL/ui 參考版 + slave new config 驅動):
#   lvgl_init.py   LVGL display 一次初始化 + bus reuse(對齊 i80_drv/tft_drv)
#                  W/H 從 bus.shared["tft_width"]/["tft_height"] 讀,不寫死
#                  不碰 MADCTL(driver init_tft 已依 config rotation 設好)
#   ui_common.py   palette/字型/widget builder(移植自參考版,修字型路徑)
#   registry.py    @register 動態註冊
#   app.py         平台解耦路由器(reuse 模式:預建 screen,widget 永駐)
#   launcher.py    動態首頁
#   board.py       板上對接層(lcd_mode 閘門 + confirm + 主迴圈)
#   page/          頁面模組(每頁 @register,update() 自己讀 bus)
#   src/           資源(字型 .bin / icon 模組 / 動效)
