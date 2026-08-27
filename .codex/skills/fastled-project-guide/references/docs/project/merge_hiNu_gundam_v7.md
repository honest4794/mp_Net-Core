# 合流紀錄：`feat/wifi-update` ← `dev_hiNu_gundam_v7`

**日期：** 2026-06-03
**目標：** 把 production 線（`dev_hiNu_gundam_v7`，實際演出用）併入 dev 線（`feat/wifi-update`，OTA/WiFi/批次更新），收斂分歧、避免長期多版本。
**merge 來源：** `dcdaa5e`（origin/dev_hiNu_gundam_v7 tip）
**dev 基底：** `dd67c8ac`

---

## 解法總原則（HYBRID）

| 類別 | 採用哪邊 |
|------|---------|
| 我們獨有的 OTA / WiFi / 批次更新 / anti-stuck | **ours** |
| production 的硬體 / 燈效 / colorpicker / powerBudget / statusFrame | **theirs** |
| config 巨集**命名**（兩邊不同名、同概念） | **ours**（較精確） |
| standalone 單晶片模式（production 已移除） | **保留 ours** |

---

## 採用 ours（保留我們分支）

| 檔案 | 內容 |
|------|------|
| `firmware/master/src/i2cController.cpp` | OTA INVALID_STATE 復原、`waitForSlaveReady` timeout/零長度放行、anti-stuck（slaveIsBlocking / serviceModeProgressWatchdog / 逾時非消費式 / I2C 框驗證 / COMPLETED 限當前 mode）。**production 沒有這些** |
| `firmware/master/src/otaManager.cpp` | LittleFS OTA 流程（含刻意移除 SPIFFS format-retry） |
| `firmware/master/src/main.cpp` | master loop（inline 重啟 timer，無 scheduledStart） |
| `data/html/slave.html` | batch OTA UI（per-slave 指定 + 依序更新） |
| config 標頭命名 | `LED_PCA_ADDRESS_*`、`MOTOR_NUM_CHANNEL_PCA`、`MAX_LED_NUM_PCA`（canonical） |
| `platformio_local.ini` | 你的機器設定（Kampfer kit） |
| standalone 支援 | `ledController.cpp` / `main_slave.cpp` / `platformio.ini` 的 `STANDALONE_MODE` 分支補回 |
| docs | `docs/ota_wifi/ota_invalid_state_fix.md`、`docs/ota_wifi/batch_ota_plan.md`（我們的）保留 |

---

## 採用 theirs（採 production）

| 檔案 / 模組 | 內容 |
|------------|------|
| `firmware/shared/src/lib/lib_channel.cpp`、`lib_channel.h` | 硬體 channel 層：馬達反轉、ESP LED pins、off=relax（`chOffMotors`=0 duty / `chOriginMotors`=hold） |
| `firmware/shared/include/config/configLed.h`、`pwm/pwmConfig.h` | LED/PWM 硬體設定（命名改回 ours） |
| `firmware/shared/src/storymode/storyMode_0/1/2/3/demo.cpp` + 新增整套 storymode | production 演出燈效 |
| `firmware/shared/src/patterns/*`、`storyMode_struct.*`、`storyMode_parameter.*` 等 | production pattern/struct 框架（`ChBoosterFadeState` 為共用，相容） |
| `firmware/slave/src/i2cController.cpp` | slave I2C 架構：`prebuiltResponse`/`updateI2CResponse`、statusFrame CRC 尾端、colorpicker、powerBudget INFO、06821 時鐘偏移 |
| colorpicker | `master/src/colorpicker.cpp`、`wifi_colorpicker.cpp`、`slave_live_colorpicker.*`、`data/html/picker.html`、`colorpicker.html`、api colorpicker routes |
| `firmware/shared/src/power/powerBudget.cpp`、`statusFrame.h`、`remoteLog.*` | production 新模組 |
| `firmware/shared/src/utils.cpp` | monitorFPS heartbeat（兩邊近似，取 theirs） |
| `platformio.ini` slave3–14 env、i80 patch（`extra_scripts`） | production 多 slave 環境 + i80 io_config patch |
| docs | `AGENTS.md`、`README.md`、`docs/ota_wifi/wifi_update.md`、`docs/motor/motor_servo.md` 等取 production |

---

## 命名調和（production → ours，全域 rename）

production 與 ours 同概念、不同名的巨集，全部改成 ours：

| production 名 | → ours 名 |
|--------------|-----------|
| `PWM_ADDRESS_n` | `LED_PCA_ADDRESS_n` |
| `MOTOR_NUM_PCA` | `MOTOR_NUM_CHANNEL_PCA` |
| `MAX_NUM_PWM` | `MAX_LED_NUM_PCA` |

---

## 補回 / 新增（讓 production 程式碼在 ours 基底編得過）

| 項目 | 處理 |
|------|------|
| `isRepeatMode`（global） | ours 曾移除 → 補回 `globals.cpp`/`globals.h`（production 單台重複模式需要） |
| `runStoryModeSingle()` | 定義已隨 merge 進入；補 `storyModeController.h` 宣告 |
| `MOTOR_REVERSE_0..7` | production 馬達反轉新功能設定 → 加 `#ifndef` 預設 0 到 `configMotor.h` |

---

## 修正 merge 產生的破損（auto-merge artifact）

| 問題 | 修正 |
|------|------|
| `storyModeController.cpp`：`resetModeState()` 與 `runStoryModeSingle()` 被巢狀（auto-merge 殘片） | 移除多餘的 `resetModeState()` 開頭，兩者改回獨立函式 |
| `currentTime` 全域**重複定義**（master/i2cController vs storyMode_parameter） | master 那個改 `static`（master 內未用到） |
| `[env:slave4_base]` build_flags 被 union 弄壞（混入 `STANDALONE_MODE=1` + 重複 `SLAVE_ID`） | 還原成與 slave1/2 一致的乾淨 pattern（code review 抓到） |

---

## 驗證

- `pio run -e master -e slave1 -e slave2 -e slave_standalone` → 全部 **SUCCESS**。
- Code review（subagent）：我們 OTA/WiFi 功能逐 byte 無損、手動解檔正確、無殘留標記、無全域重複定義；唯一 Critical（slave4_base）已修並複驗。

---

## 注意事項 / 待辦

- `platformio_local.ini` 保留**你的機器設定**；要跑 production 的 `slave3–14`，需自行在 `platformio_local.ini` 加對應 concrete env（結構比照 slave1/2）。slave3–14 目前只有 `_base`，無法直接 `pio run`。
- **watchdog 維持 60s**（未採 production 10s）——slave OTA 寫 flash 可能 >10s，過短會誤重啟。
- **i80 patch（`extra_scripts`）已納入**：我們用 I2S driver（`FASTLED_USES_ESP32S3_I2S`），此 patch 對我們無作用但無害。
- 未採用：SPIFFS format-retry（已被 LittleFS 取代）、production 的 watchdog 縮短、settle delay、b2d022 sticky dev mode。
- 實機驗證待進行（OTA + 演出燈效 + colorpicker + 各 slave）。
