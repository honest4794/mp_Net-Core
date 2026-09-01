# 本機 Firmware／程式上載工具

## 核心概念

`upload_local.ini` 像本專案的 `platformio_local.ini`：保存 firmware 路徑、
app 目錄及工具位置，但**永遠不保存 USB port**。每次插板後仍要重新列舉、核對，
再把本次 port 明確放入 command。

所有指令都在 repository 根目錄執行，而且 Python 一律使用 `-B`。

## 第一次設定

Repository 已建立本機用的 `upload_local.ini`；它被 `.gitignore` 排除，不會 commit。
可分享的格式在 `upload_local.example.ini`。

若要連同板型設定一起上載，編輯：

```ini
[upload]
device_config = ports/S3/你的板型/config.json
```

設定後，工具會先把它上載為 `/config.json`，再上載 `slave/`。不要沿用另一塊板的
profile；GPIO、RS485、motor address 或 LED 數量可能不同。

## 每次操作流程

先列出目前 USB ports：

```bash
python -B tools/PC/upload_firmware.py list
```

只寫入完整 MicroPython image，不清除整片 flash：

```bash
python -B tools/PC/upload_firmware.py flash \
  --port /dev/cu.usbmodem<本次核對的PORT>
```

只更新 `device_config`（如有設定）與整個 `slave/` 程式：

```bash
python -B tools/PC/upload_firmware.py files \
  --port /dev/cu.usbmodem<本次核對的PORT>
```

寫 firmware 後再更新程式：

```bash
python -B tools/PC/upload_firmware.py all \
  --port /dev/cu.usbmodem<本次核對的PORT>
```

`all` 寫完 firmware 後會重新列舉 USB ports，並要求再次輸入已核對的 app upload
port；它不會直接相信燒錄前的 port。

## 安全預覽

`--dry-run` 要放在動作名稱前。它只顯示將執行的完整命令與檔案 mapping，不開啟
serial port：

```bash
python -B tools/PC/upload_firmware.py --dry-run files \
  --port /dev/cu.usbmodem<本次核對的PORT>
```

## 完整清除 flash

一般更新不需要 erase。只有已確認 firmware／filesystem 必須完全清除時才使用：

```bash
python -B tools/PC/upload_firmware.py all \
  --port /dev/cu.usbmodem<本次核對的PORT> \
  --erase
```

安全限制：

- `all --erase` 要求 `device_config` 已設定且檔案存在，避免清除後遺失
  `/config.json`。
- 工具會要求輸入完整的 `ERASE /dev/cu.usbmodem...`，只輸入 `yes` 不會執行。
- 任一 erase／flash／file upload／reset command 失敗時立即停止。
- `flash --erase` 只負責 firmware；若要自動還原 app 與 `/config.json`，使用
  `all --erase`。

## 自訂設定檔

預設讀取 repository 根目錄的 `upload_local.ini`。如需另一份本機設定：

```bash
python -B tools/PC/upload_firmware.py \
  --config /path/to/another_upload.ini \
  --dry-run files \
  --port /dev/cu.usbmodem<本次核對的PORT>
```
