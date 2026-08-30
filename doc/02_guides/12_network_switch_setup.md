# 12. 網路交換器設置與連線排障手冊

> **用途**：兩台 Cisco 3560X 交換器（PoE + DHCP snooping）的正確設置，以及燈板「連不上 / 拿不到 IP / 跑著跑著不見」的排障步驟。
> **整理日期**：2026-08-30
> **對應設備**：Light-SW-01、Light-SW-02，與 `slave_map.json` 裡的 51 台燈板。

---

## 1. 環境清單

| 項目 | 值 |
|---|---|
| 交換器 1 | Light-SW-01，`192.168.8.254`，WS-C3560X-48P-L，STP 模式 `pvst` |
| 交換器 2 | Light-SW-02，`192.168.8.253`，WS-C3560X-48PF-L，STP 模式 `rapid-pvst` |
| 互連 trunk | 兩台都只有 **Gi0/47**（native vlan 1，allowed 1-4094） |
| 路由器 / DHCP server | SW-01 的 **Gi0/48**（`show cdp` 標 Router） |
| 管理 VLAN | **VLAN 192（LIGHTING）**，交換器管理 IP 在 Vlan192，不在 Vlan1 |
| 燈板 VLAN | 全部接在 VLAN 192（Gi0/1~46） |
| 管理連線 | **Telnet（正常）**；SSH 目前壞掉（見 §9） |

> 燈板是有線 **RMII LAN**，不是 WiFi（boot log：`初始化 RMII LAN`）。別被「Wi-Fi 不穩」誤導。

---

## 2. 症狀 → 根因對照表

這三種症狀我們都遇過，各自對應不同根因，別混在一起查：

| 症狀 | 真正根因 | 修法 |
|---|---|---|
| **「LAN 已初始化但尚未取得 IP」** | DHCP snooping 的 trunk（Gi0/47）沒設 `trust`，DHCP OFFER/ACK 被交換器丟掉 | §5 交換器設置 |
| **「跑著跑著就不見 / 一直敲門不回來」** | 軟體層 half-open：WS 對面靜默消失，slave 的 `connected` 卡 True，把 master 敲門吞掉 | §6 韌體端（已修，需重新部署） |
| **「上傳後一直恢復 / 無限循環」** | confirm 成功判定失真 + 根目錄檔誤走 promote → pending 永不清 → 3 次重啟自動回滾 | §7 韌體端（已修） |

---

## 3. 交換器「廣播傳不到」的真相

如果直覺是「廣播指令傳不到 SW-02」，先記住：**交換器層面廣播域是通的**（trunk VLAN 192 雙向 FWD，無 blocked / 無 MAC flapping / storm-control 從未觸發）。

真正的現象是反過來的：**SW-02 的設備「從不發任何幀」（連 ARP 都沒有）**，所以 SW-01 學不到它們的 MAC。而它們不發幀的原因就是「拿不到 IP」（DHCP snooping 擋住）——拿到 IP 之前設備根本不會主動廣播。

**驗證方式**：`show mac address-table interface Gi0/47`
- 若 SW-02 側 trunk 學到 40+ 個 VLAN 192 MAC（SW-01 設備）→ 廣播過來正常。
- 若 SW-01 側 trunk「只有交換器自己的 MAC、沒有設備 MAC」→ 設備端不吭聲，往下查 DHCP。

---

## 4. 診斷命令速查表

排障時照順序跑，就能快速定位：

```bash
# 1. 拓撲 / loop 有沒有
show spanning-tree summary
show spanning-tree inconsistentports
show interfaces status | include connected

# 2. 廣播有沒有風暴（storm-control 是否觸發）
show interfaces counters broadcast          # BcastSuppDiscards 全 0 = 沒風暴
show storm-control

# 3. DHCP snooping 誰 trusted
show ip dhcp snooping

# 4. trunk 上學到誰的 MAC（判斷廣播域通不通）
show mac address-table interface gigabitEthernet 0/47

# 5. 誰連在哪、CDP 鄰居
show cdp neighbors
show vlan brief
```

---

## 5. 交換器正確設置（核心，已執行並永久儲存）

**必須**讓 DHCP server 那一側的 trunk 端口為 `trusted`，否則跨交換器的設備永遠拿不到 IP。

### 5.1 兩台交換器都要做（Gi0/47 = trunk）

```bash
# Telnet 登入（SSH 目前壞）
telnet 192.168.8.254     # 或 192.168.8.253
# 帳號：admin（密碼見 tools/PC/poe_restart.py 的 PASSWORD / SECRET）
enable
configure terminal
interface GigabitEthernet0/47
 ip dhcp snooping trust
end
write memory             # 永久儲存（= copy run start）
```

### 5.2 驗證（兩台都要確認）

```bash
# 當下生效狀態：Gi0/47 應顯示 Trusted = yes
show ip dhcp snooping | include GigabitEthernet0/47

# 是否落盤（重啟不消失）：應看到 ip dhcp snooping trust
show startup-config | section interface GigabitEthernet0/47
```

### 5.3 正確的 trusted 分布（對照用）

| 端口 | 角色 | trusted |
|---|---|---|
| Gi0/48 | Router / DHCP server 側 | ✅ yes |
| Gi0/47 | 交換器互連 trunk | ✅ yes（本次修正） |
| Gi0/1~46 | 接燈板 | ❌ no（正確，rate limit 15） |

> 原則：**有 DHCP server / 其他交換器的那一側 → trusted；純 client 側 → untrusted。**

---

## 6. 韌體端修復（half-open，已改，需重新部署）

改動的檔案（slave 端，要透過 Step 0 重新上傳到設備）：

| 檔案 | 改什麼 |
|---|---|
| `slave/lib/sys/net_bus.py` | 新增 `idle_ms()`（距離上次收到資料的毫秒數）；connect 設 `_last_rx`、disconnect 清掉 |
| `slave/action/sys_actions.py` | `on_connect_request` 的防抖動 + 健康門檻：`connected` 且 `last_url==url` 時，若 `idle_ms() > ws_stale_ms`（預設 30000ms）就 `disconnect()` 放行重連，否則照舊 return True |

`ws_stale_ms` 可從 config `System.ws_stale_ms` 覆寫（毫秒），預設 30s，對齊 master「30s 無回應標離線」的健康檢查節奏。

master 端 `tools/PC/NetBusMaster.py` 也補了 accepted socket 的 `SO_KEEPALIVE`（macOS `TCP_KEEPALIVE` / Linux `TCP_KEEPIDLE` 30s）。

---

## 7. 韌體端修復（上傳確認循環，已改）

改動在 `tools/PC/NetBusMaster.py`：

1. `_confirm_file` / `_confirm_path_batch` / `_undo_path_batch`：改用 slave 回覆的 **pending 欄位**判定是否真的清掉（不再只看「有沒有收到回應」），失敗自動重試一次。
2. `_run_upload_batch` / `_upload_single_file_to_targets`：根目錄檔上傳後**直接進待確認清單**，不再呼叫 `_promote_file`（檔案已被 `_upload_bytes` 直接寫到 root，再 promote 會因 src 不存在而失敗 → pending 永不確認 → 3 次重啟回滾 → 無限循環）。

---

## 8. 下次排障 SOP（照順序走）

1. **看設備 boot log 第一句網路訊息**：
   - `LAN 已初始化但尚未取得 IP` → 查 §5，DHCP snooping trust 是不是又被改掉了。
   - `🌐 LAN 連接成功 | IP: 192.168.8.x` → 網路正常，往下查連線。
2. **看 master 主控台**：
   - 有 `👋 [Connect]` → 連上了。
   - 一直「無響應→離線」且 slave 端 log 靜默 → half-open（§6），確認韌體是新版。
3. **確認交換器沒 loop/風暴**：§4 那幾條跑一遍，`BcastSuppDiscards` 全 0 就是正常。
4. **確認 trunk trusted**：`show ip dhcp snooping | include Gi0/47`，Trusted 一定要 yes。

---

## 9. 已知隱患 / 待辦

| 項目 | 現況 | 建議 |
|---|---|---|
| STP 模式不一致 | SW-01 `pvst`、SW-02 `rapid-pvst` | 統一 `spanning-tree mode rapid-pvst`（目前能收斂，但抖動時收斂慢） |
| SSH 壞掉 | port 22 TCP 通但 banner 空，`Error reading SSH protocol banner` | 查 vty `transport input`、`crypto key generate rsa`（`poe_restart.py` 目前靠 Telnet） |
| 明文密碼 | `poe_restart.py` 的 PASSWORD/SECRET 明文 | 移到環境變數；交換器還開著 Telnet（明文），建議日後關 Telnet 留 SSH |

---

## 10. 安全提醒

- 交換器管理密碼明文存在 `tools/PC/poe_restart.py`，且會進 git 歷史。
- 交換器目前開著 **Telnet（明文傳輸）**。
- 若要更安全：把密碼改放環境變數 / 獨立的 config（不入 git），並關閉 Telnet 只留 SSH（先把 SSH 修好）。
