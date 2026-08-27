# Audio-Reactive 燈效（麥克風 + MP3）

本次 session 新增「音訊反應」功能：用真實音量驅動燈效。提供兩種音訊來源、兩種消費方式。
`audioActive` 關閉時，WLED 燈效輸出沿用原本的模擬律動；真實音訊取樣 task 只在啟用 audio
或進入 VU/節奏模式時 lazy start。

> **跨 repo 狀態**：此功能由姊妹專案 **FastLED_ColorPicker**（分支 `dev_colorpicker_app`）移植過來，
> 同步至本 repo（Servo Test，分支 `dev_hiNu_gundam_v11`）。本 repo 專屬差異：WLED 效果都吃中央
> `wledSimulateSound()`，故只需單一接點即可全部 audio-active；全域 `[env]` 有 `lib_ignore = SD`，
> standalone 環境已清空以啟用 SD(SPI)。

---

## 1. 架構總覽

```
[I2S mic V829]  ─┐
                 ├─► int16 PCM ─► RhythmDetector(analyze): energy→level(0..1) + beat + BPM
[MP3 解碼]      ─┘                          │  (僅 standalone)
 (standalone)                               ▼
                              全域 gAudioLevel / gAudioBeat / gAudioBPM
                ┌───────────────────────────┴───────────────────────────┐
        (master) I2C 限速(~20Hz)廣播 "Audio:lvl,beat"          (standalone) 直接寫全域
                ▼                                                        ▼
        slave receiveEvent 解析 → 全域                            本地全域
                └───────────────────────────┬───────────────────────────┘
                                            ▼
        消費：audioActive ? gAudioLevel : sin8模擬  →  WLED 效果 / 獨立「節奏模式」VU
```

- **來源 A — I2S MEMS 麥克風 (V829)**：master 用 GPIO 8/9/10、slave_standalone 用 SCK=12、WS=11、SD=13。
- **來源 B — MP3 解讀**：**僅 slave_standalone / SD card MP3 路徑**。ESP 在執行期解讀 `/soundtrack.mp3`
  → PCM 分析驅動燈效，**不輸出聲音、不需 DAC/喇叭**。
  - 檔案來源：**只讀 SD 卡（SPI）**。SD 卡上的歌曲完全不占內部 flash，可放大檔/多首。
  - 解碼 PCM 環形緩衝放 **PSRAM**，內部 DRAM 幾乎零增加（libhelix 解碼器本身的內部狀態仍在內部 RAM）。
- **分配**：master 收音 → 算 level/beat → I2C 廣播給所有 slave；slave_standalone 用本地來源。
- **消費 1**：把真實音量接進既有 WLED 效果（取代模擬 `volumeSmth`）。
- **消費 2**：獨立「節奏模式」VU 表演（`storyMode_vu`，使用 `patterns_audio_active/patterns_vu` 的 20 種 VU pattern）。

### 為何 MP3 只在 standalone？
master 的 app 分割區為 1.375MB，改動前已用 96.2%（僅 ~54KB 餘裕）。MP3 解碼器(libhelix)約
+38KB，放 master 會 overflow。standalone 餘裕較多，且「單機播放 soundtrack」本就是 standalone 情境。

---

## 2. 硬體接線（V829 I2S MEMS 麥克風）

| 角色 | SCK (bit clock) | WS (word select) | SD (data) | I2S port | 燈條輸出 |
|---|---|---|---|---|---|
| master | GPIO 8 | GPIO 9 | GPIO 10 | I2S_NUM_0 | 無（I2S 空閒）|
| slave_standalone | GPIO 12 | GPIO 11 | GPIO 13 | I2S_NUM_0 | RGB1/2/3/4/7（11/12/13 已關閉讓給 mic）|

- 取樣參數預設：16kHz、mono、24-bit-in-32-bit slot（取高 16 位）。可於 `platformio_local.ini` 覆寫
  `MIC_I2S_SAMPLE_RATE`、`MIC_I2S_SLOT_LEFT`（聲道相反時設 0）。

### SD 卡（SPI，僅 standalone 放 mp3）
SPI microSD 轉接板（含電平轉換）。麥克風走 I2S、SD 走 SPI(FSPI)，互不衝突。預設腳位（standalone
空閒、非馬達腳，可於 `platformio_local.ini` 覆寫 `SD_SPI_*_PIN`）：

| 訊號 | GPIO |
|---|---|
| SD_CS | 34 |
| SD_SCK | 36 |
| SD_MOSI | 35 |
| SD_MISO | 33 |

把歌曲命名為 `soundtrack.mp3` 放卡片根目錄即可（不用經 web 上傳）。master+slave 測試時不允許從
ColorPicker 放 soundtrack；音源走 master I2S mic，或後續 SD card MP3 硬體路徑。
- ⚠️ standalone 上 FastLED 用 ESP32-S3 的 I2S/LCD 周邊輸出燈條；mic 用 I2S_NUM_0。**需實機驗證
  兩者並存**，若衝突改用另一 port 或 PDM/類比備援。
- ⚠️ V829 的實際 I2S 格式/聲道/位元對齊需依 datasheet 確認，必要時調整 `audio_input.cpp` 與上述參數。

---

## 3. I2C 音訊協議（master → slave）

沿用既有字串指令協議（與 `Mode:` / `Brightness:` 同一條解析路徑），新增：

| 訊息 | 格式 | 說明 |
|---|---|---|
| 音量 | `Audio:<level0-255>,<beat0/1>` | master 限速 ~20Hz 廣播；slave 寫 `gAudioLevel`/`gAudioBeat` |
| 開關 | `AudioActive:<0/1>` | 切換 slave 端效果採用真實/模擬音量 |

> 協議擴充。相容性：未支援的舊 slave 會忽略未知字串，不影響既有 `Mode:`/`Brightness:`/OTA。

---

## 4. 控制（web / 旗標）

- **總開關 `audioActive`**：預設 **關閉**（WLED 效果沿用模擬 `volumeSmth`，視覺輸出與改動前一致）。
  - master：`POST /api/audio?active=0|1`（會 I2C 廣播給 slave）。
  - standalone：`POST /api/audio?active=0|1&source=mic|mp3`。
- **web UI**：colorpicker 的「Device」分頁最上方新增「Audio / 節奏」面板：啟用開關、來源下拉
  (麥克風/MP3 狀態)。master+slave 不提供 soundtrack 選檔或上傳入口。standalone 只使用本機 AP，不再提供 router WiFi manager。
  **改前端需重新 `uploadfs`** 才會生效。
- **節奏模式（VU）**：story mode 清單最後新增「節奏模式」(`storyMode_vu`)，附加於尾端以
  **不更動既有 mode id**。VU 直接讀 `gAudioLevel`；進入 VU 時會確保取樣 task 已啟動。
  目前會循環 20 個 Audio Active VU pattern，每個 20 秒，總長 400 秒。
- **功能總開關 `ENABLE_AUDIO`**：定義在 `firmware/shared/include/globals.h`（不放 platformio.ini）。
  某機不需要音訊時設 0 可整包移除（省 flash）。

---

## 5. 本次 session 變更清單

### 新增檔案
- `firmware/shared/include/audio/audio_input.h` / `firmware/shared/src/audio/audio_input.cpp`
  — I2S 麥克風擷取 + 取樣/分析 task（master/standalone）+ 來源分派 + `audioServiceTick()`。
- `firmware/master/include/audioController.h` / `firmware/master/src/audioController.cpp`
  — master：啟動取樣 task、loop 內限速廣播。
- `firmware/slave/include/audio_mp3.h` / `firmware/slave/src/audio_mp3.cpp`
  — **standalone-only** MP3→PCM 解碼（libhelix）；檔案來源 **只支援 SD(SPI)**；
  PCM 環形緩衝放 **PSRAM**。
- `firmware/shared/include/storymode/storyMode_vu.h` / `firmware/shared/src/storymode/storyMode_vu.cpp`
  — 獨立「節奏模式」VU 表演。

### 修改檔案
- `firmware/shared/include/globals.h`
  — `ENABLE_AUDIO` 旗標；`MIC_I2S_*` 腳位/取樣參數；`SD_SPI_*_PIN`（standalone SD 腳位）；
  `gAudioLevel/gAudioBeat/gAudioBPM/audioActive/gAudioSource` 宣告；`AudioSource` enum；
  `STORYMODE_VU_TOTAL_SECONDS`。
- `firmware/shared/src/globals.cpp` — 上述全域變數定義。
- `firmware/shared/include/audio/rhythm_detector.h` / `firmware/shared/src/audio/rhythm_detector.cpp`
  — 旗標由 `ENABLE_VU_METER` 改為 `ENABLE_AUDIO`；新增 `analyze()`（不渲染）、`level01()`；
  VU pattern 渲染已移到 `patterns_audio_active/patterns_vu`。
- `firmware/shared/src/patterns/patterns_wled/1D_strip.cpp`
  — 新增 `wledVolumeSmth()` helper，取代 3 處模擬 `volumeSmth`（gravcentric/midnoise 等）；
  Blurz 改為 audioActive 時用真實音量。
- `firmware/shared/src/storymode/storyModeController.cpp` — 註冊「節奏模式」(附加於尾端)。
- `firmware/master/src/i2cController.cpp` / `firmware/master/include/i2cController.h`
  — `broadcastAudio()` / `broadcastAudioActive()`。
- `firmware/master/src/main.cpp` — setup 啟動 `initMasterAudio()`；loop 呼叫 `serviceMasterAudioBroadcast()`。
- `firmware/master/src/colorpicker.cpp` — `/api/audio` 開關端點（含 I2C 廣播）。
- `firmware/slave/src/i2cController.cpp` — 解析 `Audio:` / `AudioActive:`，寫全域。
- `firmware/slave/src/main_slave.cpp` — standalone 不再開機即啟動取樣 task，改由 audio/VU lazy start。
- `firmware/slave/src/standaloneController.cpp` — `/api/audio` 與 standalone local AP 處理；
  啟用 audio 或選 MP3 來源時啟動取樣 task。
- `web/colorpicker.html` + `data/html/colorpicker.html.gz`（由 `scripts/build_web.py` 產生）
  — Device 分頁新增「Audio / 節奏」面板：啟用開關、來源(mic/mp3 狀態)，含 inline JS 串接
  `/api/audio`。**部署 standalone 需重新 `uploadfs`。**
- `platformio.ini`
  — `slave_standalone_base` 加入 `arduino-libhelix` 相依（git）、改用 `config/partitions/partitions_standalone.csv`；
  並在該環境清空 `lib_ignore`（全域 `[env]` 有 `lib_ignore = SD` 讓 FastLED 跳過 SD 避開 ff.h；
  standalone 的 mp3 需要 SD(SPI) 故重新啟用）。
- `config/partitions/partitions_standalone.csv` — standalone 無韌體 OTA，改成「單 app 2.75MB + LittleFS
  1.125MB」：優先保留 colorpicker/audio 韌體空間；LittleFS 只放 ColorPicker web UI，MP3 一律放 SD card。
  **改分割表需整顆 erase 重燒 + 重新 uploadfs。**
- `platformio_local.ini` — `[env:slave_standalone]` 明確關閉 `NUM_LEDS_RGB11/12/13`（讓給 mic）。

---

## 6. 編譯與驗證

### 已驗證（編譯通過）
（Servo Test repo 實測）
- `pio run -e master` ✅（flash **97.8%**，雙 OTA slot 1.375MB — 偏緊但可裝）
- `pio run -e slave_standalone` ✅（含 MP3 + SD + PSRAM，`config/partitions/partitions_standalone.csv`，flash **84.7%**、
  內部 RAM 65.1%）
- `pio run -e slave1` ✅（一般 slave，只收 I2C，flash **86.6%**）

> ⚠️ **本機建置環境注意**：FastLED 3.10.3 的 `file_system.cpp` 會無條件拉入內建 `SD` 函式庫，
> 而本機 `SD` 函式庫的 IDF FatFs/VFS include 路徑未被平台 build script 正確帶入，導致
> `ff.h` / `diskio_impl.h` 找不到（在**未改動的** slave1 也會發生，與本功能無關）。
> 暫時驗證用的繞法（不改動任何專案檔，純環境變數注入 include 路徑）：
> ```bash
> BASE="$HOME/.platformio/packages/framework-arduinoespressif32-libs/esp32s3/include"
> export PLATFORMIO_BUILD_FLAGS="-I$BASE/fatfs/src -I$BASE/fatfs/diskio -I$BASE/fatfs/vfs \
>   -I$BASE/vfs/include -I$BASE/sdmmc/include -I$BASE/esp_driver_sdmmc/include -I$BASE/esp_driver_sdspi/include"
> pio run -e master
> ```
> 你的正式機器若能正常 build，代表平台 include 已正確，不需此繞法。

### 待實機驗證
1. `audioActive=0` 時既有效果輸出與改動前一致（回歸）。
2. master 對麥克風發聲 → 序列埠 `gAudioLevel`/beat 變化 → slave 燈效律動。
3. standalone 本地麥克風驅動燈效，且 LED 輸出不受 I2S mic 影響（I2S 周邊並存風險）。
4. SD card 放 `soundtrack.mp3` → `source=mp3` → 燈效隨曲律動且不出聲。
5. 切到「節奏模式」→ VU 跟著音量/節拍跳動。

---

## 7. 降低 flash 用量（建議）

master 96.2%、standalone 95.7%，餘裕偏小。依「效益/風險」排序：

1. **LTO `-flto`（最大單一效益，~5–12%）**：在對應 env build_flags 與 link flags 加 `-flto`。
   低風險、build 變慢。可把 master 拉回約 88–90%。
2. **某機不需音訊就設 `ENABLE_AUDIO 0`**（globals.h）：整包移除音訊子系統。
   standalone 不用 mp3 時，連 libhelix(~38KB) 一起省。
3. **master `DEBUG_ENABLED=0`**：移除大量 `LOG_*` 字串(rodata)，省數十 KB，代價是少 serial debug。
4. **partition 重新平衡**：app slot 1.375MB、filesystem 1.21MB。若 filesystem 用量低，可縮 fs、
   擴 app slot。但 master 需 fs 暫存 slave OTA、standalone 需 fs 放 ColorPicker，空間有限。
5. **（大改、不建議輕用）放棄雙 OTA slot**：改單 app 分割可釋出 ~1.3MB 給程式，但 master 自身的
   web-OTA 會失效（slave 經 I2C OTA 不受影響）。

> 註：FastLED 會因偵測到 `<SD.h>` 而拉入未使用的 SD 函式庫，但停用方式不乾淨（取決於 include 偵測），
> 效益有限，暫不建議動。
