# Wi-Fi Update 功能

> 最後更新：2026-08-22
>
> 相關參考：`../communication/external_uart/協議規格_NC4UART.md`、`firmware/master/src/otaNc4Flow.cpp`

---

## 〇、一分鐘理解

master 使用**純 AP 模式**（無需外部 router），提供 ColorPicker 及 slave OTA（透過目前選定的 I2C／RS485 transport 轉發給 slave）。**Master 韌體只可經 USB 更新**，不提供 Wi-Fi 自我更新。
平時 master 開機是跑 story mode，**不會開 WiFi**。需要 OTA 時，要用以下任一種方法**主動觸發** WiFi mode。

I2C OTA 與 UART/NC4 OTA 是兩條獨立編譯路徑。I2C 保留原有 Dev 回報、adaptive clock 與重試；UART/NC4 在傳輸期間全熄，並使用動態 baud 及 SHA／slot 驗證。

NC4 RS485 平時使用 `115200`；更新單一新版 Slave 時暫時切到 `460800` 傳 DATA，`OTA_APPLY` 前回到 `115200`。舊 Slave 不認切速命令時，仍以 `115200` 完成第一次升級。

UART/NC4 模式進入 Master WiFi maintenance 後，未更新及正在更新的 Slave 保持全熄；目標 Slave 成功套用新韌體並 reboot 後進入 `storyMode_dev`。I2C 模式保留原有行為。

---

## 一、背景

### 1.1 Wi-Fi 啟動機制

### 方法 1：UART 指令

透過 Timer mon 發送 UART 指令。

### 方法 2：reboot Master 晶片

1. master 晶片**按 reboot 鍵**
2. 10 秒內連續 reboot 3 次
3. 第 3 次開機時，WiFi 會自動啟動

### 方法 3：`-D FORCE_WIFI_ON` build flag（**僅限開發測試**）

在 `platformio_local.ini` 的 `[env:master]` 加入：
```ini
-D FORCE_WIFI_ON   ;測試用：開機直接進 WiFi mode，不用 reboot 3 次
```
燒進去後，master 每次開機都直接進 WiFi mode，跳過 power-cycle 計數。

`slave_standalone` 也支援同一個旗標；在 `[env:slave_standalone]` 加入同一行後，standalone 每次開機都直接進 WiFi mode，跳過 reboot 計數。

⚠️ **正式部署前必須註解掉此行**，否則裝置每次開機都進 WiFi mode、無法跑正常 story mode。

### Web 頁面不需要額外登入

Master 的 ColorPicker、`/api/*`、Slave OTA 與狀態頁不需要額外 HTTP 登入。連上 Master AP 後即可直接開啟頁面。

這不會移除 Wi-Fi AP 密碼；裝置仍須先使用設定的 AP 密碼連線。Firmware 類型、Slave ID、ESP32 image 與 OTA CRC／ACK 檢查亦維持不變。

---

### 1.2 連線

1. master 晶片開啓 WiFi 後，用手機或電腦：
   - 尋找 Wi-Fi 名稱：**以 `platformio_local.ini` 中 `WIFI_NAME` 為準**（例如 `hiNU_1-60_master`）
   - 輸入密碼：**`12345678`**
2. 連線成功後（手機可能顯示「無網際網路」是正常的），系統會自動彈出瀏覽器；不需要再輸入 HTTP 使用者名稱或密碼。

---

## 二、參數與常量

### 2.1 網址

| URL | 用途 |
|---|---|
| `http://192.168.4.1/` | ColorPicker / mode editor |
| `http://192.168.4.1/slave` | Slave 韌體上載頁（可選 Slave 1–10） |
| `http://192.168.4.1/colorpicker` | Color picker / mode editor（LittleFS 內以 gzip 壓縮保存，無外網仍可使用） |
| `http://<WIFI_NAME>.local` | 同上（iOS / macOS / Android 12+ 支援 mDNS）|

### 2.2 NC4 RS485 OTA 參數

| 名稱 | 值 | 說明 |
|---|---:|---|
| `SLAVE_UART_BAUD` | 115200 | 開機、正常通訊、APPLY 與 reboot 後 |
| `NC4_OTA_FAST_BAUD` | 460800 | 只供目前 OTA 目標 Slave |
| `NC4_LINK_SWITCH_DELAY_MS` | 20ms | READY 送完後才開始計時 |
| `NC4_LINK_FALLBACK_MS` | 5000ms | 快速 baud 無合法幀，自動回 115200 |
| `OTA_UART_FAST_CHUNK_SIZE` | 224 bytes | NC4 外層 payload 內的 DATA 大小；維持不變 |
| `OTA_WITH_SEQUENTIAL_WRITES` | ESP-IDF erase mode | BEGIN 不做整區 erase；按連續 WRITE 分段擦除 |

### 2.3 I2C／UART 模式邊界

| 模式 | 編譯選擇 | 完成確認 | WiFi maintenance 行為 |
|---|---|---|---|
| I2C | `SLAVE_TRANSPORT_NC4=0`、`SLAVE_TRANSPORT_UART=0` | 保留原有 `DEV:` 回報 | 保留原有 I2C OTA 行為 |
| UART/NC4 | `SLAVE_TRANSPORT_NC4=1` | `OTA_LAST` 全檔 SHA + `OTA_VERSION` 執行映像 SHA／slot + `MODE_GET=DEV` | 傳輸時全熄；DATA 暫升 `460800`；成功 reboot 後進 Dev |

兩者不是網頁上的 runtime switch；`/slave_status.transport` 只顯示目前 firmware 的編譯模式。

---

## 三、流程

1. 啟動 WiFi maintenance；UART/NC4 模式先向在線 Slave 發送 stop 及 power off，全部燈保持熄滅；I2C 模式不改原有流程。
2. 連 AP → 開 picker 頁（手機自動彈出 / 電腦自己開）。
3. 開啟 `/slave`，選擇 Slave 1–10 其中一台。
4. 選擇該 Slave 的 `.bin` firmware 上載。
5. Master 經目前 transport 傳送完成後，目標 Slave restart、運行新韌體並進入 `storyMode_dev`；未更新及正在更新的 Slave 繼續保持全熄。

### Master USB-only partition 首次部署

Master 使用 `config/partitions/partitions_master_usb.csv`：單一約 1.75 MB app + 約 2.19 MB LittleFS。Master 沒有第二個 OTA app slot，因此不能經 Wi-Fi 更新自己。

第一次由舊 partition 轉換時，必須用 USB 依次執行 erase、firmware upload 及 `uploadfs`：

```bash
pio run -e master -t erase
pio run -e master -t upload
pio run -e master -t uploadfs
```

之後 Master 韌體仍只可經 USB 更新。Slave Wi-Fi update 使用 PlatformIO 產生的 Slave `firmware.bin`；Master 先把檔案存入擴大的 LittleFS，再逐包轉送給 Slave 的 OTA app partition。

為了讓 slave WiFi OTA 的準確性接近 USB app 更新，流程必須符合以下規則：

- START 後，新版 slave 應回 `OTA_RESP_READY`，確認 slave 已經成功 `esp_ota_begin()`。
- 為了支援只能靠 WiFi 升級的舊 slave，START 階段可接受舊式 `OTA_RESP_ACK`；若 START 回應讀不到，也允許進入第一個 DATA chunk，但第一個 DATA chunk 必須拿到正確 ACK，否則更新失敗。
- 每個 DATA chunk 都必須收到相同序號的 `OTA_RESP_ACK` 才能送下一包。
- 收到 NACK、錯誤序號 ACK/NACK、非 OTA 回應或 timeout 時，只能重送目前 chunk，不能假設成功。
- END 後，master 必須等 slave 回 `OTA_RESP_SUCCESS`，也就是 slave 已完成大小檢查、CRC32 檢查、`esp_ota_end()` 與 boot partition 設定。
- 沒有 slave 真正回報成功時，master 不能 reboot slave，也不能把 UI 顯示成更新成功。

### NC4 runtime baud 流程

1. Master 在 `115200` 查目標 Slave 的 `OTA_VERSION`。
2. 單播 `LINK_BAUD_PREPARE(460800)`；Slave 在舊 baud 回 `LINK_BAUD_READY`。
3. 雙方在 READY 完整送出後等 20ms，再切到 `460800` 並做一次 VERSION probe。
4. BEGIN／WRITE／END 走目前 runtime baud；每包仍需 ACK、offset、CRC 與最終 SHA。
5. END 成功後，用同一握手回 `115200`；normal probe 成功才可 APPLY。
6. 快速鏈路失敗時，Master 本機強制回 `115200`；Slave 最遲 5 秒自動回復。
7. 未支援 `0x3309` 的舊 Slave 保持 `115200`，流程不因第一次升級而中斷。

### firmware.bin 目標檢查

新版 master / slave firmware 會在編譯產物內嵌一段文字標記：

- `FASTLED_FW_ROLE=master`：Master firmware，供 USB 燒錄使用，Slave OTA 頁不接受。
- `FASTLED_FW_ROLE=slave`：Slave firmware，只能上傳到 `/slave`。
- `FASTLED_FW_SLAVE_ID=N`：指定這個 firmware 屬於哪一台 slave。

WiFi update 頁會先在瀏覽器檢查：

- `.bin` 副檔名、大小、ESP32 app magic byte。
- Slave 頁只接受 `slave`，而且 `SLAVE_ID` 必須符合選到的 slave。

Master 後端也會再檢查 Slave firmware，避免前端被跳過或選錯檔。舊 firmware 如果沒有 `FASTLED_FW_*` 標記，仍會允許上傳，但只能做基本 ESP32 app 格式檢查，無法確認 role/slaveId。

---

## 四、狀態與時序

### 4.1 Slave OTA 速度與相容性

Slave firmware 不是直接由 WiFi 寫入 slave，而是：

1. 瀏覽器把 `.bin` 上傳到 master。
2. master 再透過目前編譯的 I2C 或 UART/NC4 transport，把 firmware 分包送給指定 slave。
3. slave 收包後寫入 OTA partition。

網頁分開顯示「上傳到 Master」及「傳送到 Slave」。第二段速度取決於目前 transport，不可把瀏覽器已到 `100%` 當成 Slave 已更新成功。

### 4.2 Fast OTA chunk

新版協議支援兩種 chunk size：

| 類型 | chunk size | 用途 |
|---|---:|---|
| Legacy | 32 bytes | 舊 slave 相容路徑 |
| Fast | 56 bytes | 新 slave 支援的較快路徑 |

master 在開始 slave OTA 前會先送 `OTA_CMD_CAPS` capability probe：

- 如果 slave 回報支援 fast OTA，master 使用 `56 bytes` chunk。
- 如果 slave 是舊 firmware、沒有回報，master 自動退回 `32 bytes` chunk。

### 4.3 舊 Slave 的 fallback 與多台更新

- CAPS、START、DATA、END 都有 bounded timeout；CAPS 或 metadata START 失敗時會退回 legacy START／32-byte chunk。
- 若 fast metadata START 只回一般狀態封包、沒有 `OTA_RESP_READY`／ACK，Master 不會開始 56-byte DATA；會先 ABORT 並以 32-byte、100kHz conservative 模式重新 START。此路徑供不能使用 USB 的舊 Slave 完成第一次升級。
- 若 fast DATA 的第一包未取得有效 ACK（包含只收到一般狀態封包），master 會記住該 Slave 的 legacy 偏好，完整重開本次 OTA 後以 legacy chunk 繼續，避免卡在半套協議。
- 舊版只回一般狀態封包、不回 OTA ACK 時，master 會以限速的 status-only rescue 路徑送出資料；若仍無法確認 chunk，會明確報錯，不會把 UI 誤判成成功。
- 新版 Slave 的 fast OTA 確認可由已提交狀態重建：第一個 DATA 前可重送 `READY`，DATA 寫入後可重送最後一個 chunk 的 `ACK`，完成驗證後可重送 `SUCCESS`；單次 I2C read 遺失不會永久吃掉確認。
- Fast DATA 若整個 ACK polling window 都只讀到非 OTA／錯位 frame，Master 會完整重置 I2C bus、恢復目前 OTA clock，再重送同一個 56-byte chunk；不會跳包或切換 legacy。
- Fast DATA 封包最大為 64 bytes，slave 共用接收 buffer 必須保留第 65 byte 作字串結尾；OTA 進行中固定回傳 8-byte OTA response，可回前一個已提交 ACK 或 `OTA_RESP_BUSY`，不可混入一般狀態封包。
- 同一時間只允許一台 Slave OTA。`/slave_status` 會回傳 `globalBusy` 與 `thisSlaveActive`，網頁只顯示目前選定 Slave 的進度，其他頁面會顯示「另一台 Slave 正在更新」。
- 批次頁可一次選多個 firmware，但嚴格逐台處理：上一台完成或失敗後，才上傳下一個檔案到 Master。
- I2C 保留原有整份 firmware 自動重試；UART/NC4 不會因最終驗證失敗而把同一檔案再次由瀏覽器上傳，僅使用 frame／chunk bounded retry。
- I2C END 必須收到 `OTA_RESP_SUCCESS`，並在重啟後確認 Slave 回報 `DEV:`；這是原有完成流程。
- UART/NC4 使用獨立 `0x22xx` OTA 流程，完成時同時要求兩種 SHA／slot 正確及 `MODE_GET=DEV`。

### 4.4 WiFi maintenance 燈光狀態

- I2C 模式保留原有 OTA reboot 後進入 Dev Mode 及 `DEV:` 確認。
- UART/NC4 的 `Power: off` 期間禁止因沒有 Master polling 而自動進入 link-lost Dev Mode。
- UART/NC4 OTA 傳輸期間保持全熄；成功 APPLY 並 reboot 後由 `boot_dev` 進入 Dev Mode。
- UART/NC4 OTA 失敗或未開始的 Slave 不會自行亮起。

### 4.5 UART/NC4 進度與驗證

| 階段 | UI 顯示 | 成功證據 |
|---|---|---|
| Browser → Master | 上傳百分比 | Master 收到完整檔案並通過 role／Slave ID 檢查 |
| Master → Slave | 傳輸百分比、目前 baud、速度、預計剩餘時間 | 每包 ACK、offset 與重試結果 |
| Verifying | `100%`、`驗證中` | END 全檔 SHA 通過 |
| Rebooting | `100%`、`重新啟動中` | 回到 `115200`，reboot 後兩種 SHA、slot 及 `MODE_GET=DEV` 均吻合 |

UART/NC4 使用兩個不同 SHA domain：

- `OTA_LAST` 比對完整 `firmware.bin` SHA，證明接收內容無誤。
- `OTA_VERSION` 比對 firmware 內嵌的 `app_elf_sha256` 及 running slot，證明新映像實際啟動。
- 若 `OTA_BEGIN` ACK 遺失，第一次 `WRITE` 前的相同 BEGIN 只補回 ACK，不會再次 erase／開啟 OTA slot。
- NC4 BEGIN 使用 `OTA_WITH_SEQUENTIAL_WRITES`；不可改回 `OTA_SIZE_UNKNOWN`，後者會先擦除整個 partition，實機會超過現有 BEGIN timeout。

畫面只有在映像與 Dev 狀態全部通過後才顯示成功。若在 `100%` 後失敗，UI 會保留 `100%` 並顯示失敗原因，不會重新上傳整份檔案。

## 五、限制與注意事項

### 5.1 只可用 WiFi 更新 Slave 時的升級方式

如果 slave 不能用 USB，只能靠 WiFi OTA：

1. 第一次把舊 slave 升級到新版 firmware 時，仍會使用 legacy `32 bytes`，所以速度可能仍然較慢。
2. slave 成功升級並 reboot 後，之後再更新同一台 slave，master 會偵測到 fast OTA，改用 `56 bytes`。

這樣可以避免「master 先改快封包，但舊 slave 不懂新封包，導致第一次 WiFi OTA 失敗」。

- 同一時間只可更新一台 Slave，且切速命令不可 broadcast。
- `0x3309/0x330A` 暫屬本專案 local extension，未納入隊友 upstream System schema。
- `transportRate` 顯示目前 runtime baud；看到 `460800` 只代表正在快速 session，不代表 OTA 已成功。
- 實際成功仍以 reboot 後 running SHA／slot 與上傳 image 一致為準。

---

## 六、驗證結果

### 6.1 Mac 自動批次 OTA 實機測試

Mac 先連線到 Master AP，再於 repo 根目錄執行：

```bash
python3 scripts/test_slave_wifi_ota_e2e.py
```

預設會先建置並依序更新 `Slave 2 → Slave 3 → Slave 4 → Slave 5`。使用現成 firmware 時：

```bash
python3 scripts/test_slave_wifi_ota_e2e.py --skip-build
```

自訂順序或 Master 位址：

```bash
python3 scripts/test_slave_wifi_ota_e2e.py \
  --slaves 5,2,4 \
  --base-url http://192.168.4.1
```

只有全部 Slave 回報 `success` 時 exit code 才是 `0`。`unconfirmed`、`failed` 或 timeout 都會回傳非 0，但測試仍會繼續下一台。

腳本不會自動切換 Mac WiFi，也不會更新 Master 韌體。

### 6.2 2026-08-22 動態 baud 軟體驗證

- 時間：2026-08-22（Asia/Hong_Kong）
- 設備：macOS、host C++ tests、PlatformIO ESP32-S3 `master`／`slave1`／`slave2`／`slave_standalone`；未接實體硬件
- 現象：schema codec、20ms 切換、5 秒 lease、session echo、舊 Slave fallback、APPLY／中止前 RESTORE contract 全部通過；四個 firmware 環境 build 成功
- 結論：實作可建置；Slave1/Slave2 的 460800 WiFi OTA 時間、SHA、slot 與 reboot 尚待實機驗收

### 6.3 WiFi maintenance 熄燈／完成後 Dev 軟體驗證

- 時間：2026-08-22（Asia/Hong_Kong）
- 設備：host contract tests、PlatformIO ESP32-S3 build
- 現象：UART/NC4 傳輸期間保持全熄；成功 reboot 後以 `MODE_GET=DEV` 確認進入 `storyMode_dev`；I2C 仍使用原有 boot-to-Dev 流程
- 結論：I2C／UART 隔離 contract 通過；Master、Slave1、Slave2 已重新 build／USB upload，UART/NC4 完成後 Dev 行為待下一輪 WiFi OTA 實機確認

### 6.4 2026-08-22 Slave1／Slave2 動態 baud 實機驗證

| 項目 | Slave1 | Slave2 |
|---|---:|---:|
| Browser→Master 上傳及儲存 | 8.44s | 8.03s |
| `OTA_BEGIN`→DATA 100% | 46.98s | 53.80s |
| HTTP request→reboot 後驗證完成 | 56.48s | 62.89s |
| 快速傳輸 baud | 460800 | 460800 |
| 回復正式 baud | 115200；第一次 probe 成功 | 115200；第一次 probe 成功 |
| 新增 timeout／retry／bad frame | 0／0／0 | 0／0／0 |
| 映像驗證 | `OTA_LAST`＋`OTA_VERSION`／slot 通過 | `OTA_LAST`＋`OTA_VERSION`／slot 通過 |

- 時間：2026-08-22（Asia/Hong_Kong）
- 設備：ESP32-S3 Master、Slave1、Slave2；Master AP `dev_PGU_V1`；NC4 RS485
- 現象：兩台均完成 `115200→460800→115200`；每 10% 顯示 progress、baud 與 ETA。Slave1 驗證完成後 125ms 才開始處理 Slave2，證明批次逐台執行。
- 結論：動態 baud、BEGIN 分段 erase、進度、順序隊列、兩種 SHA／slot 與正常 baud restore 實機 PASS。該輪使用舊的完成策略，log 為 `power-off held`；其後已改成 reboot 後取得 `MODE_GET=DEV` 才判定成功，程式、build、USB upload 已完成，但新策略仍待一次 WiFi OTA 肉眼複測。

## 七、結論

- Master WiFi AP 只接收／暫存 firmware；Slave OTA 的可靠性仍由 transport ACK、CRC、SHA 與 reboot 後版本確認決定。
- NC4 正常值固定 `115200`，快速 DATA 使用 `460800`；成功、失敗或失聯後都必須回 `115200`。
- 舊 Slave 保留 115200 相容路徑，不能因加入快速模式而失去第一次 WiFi 升級能力。
- Slave1／Slave2 的 460800 實機 OTA、進度、順序執行、映像驗證與 115200 restore 已通過；成功 reboot 後 Dev 燈效仍待最後肉眼複測。
