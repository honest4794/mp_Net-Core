# ui/ — slave new 統一 UI 區塊
#
# 兩個子區塊,執行邏輯各自獨立,只是資源歸在同一層:
#   ui/web/   靜態網頁 UI（由 tasks/web_ui.py 的 WebUITask 服務,web_root="ui/web"）
#   ui/lvgl/  LVGL 本地 UI（由 ui.lvgl.board.run() 啟動,跑在 LCD 上）
#
# LVGL 與 web 不耦合;兩者透過 slave new 的 bus 系統與其他模組溝通。
