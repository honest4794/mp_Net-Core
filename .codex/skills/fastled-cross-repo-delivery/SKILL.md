---
name: fastled-cross-repo-delivery
description: Use when FastLED changes may need synchronization to ColorPicker, MP4 Preview, or a paired Hi-Nu motor/sound repository; when auditing effect completeness or cross-board timing; or before task-only commit/push and GitHub Pages delivery.
---

# FastLED 跨 Repository 交付

## 核心流程

固定執行：**掃描差異 → 更新 → 完整性驗證 → staged diff 複核 → commit／push → 適用時提供 Pages 證據**。

不能只同步同名檔、只看到選單名稱，或只確認 push 成功。

## 目標角色

| 目標 | 適用變更 |
| --- | --- |
| `FastLED_ColorPicker` clone | ColorPicker Web／PWA、USB、Preset／Playlist、effect／palette catalog、schema、renderer、QA |
| `MP4_Preview_App` clone | RGB／WLED／PWM effect、palette、schema、catalog／adapter、recorder runtime、WASM、preview、Pages |
| Hi-Nu 配對 repositories | 藍色 `SlaveX` 的 C++ RGB／PCA／StoryMode，及黑色 `SlaveX.1` 的 MicroPython motor／sound／JSON timeline |

目標 root 必須來自本次使用者指示、全域／專案 `AGENTS.md` 或已驗證 workspace 設定，再以 repository root、origin 與目前 branch 確認；repo skill 不寫死個人電腦路徑。Effect、palette 或共用 schema 改變時通常核對兩個目標；純 ColorPicker UI／USB 變更不需碰 MP4。硬體 mapping、GPIO、profile、brightness、slave grouping、`platformio_local.ini` 只留在各自 authority repository。

### 例子

若來源與 ColorPicker 的 `rhythmic.cpp`、WLED 1D／2D 實作及 registry 已同 hash，但 ColorPicker 缺少「RGB 節奏（30）」分類，task manifest 只包含 Web source、分類測試與重建 HTML；不覆蓋 firmware，也不更新無關的 MP4 repository。

## Hi-Nu 配對板判定

配對 root 與預期 branch 以兩邊 `AGENTS.md` 及已驗證 checkout 為準。典型分工如下：

- 藍色 `SlaveX`（Hi-Nu C++ repo）擁有 RGB、PCA、視覺 StoryMode 與 Master scheduling。
- 黑色 `SlaveX.1`（companion repo 的 `dev_motor_effects` branch）擁有 motor effect JSON、motor UART、sound cue 與其硬體設定。
- Master 對兩板排定同一開始時間；兩板不以 peer-to-peer 命令互相啟動。現有非 `SlaveX.1` motor path 不因本配對規則而停用或搬移。

Hi-Nu 配對硬體 wiring 的最高權威是 [Figma `Gunpla` board 目前版本](https://www.figma.com/board/Wd6kUSFmDwmTflF711eixM/Gunpla?node-id=0-1&t=W5TL9CJopGvFQ9nh-1)。Repository 內的 `config.json`、`platformio_local.ini` 與文件只視為部署快照；涉及板角色、GPIO、UART address、RS485 或連線時，先讀取 Figma 目前內容，再只更新擁有該硬體的 repository。無法讀取 Figma 時，不以舊 config 猜測新 wiring。

先分類變更，再決定實際要修改的 repository：

| 變更 | 交付範圍 |
| --- | --- |
| motor／sound effect、cue、timeslot、方向、速度曲線、open／close／STOP | 更新 companion；若共同時序合約改變，同步 Hi-Nu |
| StoryMode mode ID／次序／總長／stage boundary／scheduled start 會改變 motor 或 sound cue | 掃描並同步兩邊 |
| 純 RGB／PCA 顏色、亮度或視覺參數，且共同時序合約不變 | 只更新 Hi-Nu；companion 維持零 diff |
| 純 companion runtime／JSON 修正，且 mode mapping 與時序合約不變 | 只更新 companion；Hi-Nu 維持零 diff |
| GPIO、UART address、port profile 等硬體 mapping | 先以 Figma 目前版本核對，再只修改擁有該硬體的 repo |

共同時序合約至少包含：穩定 mode key／ID 或明確 mapping、Master scheduled-start 語意、時間單位、總長、每個 motor／sound cue 的 start／end，以及結尾 motor STOP／sound stop。只有受影響的 repository 才產生 commit，不做占位修改或空同步 commit。

## 1. 掃描差異

1. 對來源與每個適用目標讀取 `AGENTS.md`、README、目前 branch、HEAD、origin、upstream、`git status --short`、staged／unstaged／untracked 清單。
2. 以本次任務已知 base 與 working diff 建立 task manifest；base 不明時從任務 commit 或已驗證 upstream 找證據，不猜 branch／remote，也不切換 checkout。
3. 用 `rg` 比對 effect ID、stable key、header/source、registration、catalog、schema、renderer dispatch、UI request、runtime adapter 與 generated asset。檔案存在或 hash 相同只證明該檔，不代表整條功能完整。
4. 記錄目標既有 dirty 路徑。與 task manifest 重疊且不能可靠分離時，停止該目標更新並回報；不得 stash、reset、clean、整目錄覆蓋或 `rsync --delete`。

## 2. 更新

- 只移植 task manifest 的依賴閉包，沿用目標現有 generator 與 filing structure。
- 先改 source-of-truth，再用目標現存 build 產生 HTML、PWA、catalog 或 WASM；不得只手改 generated file。
- 目標已有較新邏輯時做語意合併，不以來源整檔覆蓋。
- 不新增同步報告檔；除非使用者要求，證據留在測試輸出與交付摘要。

## 3. ColorPicker 完整性 Gate

每個受影響 effect／palette 都要證明：

1. ID／key 唯一，且 catalog、schema、renderer routing 集合一致。
2. UI 分類正確；schema 的型別、範圍、預設值與 renderer 實際讀取參數一致。
3. speed、brightness、color、palette 與專用欄位會形成正確 request；可用時比對 requested state 與 applied/readback state。只出現在 dropdown 不算完成。
4. USB 與 Web 使用同一控制 contract；Preset 可儲存／讀回／套用完整參數，Playlist 可引用、儲存、播放並恢復。
5. Web source 重建 generated HTML／PWA；第二次重建為零 diff。
6. 目前專案基線須具名核對：`234 effects`、`234 schemas`、`184 palettes`、rhythmic `30/30`、新增 WLED `6 個 1D + 2 個 2D`、house palettes `40/40`。正式 catalog 增減時，總數與對應測試必須在同一任務更新。
7. Preview／host test 要證明效果產生可見 frame，且受支援參數改變會改變輸出；要求實機驗收時再以指定 port 驗證，不猜 port。

## 4. 驗證

每個 repository 先從實際存在的 `AGENTS.md`、`package.json`、PlatformIO environments、scripts 與 Pages workflow 選命令；執行前確認檔案或 npm script 存在。禁止憑記憶發明測試。

- ColorPicker：至少涵蓋受影響的 build、catalog/schema、UI request、USB、Preset／Playlist、PWA 與韌體環境。
- MP4 Preview：至少涵蓋 preview build、catalog／adapter、runtime／WASM、parameter compatibility 與 Pages entry。
- Hi-Nu 配對：Hi-Nu 建置 Master 與受影響藍板；companion 執行 repo 內現有 motor／StoryMode JSON 測試。若存在，至少執行 `python3 -B test/motor/test_uart_motor.py` 與 `python3 -B test/pixel/test_uart_motor_storymodes.py`。
- 跨板 timing audit 必須證明兩邊 start contract、mode mapping、時間單位與總長一致，每個 cue 都有 start／end，最後有 motor STOP 與 sound stop；不要求未受影響的 repo 製造檔案差異。
- 任何 build／test 失敗、generated 第二次仍有 diff、或 completeness gate 不成立，都不得標示完成或 push 未驗證版本。

## 5. Task-only Commit／Push

1. 每個 repository 只 stage 明確 task paths；不用 `git add -A`、`git add .`、`git commit -a`。
2. commit 前檢查 `git diff --cached --check`、cached name-status 與完整 cached diff；確認既有 dirty 內容未被 stage。
3. 驗證通過後，自動 commit 並 push 各受影響 repository 的**目前 checkout branch**。不猜或切換部署 branch，不用 `--all`、force、tags，也不改寫歷史。
4. remote 已前進或 push rejected 時保留本機 commit並停止；不得自動 rebase／force。回報 repository、branch、commit 與錯誤。

## 6. GitHub Pages 證據（只限 Pages 目標）

Push 不等於部署完成。先讀實際 workflow 的 branch／path filters；缺 workflow 時先補齊已核准的部署路徑。Push 後核對同一 commit SHA 的 Actions run、成功狀態、Pages URL 與線上版本／內容。無法查到 run 或 URL 時，只能回報「已 push，Pages 未驗證」。

## 完成摘要

逐個 repository 回報：掃描到的差異、實際更新檔案、完整性或 timing contract 結果、測試結果、branch、commit SHA、push 結果、適用時的 Pages run／URL，以及保留的既有 dirty 路徑。

## 常見錯誤

- 同名檔或相同 hash 就宣稱 ColorPicker 完整。
- 猜測 target branch、remote、測試命令或 USB port。
- 因目標很髒而提交全部修改，或偷偷以 clean worktree 繞過重疊決策。
- 複製來源硬體 mapping／profile／brightness 到 App 或 Preview。
- 只驗證 catalog 名稱，不驗證 schema、request、renderer 與 applied state。
- Push 成功就宣稱 GitHub Pages 已更新。
- 把藍板當成黑板 motor／sound executor，或讓兩板互相直接啟動。
- 每次 StoryMode 視覺微調都強迫 companion 產生無意義修改或 commit。
