---
name: fastled-project-guide
description: Use when working in this FastLED ESP32-S3 firmware project, especially for PlatformIO builds, master/slave routing, story mode, timer/video UART, WiFi OTA update, motor/servo/PCA9685 hardware, or onboarding new contributors. Combines README.md and docs/ into skill references with beginner-friendly Traditional Chinese guidance.
---

# FastLED Project Guide

本 skill 是本專案文件入口。回覆使用者時使用繁體中文，盡量簡潔。

## 新手解釋方式

所有使用者的概念說明都預設使用 Feynman Technique（費曼技巧），用最簡單繁體中文說明；除非使用者明確要求深入技術細節，否則不要先用複雜術語。若問題牽涉 master/slave/story mode/PWM/motor 基礎，先讀 `references/newbie-concepts.md`。

- 先用一句話講核心概念。
- 不先丟術語；必要術語要馬上用白話解釋。
- 用一個小例子說明，例如「Master 是總指揮，Slave 是執行者」。
- 最後連回實際檔案、函式或硬體。
- 不寫長篇教科書，用短段落與少量 bullet。

## 先讀哪裡

- 新手或需要概念說明：讀 `references/newbie-concepts.md`。
- 一般專案背景：讀 `references/README.md`。
- 要找文件位置：讀 `references/docs-index.md`。
- 動 StoryMode／effect 前：先判斷 project 是 `master-slave` 還是 `slave_standalone`；再依 topology 選 routing 與測試入口。
- 開始新 project 或從舊 branch 取回 storyMode code：使用獨立 `project-automation-rules` skill，第一步確認 slave definition / grouping 與 RGB1-RGB4 storyMode SOP。
- 修改 story mode / effect / motor：讀 `references/docs/storymode/storymode製作標準.md`、`references/docs/project/standards/uniform_coding_style.md`、`references/docs/storymode/effects/rgb_effect_authoring_standard.md`、`references/docs/motor/motor_servo.md`、`references/docs/motor/servo_storymode.md`。
- 修改 cross-slave RGB / virtual strip / RGBSeqOnV3 / 跨 RGB 燈效：讀 `references/docs/virtual_strip_connector.md`。
- 修改 master/slave routing 或 I2C：讀 `references/docs/communication/master_slave/slave_routing.md`。
- 修改 GPIO14/15/16 RS485 middleware、clock sync、status 或 RS485 OTA queue：讀 `references/docs/communication/master_slave/協議規格_slaveUART.md`。
- 修改 GPIO17 → ATtiny412 motor、Direction A/B、pattern 或 ColorPicker motor live control：讀 `references/docs/motor/uart_dc_motor_gpio17_agent_handoff.md`。
- 修改 timer 或 video UART：讀 `references/docs/communication/external_uart/協議規格_timerUART.md` 或 `references/docs/communication/external_uart/協議規格_videoUART.md`。
- 修改 WiFi / OTA / web update：讀 `references/docs/ota_wifi/wifi_update.md`、`references/docs/ota_wifi/ota_invalid_state_fix.md`、`references/docs/ota_wifi/batch_ota_plan.md`。
- Debug workflow：讀 `references/docs/project/workflows/project_workflow_debugging.md`。
- Debug standalone WiFi AP、good/bad commit、ESP/PCA channel、ColorPicker web 同步：讀 `references/docs/firmware_debug_playbook.md`。
- 用 `storyMode_demo` 做 standalone RGB/PCA 硬體測試：讀 `references/docs/storymode/storymode目錄.md` 的 demo 測試入口；保留 standalone timer/輪播程式。
- 微調 Plasma stage、跨 slave group、雷電節奏，或排查 standalone demo/PCA effect：讀 `references/docs/storymode_plasma_standalone_lessons.md`。

## 必守工程規則

- 只用 PlatformIO，不支援 Arduino IDE。
- shared code 會同時影響 master、slave、standalone；改 shared 前要想清楚影響範圍。
- 不要隨便改 I2C address、slave ID、GPIO、PWM channel、LED 數量、story mode 總秒數。
- `platformio.ini` 是共用設定；`platformio_local.ini` 是本機硬體設定。
- 修改 story mode、RGB、PWM、motor 時，每個實際呼叫前要有硬體註解。
- 新 project 第一件事是確認 slave definition / grouping；不要沿用舊 project 的 weapons/platform/backpack 分組。
- Story mode 效果直接寫在對應 `case slaveId`，不要新增只包效果的 helper / macro / lambda。
- 新增或修改 RGB effect / cross-effect 前，必須遵守 `rgb_effect_authoring_standard.md`：呼叫端像接線表、少 helper、少 wrapper、cross-slave 用 `RgbVirtualSlaveGroup` 表達同步與連接。
- Cross-slave RGB / virtual strip 修改前，必須遵守 `virtual_strip_connector.md`：不要新增 `RgbVirtualStrip` 物件，不用特殊值隱藏同步語意，不用多層 `make/total/clear/directed` helper。
- 多段 stage 要用累積門檻，例如 `if (time >= 0)`、`if (time >= 2000)`，不要用 close gate 讓前段效果停止。
- 同一 slave stage 內，先寫 `espMotor` buffer，再寫 RGB / PCA base effects。
- 遇到「某 commit 可用、目前不可用」時，先做 good/bad commit A/B，不要先猜 root cause。
- UI/API 有 channel 名稱不代表 firmware backend 已支援；新增 espLed / espMotor / pcaLed / pcaMotor 必須同步 config accessor、channel map、attach/write、JSON state 與 web UI。
- 修改 ColorPicker web 時，要確認 source/partial 與 generated `web/colorpicker.html` 的同步策略，避免下次生成覆蓋修改。
- `platformio_local.ini` 是本機硬體設定；除非使用者明確要求，不要把硬體測試 flag 和功能 commit 綁在一起。
- 獨立 standalone project 可直接用已配置的 `slaveId` 執行正式 StoryMode；只保留 standalone target 所需路徑，不用 macro／wrapper 建另一套 timeslot。

## 驗證

- shared code 有變更時，至少跑：

```bash
arch -arm64 pio run -e master -e slave1 -e slave_standalone
```

- 可行時也跑相關 Python static tests。
