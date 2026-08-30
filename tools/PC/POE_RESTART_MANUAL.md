# PoE Port 重啟工具使用手冊

`tools/PC/poe_restart.py` — 遠端重啟 Cisco 3560 交換器上的 PoE port（斷電 → 等待 → 恢復供電）。
適用 macOS / Windows，需要 Python 3.8+。

> 已整合進 `NetBusMaster.py` 主選單的 **9. PoE Restart**（可選正式執行或 Dry-run），
> 也可以用底下指令單獨執行本腳本。

## 快速開始

```bash
cd tools/PC

# 正式執行
python3 poe_restart.py

# 模擬模式（只預覽指令，不連線，練習用）
python3 poe_restart.py --dry-run
```

第一次執行若沒裝 Netmiko，腳本會提示並詢問是否自動安裝。

## 操作流程

1. **選交換器**：`1` Light-SW-01（192.168.8.254）/ `2` Light-SW-02（192.168.8.253）/ `3` 兩台都要
2. **選範圍**：`1` 全部（port 1–45）/ `2` 部分
3. 選部分時**輸入 port**，支援逗號與範圍混用，例如：`3,5,10-15`
4. **確認摘要**：畫面列出目標、動作、最終 port 清單
5. 輸入完整的 `yes` 才會執行；其他任何輸入＝取消

執行時：斷電 → 等待 `OFF_DELAY` 秒 → 恢復供電。全程不會把 port 留在斷電狀態。

## 保護機制

| 機制 | 說明 |
|------|------|
| 受保護 port | **46（電腦）、47（switch 互連）、48（router）** 永遠不會被操作；輸入了也會自動剔除並提示 |
| 二次確認 | 必須輸入完整 `yes`，按 Enter 或 `y` 都算取消 |
| 恢復失敗自救 | 恢復供電失敗會自動重連重試 3 次；最終失敗會明確警告哪些 port 仍斷電及手動補救指令 |

## 常用設定（腳本最上方「設定區」）

| 變數 | 預設 | 說明 |
|------|------|------|
| `OFF_DELAY` | `5` | 斷電後等幾**秒**恢復。要用分鐘寫 `2 * 60` |
| `USERNAME` / `PASSWORD` | `admin` / `Zion4794` | 登入帳密（無帳號的 Telnet 只用密碼） |
| `SECRET` | 同密碼 | enable 密碼 |
| `PROTECTED_PORTS` | `{46, 47, 48}` | 受保護 port 清單 |
| `ON_RETRIES` | `3` | 恢復供電的重試次數 |
| `IFACE_PREFIX` | `GigabitEthernet0/` | 模組化機型改 `GigabitEthernet1/0/` |

## 連線方式

先試 **Telnet**（連線快），失敗自動改試 **SSH**。錯誤訊息會區分「帳密錯誤」與「連不到裝置」。

> 電腦必須在 192.168.8.x 網段（或能路由到）才連得上交換器。


## 測試

```bash
python3 test_poe_restart.py   # 12 項測試，不需網路、不需 netmiko
```
