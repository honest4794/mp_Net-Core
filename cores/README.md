# cores/ — 核心實例

每個 `Core_XXX.py` 是一個**能獨立啟動的核心程式**：靠讀 bus 拿數據，數據由另一個核心提供。boot.py 跑完（總線就緒）後即可 `import + start()` 啟動。

## 三個核心

| 核心 | 職責 | 整合來源 | 前置條件 |
|------|------|---------|---------|
| **Core_LVGL** | LVGL UI 渲染。輸入讀 hw_manager 快照，不碰硬體 → 可跨核心 | `slave new/ui/lvgl/board.py` + `Core1.py` | LCD 在 bus + HwSampleTask 在跑 |
| **Core_MP4** | MP4/JPEG 影片播放，雙核心 pipeline（Core1 解碼 + Core0 讀檔顯示） | `mp4_testkit/Core0_worker.py` + `Core1_engine.py` | LCD + SD + io_hub/frame_hub/decoder 在 bus |
| **Core_Comm** | 純通訊（網路 + 實體線 + 硬體採樣），無 LCD 依賴 | `slave/main.py` 舊通訊核心 | network/uart/pin 在 bus |

## 啟動方式

所有核心共用同一份 boot.py（硬體初始化 + 總線註冊）。soft reboot 後：

```python
# boot.py 已跑完 → 總線就緒
import Core_LVGL    # 或 Core_MP4 / Core_Comm
Core_LVGL.start()   # 進入阻塞主迴圈
```

## 與 slave new/ 的關係

`slave new/` 是**完整整合版**（Core_Manager 任務模式 + Core0/Core1 核心模式，TaskManager 調度所有任務）。
`cores/` 是**單一職責的獨立核心範例**，展示如何用最小配置跑某一種功能，方便：

- 單獨測試某個功能（不需起整套 TaskManager）
- 組合多個核心（例如 Core0 跑 Core_Comm 採樣+通訊，Core1 跑 Core_LVGL 渲染）
- 作為新核心的範本

## 設計原則

1. **總線解耦**：核心只讀 bus / bus.shared，不直接碰別的核心的內部狀態
2. **輸入統一採樣**：hw_manager 快照（`bus.shared["_hw_inputs"]`）由 HwSampleTask 產生，所有核心消費
3. **LCD 互斥**：Core_LVGL / Core_MP4 共用同一塊 LCD，不可同時跑
4. **阻塞主迴圈**：`start()` 會阻塞（對齊 `slave new/Core0.py:worker_start` 風格），適合「一核心一主迴圈」的核心模式
