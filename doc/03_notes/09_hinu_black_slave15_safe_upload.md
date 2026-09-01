# Hi-Nu 黑色 Slave15 安全上載紀錄

## 結論

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
| 設定來源 | `ports/S3/ESP32-S3_1_18_hinu_slave15_unverified/config.json` |

USB port 只記錄本輪實測結果；下次操作仍須重新列舉，不可直接沿用。

## 上載範圍

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

## 重做設定上載

每次先重新列舉並核對板身份，再執行：

```bash
python -B -m serial.tools.list_ports -v
python -B test/protocol/night_run/repl_upload.py \
  /dev/cu.usbmodem<本次核對的PORT> \
  ports/S3/ESP32-S3_1_18_hinu_slave15_unverified/config.json \
  /config.json
```

讀回驗證時必須確認 `cID=000F`、`num_pixels=0`，以及所有 `enable` 均為 `0`。
