# Hi-Nu 黑色 Slave 更新範圍與 Slave15 安全上載紀錄

## 目前更新範圍

更新黑色 Slave 時，本次工作範圍只包含以下內容：

```text
slave/                              # 完整目錄：包含根目錄檔案及所有子資料夾
tools/ESP/hinu_motor_master.py      # 黑色 Master 的 Hi-Nu motor 測試／控制程式
test/protocol/rs485_probe.py        # 板端 RS485 漸進式測試程式
ports/S3/ESP32-S3_1_18_hinu_black/master/config.json
ports/S3/ESP32-S3_1_18_hinu_black/  # Master＋18 塊實體 Slave 的 config.json
```

`slave/` 必須保留完整目錄結構，不可只取個別 Python 檔案。設定檔共需 19 份部署副本：Master 一份，以及 18 塊實體 Slave 各一份。每份 `config.json` 都必須保持與板角色及 `System.cID` 的對應關係，不可用同一份通用設定取代全部裝置。

Slave14 與原 Slave16 已合併為同一塊實體 Slave，由 Slave14 的 `System.cID=000E` 統一控制。Slave14 保留翼 Address `44`，並吸收原 Slave16 的全部左浮游炮 motor addresses；不再部署 `slave16/config.json`。

Slave15 與原 Slave17 已合併為同一塊實體 Slave，由 Slave15 的 `System.cID=000F` 統一控制。原 Slave17 的全部右浮游炮 motor addresses 已加入 Slave15；不再部署 `slave17/config.json`，避免同一組 motors 被拆成兩個 Slave 身份。

Slave20 的硬體／module 設定以 Slave13 為範本，但兩者的板身份及 motor address 不同。複製後必須保留 Slave20 自己的 `System.cID`，並把 `uartMotor` address 設為右燃料管的 `60`、`61`、`70`、`71`；不可沿用 Slave13 左燃料管的 `45`、`46`、`48`、`49`。

實體 Slave 的正式設定已保存於 `ports/S3/ESP32-S3_1_18_hinu_black/slave01/` 至 `slave20/`；其中沒有 `slave16/` 或 `slave17/`。Slave16 motors 已併入 `slave14/config.json`，Slave17 motors 已併入 `slave15/config.json`。Master 設定保存在同一目錄下的 `master/config.json`；其 `System.cID` 為 `0000`，所有 runtime modules 停用，由 `hinu_motor_master.py` 自行擁有 RS485 UART。除上述項目外，repository 內其他檔案及資料夾均不屬於這次黑色 Slave 更新範圍，不需要一併複製或上載。

### 使用位置

- `slave/`：黑色 Slave 的正式 runtime 來源。
- `hinu_motor_master.py`：供黑色 Master 發送 Hi-Nu motor mode／stop／reboot 指令；不要當成 Slave runtime。
- `rs485_probe.py`：需要排查 RS485 時暫時部署到測試板；測試前先停止會佔用 UART1 的 `main.py`。
- Master `config.json`：只部署到對應的黑色 Master；不要在設定檔另行啟用 UART，避免與 `hinu_motor_master.py` 衝突。
- 實體 Slave `config.json`：依板號逐一部署；Slave16／17 不獨立部署，分別使用 Slave14／15 profile 統一控制。Slave20 可使用 Slave13 的硬體／module 設定作範本，但必須改成 Slave20 的板身份及右燃料管 motor address。

## Motor wiring 與 Kai 次序

Motor UART TX 使用 GPIO `12`、9600 baud。方向及最快速度固定為：Close 使用 Direction `A`／raw `0`；Open 使用 Direction `B`／raw `255`。每個 Kai timeslot 為 `5000 ms`，同一 Kai 次序內的全部已知 targets 使用共同 deadline 同時動作。

Address `35` 不存在，右前裙甲使用 Address `38`。Address `41` 保留為未指定，不自行猜配，也不寫入任何 `config.json`。

| Kai 次序 | 可動位置 | Slave：Motor addresses |
|---:|---|---|
| 1 | 頭：下巴推桿；上背包：鎚仔 | `1: 40`；`12: 42` |
| 2 | 左右腳掌；左右小腿推桿、外推桿、內推桿 | `9: 22`；`11: 23`；`8: 24,25,26`；`10: 28,29,30` |
| 3 | 左右膝頭；左右前／側／後裙甲 | `8: 27`；`10: 31`；`7: 32,33,34,38,36,37` |
| 4 | 胸；左右肩膀內／外／上 | `5: 73,75,74,76,77`；`3: 83,85,84,86,87`；胸地址 pending |
| 5 | 左右翼；左右燃料管 | `15: 43`；`14: 44`；`13: 45,46,48,49`；`20: 60,61,70,71` |
| 6 | 盾；頭頂＋耳仔推桿；左右浮游炮全部開蓋及尖尖：下／中／上、前／後 | `1: 39`；`14: 53,91,63,101,54,92,64,102,55,93,65,103`；`15: 57,94,67,104,58,95,68,105,59,96,69,106`；盾地址 pending |

尚未提供地址的部件只記錄為 pending，不會輸出 motor command：

- Kai 4：胸正前方、兩邊散氣口甲、駕駛艙上、駕駛艙中、駕駛艙下。
- Kai 6：盾中間兩邊、盾頂、盾尾兩邊。

Master 未連線超過 `10000 ms` 時，全部 Black Slave 進入本機 Dev loop：Mode 2 最快 Close `10000 ms`，保持 `0x80 STOP` `5000 ms`，再以 Mode 1 最快 Open `10000 ms`，保持 `0x80 STOP` `5000 ms`，之後循環。設定以 `[2, 1]` 兩個 `15000 ms` slot 表示；兩個 effect 均在前 `500` frames（20 ms/frame）動作，slot 剩餘 `5000 ms` 輸出 STOP。Master 恢復時先停止本機 loop，再交回 Master 控制。

> 下方內容是 2026-09-01 首次建立 Slave15 零輸出安全狀態的歷史紀錄。當時只上載 `config.json`；這不代表目前更新仍只需要該檔案。目前更新應依本節列出的範圍執行。

## 2026-09-01 安全設定結論

2026-09-01 核對 Figma `Gunpla` wiring 目前版本時，Slave15 的黑色 ESP32-S3 接線無法確認。因此本輪不採用 repository 內其他 Slave 的 GPIO、RS485、UART motor address 或聲音設定，也不由 `hi_nu_motor_project.json` 的 sequence address 反推實體接線。

板端只上載 Slave15 的安全設定檔：

- `System.cID`：`000F`
- `System.num_pixels`：`0`
- `ProjectMode.enable`：`0`
- `CircuitDecode`、Network、SPI、I2C、UART、PWM、I2S、SD、PIN、ENC、TFT、HUSB238、WS2812、APA102、PCA9685、`uartMotor`：全部停用
- 所有輸出及 motor list：空陣列

此設定只建立 Slave15 身份與零輸出安全狀態，不代表 motor／sound 程式已完成部署。

## 本輪硬體身份

| 項目 | 核對值 |
|---|---|
| USB port | `/dev/cu.usbmodem1101` |
| ESP32-S3 UID | `90da7249a6a4` |
| MicroPython | `1.29.0-preview` |
| 設定來源 | 原始零輸出 legacy profile；完成 canonical migration 後已移除，驗證值保留於本紀錄 |

USB port 只記錄本輪實測結果；下次操作仍須重新列舉，不可直接沿用。

## 當日上載範圍

為避免把無關 runtime／測試／UI 檔案寫進黑色 Slave15，本輪重新清除並寫入固定 MicroPython image 後，只上載：

```text
/config.json
```

沒有上載 `boot.py`、`main.py`、motor／sound runtime、pixel modes、mapping、sequence、UI 或測試檔案。待 Figma wiring 可核對後，才建立正式 Slave15 profile 並部署必要 runtime。

## 2026-09-01 實機驗證

- Flash erase：成功
- MicroPython image：寫入 `1,799,728` bytes，esptool 回報 `Hash of data verified.`
- MicroPython：`1.29.0-preview`
- UID：`90da7249a6a4`
- `/config.json` SHA-256：`b1ff7121b6d8aeafef4ffbb93f9eb8c4491e1c0242ff081c48a7231806d7ca11`，與本機 profile 完全相同
- Filesystem root：`boot.py`、`config.json`；其中 `boot.py` 由固定 MicroPython image 內建，本輪唯一另外上載的檔案是 `config.json`
- 讀回設定：`cID=000F`、`num_pixels=0`、全部 module／Network `enable=0`

## 上載目前 Slave15 profile

歷史零輸出 profile 已移除；目前 canonical Slave15 profile 會啟用 GPIO12 motor UART，並同時控制原 Slave15／17 motors，不可把它當成上方歷史安全設定。每次先重新列舉並核對板身份，再執行：

```bash
python -B -m serial.tools.list_ports -v
python -B test/protocol/night_run/repl_upload.py \
  /dev/cu.usbmodem<本次核對的PORT> \
  ports/S3/ESP32-S3_1_18_hinu_black/slave15/config.json \
  /config.json
```

讀回驗證時必須確認 `cID=000F`、motor UART TX GPIO `12`，以及 `uartMotor.address=["43","57","94","67","104","58","95","68","105","59","96","69","106"]`。
