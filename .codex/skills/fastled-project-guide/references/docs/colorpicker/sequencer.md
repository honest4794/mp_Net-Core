# Runtime Sequencer 規格

Runtime Sequencer 讓 ColorPicker 的時間軸直接在裝置執行，不需要重新編譯 story mode。

## 資料格式

瀏覽器會把一般單一 timeline 轉成 `SEQV1`；可編輯 StoryMode Playlist 使用含 Mode 邊界的 `SEQV2`。韌體不解析 editable JSON，只按時間轉送既有 `LC:` 指令。

```text
SEQV1,<durationMs>,<name>
<startMs>,<endMs>,<target>,LC:pat,...

SEQV2,<totalDurationMs>,<name>,<loop:0|1>
MODE,<index>,<startMs>,<endMs>,<name>
<startMs>,<endMs>,<target>,LC:patv,...
```

- `durationMs`：整段長度，最大 24 小時。
- `target`：`all` 或 slave ID。
- 舊式合併 upload 的 `.seq` 上限 16 KiB；StoryMode 兩階段 upload 的 `.seq` 上限 32 KiB。
- `.seq` 儲存在 `/seq/<slot>.seq`；壓縮後的 editable JSON 儲存在 `/seq/<slot>.json`，只供網頁重新編輯。
- slot 範圍為 `0-7`。
- `endMs` 是描述資料；停止動作已由瀏覽器展開成另一行到期的 `LC:` 指令。

播放前會送 `LC:enter` 暫停 story mode；停止或自然播完會送 `LC:exit`。Master 收到 Timer 的一般 story mode frame 時會自動停止 sequence，Timer UART payload 沒有變更。

## HTTP API

| 方法 | 路徑 | 說明 |
|---|---|---|
| POST | `/api/seq/upload?slot=0` | form body：`seq=<SEQV1>&json=<timeline JSON>` |
| POST | `/api/seq/stage?slot=0` | multipart file：分段寫入、驗證並暫存 `.seq`，上限 32 KiB |
| POST | `/api/seq/commit?slot=0` | multipart file：分段寫入 editable JSON，並原子更換兩個正式檔案 |
| POST | `/api/seq/play?slot=0` | 播放指定 slot |
| POST | `/api/seq/stop` | 停止目前播放 |
| POST | `/api/seq/pause`、`/resume` | 停留目前 Mode／繼續播放 |
| POST | `/api/seq/previous`、`/next` | 上一個／下一個 Mode |
| POST | `/api/seq/delete?slot=0` | 刪除指定 slot 的播放檔及 editable JSON |
| GET | `/api/seq/list` | 列出 slot、大小與播放狀態 |
| GET | `/api/seq/get?slot=0` | 取得 JSON sidecar |

StoryMode 採兩階段、multipart chunk 流式寫入，避免 25 KiB 播放檔與約 45 KiB editable JSON 同時佔用 standalone heap；每個 chunk 都會檢查大小及 LittleFS 寫入結果。commit 會先復原未完成的舊 transaction、備份最後良好版本，再以 marker 原子替換；失敗或重啟可回復舊版本。

## Teddy Bear StoryMode 範本

- 來源：commit `21eb2fa0` 的 `storyMode_demo.cpp` 與當時 `platformio_local.ini` 燈數。
- 共 11 Modes、總長 250 秒，保留 RGB1–RGB18、ESP LED、完整 effect 參數、時間與次序。
- `mapping` 會完整保存以便重現來源；目前 1D WLED backend 只有 Pride 的 circle mapping 會改變畫面，其餘值屬來源相容資料，不會顯示成通用可調 slider。
- 在 ColorPicker → Playlists →「StoryMode Playlist 編輯器」按「載入 Teddy Bear 範本」。載入只建立草稿，不會覆寫裝置。
- 可修改 Mode 次序／名稱／秒數／亮度，以及每個事件的 channel、開始／結束時間、effect 與 JSON 參數。
- 選 Slot 後按「儲存到裝置」；按「儲存並播放」會在成功提交後才開始播放。
- 一般 `pio run -e slave_standalone -t upload` 只更新 app partition，不會刪除 LittleFS，所以 Playlist 會一直保存，直到使用者按刪除。
- `erase_flash`、LittleFS format 或 `uploadfs` 會改寫／清除資料分區，不屬於保存承諾。

「停留目前 Mode」是 pause：燈保持當前畫面及 mode 位置；「繼續自動播放」從同一位置恢復。上一個／下一個會跳到 Mode 邊界重新派發該 Mode 的初始效果。

## Story boundary

Sequence 編輯器可匯出 `-D STORYMODE_*_TOTAL_SECONDS=` 片段，但不會在 runtime 修改 story mode 時長。這些時長是 Master 與 Timer screen 的編譯期合約；變更後仍需重新編譯兩端並保持一致。

## Touch LCD

Touch MON 的單行 UART buffer 不適合上傳 timeline。Touch web 只轉發 `/api/seq/list`、`/api/seq/play`、`/api/seq/stop`；上傳按鈕會隱藏，`upload/get` 必須直接連 Master 或 Standalone HTTP。
