# Codex 專案規則

請用繁體中文回應一切對答。盡量簡潔、精準,除非要你解釋，否則不要長篇大論。


## 對話啟動

每次新對話開始時，先讀取 `.codex/skills/fastled-project-guide/SKILL.md`、`.codex/skills/fastled-project-guide/references/docs-index.md` 與本文件的「文件索引」。再依任務範圍讀取 skill references 中的相關文件；若任務跨系統、影響 shared code、協議或硬體設定，才讀取 `.codex/skills/fastled-project-guide/references/docs/**/*.md`。若存在 `doc/` 目錄，依同樣規則讀取其中的 Markdown 檔案。

所有 agent 必須把本 repo 的 `.codex/skills/*/SKILL.md` 全部視為團隊可用 skills，依 skill description 與任務觸發規則選用。使用 repo 相對路徑解析，不可寫死 `/Users/all.are.mathematics/...` 等個人電腦絕對路徑；這樣隊友 clone 或 pull 後，會直接取得同一套 project skills。

Claude Code skills 直接保存在 `.claude/<skill-name>/`，不可放進 `.claude/skills/`。若需要 user scope，執行 `./scripts/install_claude_skills.sh` 同步至 `~/.claude/<skill-name>/`；隊友 clone 或 pull 後使用相同指令。

所有使用者的概念說明都預設使用 Feynman Technique（費曼技巧），用最簡單繁體中文說明；除非使用者明確要求深入技術細節，否則不要先用複雜術語。若問題牽涉 master/slave/story mode/PWM/motor 基礎，先讀 `.codex/skills/fastled-project-guide/references/newbie-concepts.md`。

- 先用一句話講核心概念，像在教第一次接觸的人。
- 避免先丟術語；必要術語要立刻用白話解釋。
- 用一個很小的例子或比喻說明，例如「Master 是總指揮，Slave 是執行者」。
- 說明完後回到實際檔案、函式或硬體，讓使用者知道這個概念在專案哪裡出現。
- 不要長篇教科書式解釋；用短段落、少量 bullet，確保對方能馬上用。

修改 story mode、燈效、PWM、motor 或 `firmware/shared/src/storymode` 時，先讀 `.codex/skills/storymode-coding-style/SKILL.md`。

## 文件索引

依任務範圍先讀取對應文件：

- `.codex/skills/fastled-project-guide/references/README.md`：專案總覽、基本使用方式與主要背景。
- `.codex/skills/fastled-project-guide/references/newbie-concepts.md`：新手概念，master/slave/story mode/RGB/PWM/motor 最簡單說明。
- `.codex/skills/fastled-project-guide/references/docs/ota_wifi/wifi_update.md`：master WiFi 更新 UI、LittleFS、OTA/web update 流程。
- `.codex/skills/fastled-project-guide/references/docs/colorpicker/color_picker.md`：ColorPicker 入口、standalone 本機 AP、VU 測試、uploadfs 與常見排查。
- `.codex/skills/fastled-project-guide/references/docs/communication/master_slave/slave_routing.md`：master 到 slave 的 routing、I2C 指令分派、slave ID 對應。
- `.codex/skills/fastled-project-guide/references/docs/communication/external_uart/協議規格_timerUART.md`：timer screen UART 協議、story mode 時長同步、timer 端資料格式。
- `.codex/skills/fastled-project-guide/references/docs/communication/external_uart/協議規格_videoUART.md`：video UART 協議、影片控制訊號與 payload 格式。
- `.codex/skills/fastled-project-guide/references/docs/storymode/storymode目錄.md`：story mode 清單、模式註冊、燈效行為與時長。
- `.codex/skills/fastled-project-guide/references/docs/storymode_plasma_standalone_lessons.md`：Plasma 五階段、跨 slave group、standalone demo 測試入口、PCA effect payload 與常見誤解。
- `.codex/skills/fastled-project-guide/references/docs/storymode/storymode製作標準.md`：story mode 製作 workflow、文件標準、general name / effect name 拆分、timeslot 描述規則。
- `.codex/skills/fastled-project-guide/references/docs/storymode/effects/audio_reactive.md`：I2S mic、MP3、Audio Active、VU pattern 與音訊排查。
- `.codex/skills/fastled-project-guide/references/docs/motor/servo_storymode.md`：servo storymode 組、與 LED 組的切換（Timer bit6）、新增 servo 模式的方式。
- `.codex/skills/fastled-project-guide/references/docs/motor/motor_servo.md`：馬達、servo、PWM、PCA9685 與 LEDC 資源限制。
- `.codex/skills/fastled-project-guide/references/docs/project/standards/uniform_coding_style.md`：agent 生成或修改 story mode、燈效、lib/patterns 程式碼時必讀的統一 coding style。
- `.codex/skills/fastled-project-guide/references/docs/ota_wifi/standalone_wifi_heap_debug.md`：**改 shared/storymode/patterns 或處理 standalone WiFi 問題前必讀**。static RAM 預算（standalone RAM% 不得超過 ~76%）、heap 耗盡症狀、lazy state pool 模式、診斷 log 用法。

## 專案背景

這是一個 ESP32-S3 韌體專案，用於基於 FastLED 的燈光控制。專案只使用 PlatformIO。

韌體有三種主要模式：

- `master`：協調整個系統、WiFi 更新 UI、timer/video UART，以及送往 slave 的 I2C 指令。
- `slave1` 到 `slave7`：接收 master 指令，並執行燈光、PWM、馬達與 OTA 接收端行為。
- `slave_standalone`：在沒有 master 的情況下執行 slave 韌體，用於單晶片安裝。

`firmware/shared` 下的共用程式碼會同時編入 master 與 slave 建置。除非已證明不會影響其他環境，否則 shared 變更都應視為跨環境變更。

## 重要檔案

- `platformio.ini`：共用 PlatformIO 環境與基礎編譯旗標。
- `platformio_local.ini`：本機硬體設定、上傳連接埠、story mode 時長、LED 數量與啟用裝置。不要假設這裡的值可攜到其他機器或安裝環境。
- `firmware/master/src/main.cpp`：master 韌體進入點。
- `firmware/slave/src/main_slave.cpp`：slave 與 standalone 韌體進入點。
- `firmware/master/include/config.h` 與 `firmware/slave/include/config.h`：編譯期設定合約。
- `firmware/shared/include` 與 `firmware/shared/src`：多個韌體目標共用的程式碼。
- `firmware/shared/src/storymode` 與 `firmware/shared/src/patterns`：燈光行為與可重用 pattern 邏輯。
- `docs/`：協議與硬體行為說明。修改 UART、I2C、routing、motor/servo、WiFi update 或 story mode 行為前，先閱讀相關文件；修改 story mode、燈效、`lib/` 或 `patterns/` 前，必須閱讀 `docs/storymode/storymode製作標準.md` 與 `docs/project/standards/uniform_coding_style.md`。
- `.codex/skills/fastled-project-guide/`：整合 `README.md` 與 `docs/` 的 Codex skill；新對話優先用這裡的 references 做專案索引。
- `.codex/skills/storymode-coding-style/`：修改 story mode、燈效、PWM、motor 前必讀的 Codex skill。
- `.codex/prompts/`：團隊共用的 Codex prompt 原始檔；隊友 pull 後執行 `./scripts/install_codex_prompts.sh`，重新啟動 Codex，即可使用 `/prompts:fable-mode`。

## 編輯規則

- 先衡量變更規模。小型變更（例如暫時註解／恢復陣列項目、單一設定切換、文字或註解修正）不需要先寫 plan、design spec 或新增測試程式；可直接修改，再做基本 diff／語法檢查。
- 若變更跨系統、影響 shared API／協議／硬體設定／記憶體配置、修改實際燈效或時序邏輯，仍應先規劃並執行相稱的建置或測試。
- 變更範圍應限於使用者要求的韌體模式與受影響子系統。
- 編輯 shared 程式碼前，先確認變更是否會影響 master、slave 與 standalone 建置。
- 優先沿用既有專案模式，不要新增不必要的抽象。這是硬體導向的程式碼；小而明確的寫法通常比聰明的間接層更好。
- 不要隨意更改 I2C 位址、slave ID、GPIO 腳位、PWM channel 數量、LED strip 數量、story mode 時長、partition 設定、上傳連接埠或 FastLED driver 旗標。
- 保留 `platformio.ini` 中的設定與 `platformio_local.ini` 中本機安裝值之間的區別。
- 產生或更新給使用者閱讀的 Markdown、HTML 與 PDF 文件時，內文必須使用繁體中文；必要的程式碼符號、檔名、函式名與編譯旗標可保留原文。
- 使用 `storyMode_demo` 做 standalone 硬體測試時，保留 `runStandaloneLoop()` 的 timer、timeout 與模式輪播程式；只在 `ledController.cpp::runPattern()` 的既有 `STANDALONE_MODE` demo test block 暫時啟用 `runStoryModeDemo(); return;`，測完重新註解。
- `storyMode_demo()` 測試入口不加入無用途的 `slaveId`，也不為此改動正式 `storyModes` array。
- Arduino `String` 串接 `uint8_t` channel/effect 時使用 `String(value)` 明確轉為數字，避免 `LC:pwm` payload 變成控制字元。

## 設定安全

- Slave I2C 位址必須從 `0x10` 開始並依序遞增，除非使用者明確要求不同的接線配置。
- `SLAVE_ID` 在所有啟用的 slave 環境中必須保持唯一。
- ESP32 native LEDC 資源由 native motor PWM 與 native LED PWM 共用。保持 `MOTOR_NUM_ESP + LED_NUM_ESP <= 8`。
- Motor PCA9685 支援假設只有一片 motor PCA 板，最多 16 個 channel。
- LED PCA9685 位址不得與 motor PCA9685 位址衝突。
- Master 與 timer-screen 的 story mode 時長必須保持一致。
- 如果更改協議常數或 payload 格式，必須在同一次變更中更新 `docs/` 內的相關文件。


## 韌體慣例

- 一致使用 `IS_MASTER`、`IS_SLAVE`、`STANDALONE_MODE` 等編譯期旗標，並符合既有環境切分。
- Master-only 程式碼放在 `firmware/master`，slave-only 程式碼放在 `firmware/slave`，真正共用的邏輯放在 `firmware/shared`。
- 新增 story mode 或 pattern 時，需同步更新宣告、定義、註冊/routing 程式碼與文件。
- 新增或重做 story mode 時，文件與簡報應分清楚 timeslot/general description、description、effect name；箭頭流程代表時間段，不應變成 effect name 清單。
- 新增或修改 story mode 內的 RGB / PWM / motor / GPIO 呼叫時，每個實際呼叫前都要加硬體註解；部位名稱與燈珠數優先從 Excel / 接線表複製。
- Story mode 多段時序應使用累積時間門檻，例如 `if (time >= 0)`、`if (time >= 2000)`、`if (time >= 4000)`。除非明確要關閉或 fade out，不要用 `if (time >= a && time < b)` 讓前段效果停止。
- Story mode 效果要直接寫在對應 `case slaveId` block；不要新增 `renderBaseEffects`、lambda、macro 或只包效果的 helper。
- 同一個 slave stage 內，先呼叫會寫 `espMotor` buffer 的 `chServo*` / `chFadeIn` / `chFadeOut` / DC motor 函式，再呼叫該 slave 的 RGB / PCA base effects。
- 不要用 `renderStoryModeInternalStructure(...)` 這類隱藏 channel 的 helper；在 story mode 內直接寫底層 `chInternalStructure(...)` 與所需 state buffer。
- 將 timer UART、video UART、I2C、OTA 與 WiFi update 行為視為外部協議。除非使用者明確要求協議變更，否則維持向後相容。
- 在時序敏感的 LED、PWM、I2C、UART 或 OTA 路徑中，謹慎使用 blocking call、delay、heap allocation 與 logging。
- Debug logging 由編譯旗標控制。避免新增無條件且吵雜的 serial output。

## 完成前

- 可行時，針對已變更環境執行最相關的 `pio run` 指令。
- 如果 shared 韌體有變更，至少建置 master、一個 slave 與 standalone。
