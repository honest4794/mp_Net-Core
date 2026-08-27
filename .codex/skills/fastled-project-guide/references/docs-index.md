# 文件索引

這份索引用來快速決定要讀哪份 reference。`references/docs/` 保存高頻核心文件；完整、最新的功能分類以 repo 的 `docs/README.md` 為準。

## 專案總覽

- `README.md`：專案背景、PlatformIO 使用方式、master/slave 基本概念、設定 checklist。
- 開始修改前先判斷 project 是 `master-slave` 還是 `slave_standalone`；前者使用 transport/routing，後者直接以已配置的 `slaveId` 執行正式 StoryMode。
- `docs/project/workflows/project_workflow_debugging.md`：debug 工作流程、建議檢查順序。
- `docs/firmware_debug_playbook.md`：standalone WiFi AP、good/bad commit A/B、ESP/PCA channel backend、ColorPicker web 同步與 commit hygiene。
- `project-automation-rules` skill：新 project 開始前必讀；確認 slave definition / grouping、storyMode regrouping SOP、RGB1-RGB4 常用效果與 call example。
- `docs/project/workflows/session_prompts.md`：常用 session prompt 與工作提示。

## Story Mode / 燈效

- `docs/storymode/storymode目錄.md`：story mode 清單、名稱、時長。
- `docs/storymode_plasma_standalone_lessons.md`：Plasma 五階段定案、跨 slave group、standalone demo 測試入口、PCA effect payload 與本次常見誤解。
- `docs/storymode/storymode製作標準.md`：story mode 製作流程、timeslot / description / effect name 分工。
- `docs/project/standards/uniform_coding_style.md`：story mode / effect / motor 程式碼風格，包含累積時間門檻規則。
- `docs/ota_wifi/standalone_wifi_heap_debug.md`：改 shared/storymode/patterns 或 standalone WiFi 問題前必讀；static RAM 預算（standalone RAM% ≤ ~76%）、heap 耗盡症狀、lazy state pool 模式。
- `project-automation-rules` skill：storyMode project SOP，包含目前專案 `slave 1-20` 定義、Slave 19／20 左右腳掌、case 排序與 RGB1-RGB4 常用效果。
- `docs/virtual_strip_connector.md`：cross-slave / cross-RGB virtual strip connector，說明 `Slave 7 RGB1 -> Slave 6 RGB1` 這類接線順序如何變成 future cross-effects 的 virtual LED index。
- `docs/storymode/effects/rgb_effect_authoring_standard.md`：RGB effect 撰寫與轉換標準，包含 universal params、submenu params、context、ColorPicker 同步與 storyMode call 規則。
- `docs/storymode/effects/dream_factory_storymode_demo_wled_effects.md`：Dream Factory `storyMode_demo` 最終版實際使用的 19 款 WLED 1D 效果與 RGB group。
- `docs/storymode/effects/audio_reactive.md`：I2S mic、MP3、Audio Active、VU pattern 與音訊排查。
- `docs/storymode/slave_rgb_effects_by_storymode.md`：不同 slave 在 story mode 中的 RGB 效果對照。
- `docs/motor/servo_storymode.md`：servo story mode 組與 LED story mode 的切換。
- `docs/motor/motor_servo.md`：motor、servo、PWM、PCA9685、LEDC 資源限制。
- `docs/motor/uart_dc_motor_gpio17_agent_handoff.md`：GPIO17 → ATtiny412 TX-only motor、Direction A/B、pattern、ColorPicker live control 與 STOP safety。

## 通訊協議

- `docs/communication/master_slave/slave_routing.md`：master 到 slave 的 routing、I2C／RS485 指令分派、slave ID 對應。
- `docs/communication/master_slave/協議規格_slaveUART.md`：Master↔Slave I2C／RS485 middleware、GPIO14/15/16、half-duplex frame、clock sync、狀態輪詢、OTA queue 與三板實測方式。
- `docs/communication/external_uart/協議規格_timerUART.md`：timer screen UART 協議、story mode 時長同步。
- `docs/communication/external_uart/協議規格_videoUART.md`：video UART 協議、影片控制訊號。
- `docs/colorpicker/touch_lcd/協議規格_touchLCD_colorpickerUART.md`：7 寸 ESP32-S3 觸控螢幕 / other mon 透過 master UART GPIO 5/6 傳 ASCII ColorPicker 指令。

## WiFi / OTA

- `docs/ota_wifi/wifi_update.md`：master WiFi 更新 UI、LittleFS、OTA/web update。
- `docs/colorpicker/color_picker.md`：ColorPicker 入口、standalone 本機 AP、VU 測試、uploadfs 與常見排查。
- `docs/colorpicker/sequencer.md`：ColorPicker timeline 的 SEQV1 runtime 格式、LittleFS slot 與 `/api/seq/*` 端點。
- `docs/firmware_debug_playbook.md`：standalone AP 無法 join、open AP 對照測試、WiFi 與 LED/PWM 記憶體變因排查。
- `docs/ota_wifi/ota_invalid_state_fix.md`：OTA invalid state 問題與修正方向。
- `docs/ota_wifi/batch_ota_plan.md`：批次 OTA 計畫。

## 歷史計畫 / 規格

- `docs/project/merge_hiNu_gundam_v7.md`：Hi-Nu Gundam v7 合併紀錄。
- `docs/superpowers/specs/2026-06-01-colorpicker-pwa-design.md`：colorpicker PWA 設計規格。
- `docs/superpowers/plans/2026-06-01-colorpicker-pwa.md`：colorpicker PWA 實作計畫。
- `docs/superpowers/specs/2026-06-16-storyMode-motor-reset-design.md`：storyMode motor reset 設計規格。
- `docs/superpowers/plans/2026-06-16-storyMode-motor-reset.md`：storyMode motor reset 實作計畫。

## 其他

- `docs/runStoryModeAll_timeslot.html`：story mode timeslot HTML 參考。
