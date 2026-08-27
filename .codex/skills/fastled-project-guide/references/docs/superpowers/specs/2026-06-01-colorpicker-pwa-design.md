# Colorpicker GitHub Pages PWA 設計

日期：2026-06-01

## 目標

把現有的 Penelope colorpicker 包裝成可安裝的 Web App，使用方式跟 Money Home 類似：使用者用 Safari 或 Chrome 打開公開網址，選擇「加入主畫面」，之後就可以像 App 一樣啟動。

這個 App 會放在公開的 GitHub Pages，並在進入 App 前加上一個共用密碼畫面。共用密碼由專案負責人私下提供，不應以明文提交到 repository。

## 範圍

這次工作只處理現有 colorpicker UI 外層的可安裝 App 包裝與部署檔案。

包含：

- 給 colorpicker 使用的公開 GitHub Pages 輸出。
- 支援 iOS 與 Android 安裝體驗的 PWA manifest 與 mobile metadata。
- 用於安裝與快取靜態檔案的 service worker。
- 顯示 colorpicker UI 前的首次密碼畫面。
- 密碼正確後，在本機瀏覽器記住已解鎖狀態。
- 方便開發者更新與發布的 build/deploy 流程。

不包含：

- 真正的帳號登入、每人不同密碼，或後端驗證。
- 防止有心人士查看原始碼。GitHub Pages 是公開靜態網站。
- 修改 firmware 的 colorpicker 行為，除非 hosted app 相容性需要。
- 取代現有 ESP32 自己提供的 `/colorpicker` 流程。

## 安全模型

密碼畫面是便利性與基本隱私阻擋，不是真正的強安全機制。因為 GitHub Pages 只提供公開靜態檔案，有心人士仍然可以檢查 bundled JavaScript，然後繞過或找出密碼檢查邏輯。

App 仍應避免把明文密碼直接放在明顯的 UI 文字或設定中。密碼檢查可以使用內嵌 hash。這可以避免一般使用者隨手看到密碼，但不代表真正保密。

密碼輸入正確後，App 會把解鎖標記存在瀏覽器 local storage。使用者清除瀏覽器資料後，就會重新看到密碼畫面。

## 建議方案

使用目前產生出的 colorpicker 頁面作為 App 入口，並在外層加入 PWA 需要的檔案：

- `index.html`：GitHub Pages 的入口頁，包含或導向產生出的 colorpicker App。
- `manifest.webmanifest`：PWA 名稱、顯示模式、主題色、啟動 URL 與 icons。
- `service-worker.js`：靜態 app shell 快取。
- `icons/`：iOS 與 Android 使用的 App icons。

UI 的 source of truth 仍然維持在現有的 `web/` partials 與 `scripts/build_web.py`。產生出的檔案不應變成需要手動維護的來源。

## 使用者流程

1. 使用者打開公開 GitHub Pages 網址。
2. App 以支援 PWA 的網頁方式載入。
3. 在 colorpicker 控制介面出現前，先顯示密碼畫面。
4. 使用者輸入專案負責人提供的共用密碼。
5. App 在本機記住已解鎖狀態，並顯示 colorpicker。
6. 使用者透過 Safari 或 Chrome 的「加入主畫面」安裝。
7. 之後再次開啟會直接進入 colorpicker，除非 local storage 被清除。

## App 安裝行為

App 應使用：

- manifest 內的 `display: standalone`。
- 指向 GitHub Pages App 入口的 `start_url`。
- iOS metadata，例如 `apple-mobile-web-app-capable`、`apple-mobile-web-app-title` 與 touch icons。
- 與現有淺色 colorpicker 設計一致的 theme colors。

iOS 不會完整遵守所有 manifest 行為，所以除了 manifest 之外，HTML 內的 metadata 與 touch icon links 也必須保留。

## 開發者更新流程

開發者修改 repository 內的 source files，執行 colorpicker build，然後把產生出的 PWA output 發布到 GitHub Pages。

建議實作選擇：

- 讓產生出的 web output 保持 deterministic。
- 新增 build step，從現有產生出的 colorpicker 準備 GitHub Pages App folder。
- firmware output 與公開 PWA output 要保持足夠分離，避免 PWA service worker 檔案在非預期情況下被包進 firmware。

## 資料流程

密碼 gate 全部在瀏覽器 JavaScript 內執行：

- 啟動時檢查 local storage 是否已有解鎖標記。
- 如果尚未解鎖，隱藏 colorpicker shell 並顯示密碼畫面。
- 送出密碼時，對輸入值做 hash 或比較。
- 如果正確，儲存解鎖標記並顯示 App。
- 如果錯誤，顯示簡短錯誤訊息並維持鎖定。

解鎖後，colorpicker 控制流程維持現有 `web/script.js` 行為。

## 錯誤處理

密碼 gate 應處理：

- 空密碼：保持焦點在密碼欄位，並顯示簡短錯誤。
- 密碼錯誤：顯示簡短錯誤，不清空整個 App。
- local storage 失敗：允許目前 session 解鎖，但不要宣稱已記住登入狀態。
- service worker 更新：service worker 註冊失敗時，不阻止 App 使用。

## 測試

驗證項目應包含：

- 產生出的 App 可以在桌面瀏覽器打開。
- 鎖定狀態下，輸入密碼前 colorpicker 不會顯示。
- 錯誤密碼不會解鎖。
- 正確的共用密碼可以解鎖 App。
- 解鎖後重新整理仍維持解鎖。
- manifest 可以被讀取，而且是有效 JSON。
- service worker 可以在本機 HTTP server 註冊。
- 手機尺寸 viewport 下，密碼畫面與 colorpicker layout 沒有重疊問題。

能做到時，應使用本機 HTTP server 與 browser automation 或 headless Chrome 驗證，而不是用 `file://`，因為 service worker 需要 secure context 或 localhost。

## 尚未決定

公開 GitHub Pages repository 名稱與正式 production URL 尚未指定。實作時路徑應盡量保持相對路徑，讓 App 不論部署在 user page root 或 project page subpath 都可以運作。
