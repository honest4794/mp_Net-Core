# 韌體 Debug Playbook

這份文件收集本專案最常重複出現的 debug 流程。核心原則：先縮小變因，再改程式；不要把 WiFi、UI、story mode、硬體 flag 混在同一次測試。

## Good / bad commit A/B

當使用者說「某個 commit 可以、現在不可以」時，該 commit 就是 known-good baseline。

- 先確認目前是不是 dirty worktree；dirty change 可能才是真正測試版本。
- 用 good commit 對照相關檔案，不要先憑記憶猜。
- 優先比較啟動路徑、config flag、記憶體用量、WiFi 初始化、channel 初始化。
- 一次只測一個變因，例如只換 SSID、只關 ESP LED、只改 WiFi AP 模式。
- 不要把「已知可用 commit」和「目前 dirty 檔案」混在同一個結論。

常用檢查方向：

```bash
git status --short
git show <good-commit>:<path>
git diff <good-commit>..HEAD -- <path>
```

## Standalone WiFi AP 不能 join

`WiFi.softAP()` 成功只代表 AP 建起來，不代表手機一定能完成連線。

- Serial log 出現 `Standalone: WiFi AP '<ssid>' IP=192.168.4.1` 代表 AP 已啟動。
- `stations=0` 代表目前沒有 client associate。
- `Disconnected (read failed: [Errno 6] Device not configured)` 通常是 USB serial monitor 斷線重連，不是 WiFi join 失敗本身。
- 先拿 known-good commit 或最小 open WiFi test program 對照，確認硬體與手機可以連。
- 如果 AP 可見但密碼正確仍不能 join，先測 open AP，再測短 SSID，再測固定 channel。
- 如果 DIRAM / heap 非常滿，WiFi AP 可能能啟動但 join 不穩；要把 LED buffer、story mode buffer、web payload 或 debug feature 分開測。
- 不要同時改 SSID、password、`ENABLE_LED_ESP`、story mode、web page，否則無法判斷 root cause。

## ESP / PCA channel backend 同步

UI 出現 `espLed`、`pcaLed`、`espMotor`、`pcaMotor` 不代表 firmware backend 已完整支援。

新增或修正 channel backend 時，至少檢查：

- `platformio.ini` / `platformio_local.ini` 的 enable flag 與 channel 數量。
- config accessor 是否有正確回傳 ESP LED / ESP motor / PCA LED / PCA motor 數量。
- channel map 是否分清楚 `CH_LED_ESP_START`、`CH_MOTOR_ESP_START`、`CH_LED_START`、`CH_MOTOR_PCA_START`。
- ESP LED 是否有 `ledcAttach` 與 `ledcWrite`。
- PCA LED / PCA motor address 是否沒有衝突。
- web state JSON、scan JSON、channel group render、test page UI 是否一起更新。
- `MOTOR_NUM_ESP + LED_NUM_ESP <= 8`，避免 ESP32 LEDC channel 超限。

停用 motor 時要確認 firmware log 顯示 motor channel 數量是 0；UI switch 只能控制顯示或測試，不會憑空建立 backend channel。

## ColorPicker web 同步

`web/colorpicker.html` 常是給裝置直接服務的整合頁，但 tab partial / script source 也可能同時存在。

- 為了快速測試可以改 `web/colorpicker.html`。
- 若變更要保留，必須同步改 source/partial，例如 `web/script.js`、`web/tabs/*.html`。
- 新增 page 或移除 page 時，要同步 nav、tab content、state parser、event binding。
- 新增 channel group 時，要同步 render、test payload、scan display、mode editor tracks。
- 修改 web update / OTA UI 時，要注意 LittleFS upload 內容是否也需要更新。

## Commit / build hygiene

硬體專案最容易出錯的是「功能改動」和「本機硬體設定」被包在同一個 commit。

- Commit 前先看 `git status --short`，確認沒有非預期檔案。
- Story mode / RGBSeq / WiFi / ColorPicker / `platformio_local.ini` 盡量拆 commit。
- `platformio_local.ini` 是本機設定；只有使用者明確要求時才一起 commit。
- 若 commit 後又出現 dirty file，先停下來問使用者，不要直接補進上一個 commit。
- shared code 變更理論上要至少 build master、一個 slave、standalone；若使用者沒有要求驗證，不要宣稱已通過。
