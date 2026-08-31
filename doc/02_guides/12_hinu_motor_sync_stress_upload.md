# Hi-Nu Black Motor 上載與同步壓測指令

本文件記錄兩種獨立測試：

- Black Master 直接向 Black Slave 1／2 發送 motor Mode 0–3。
- Blue Hi-Nu Master 使用無 motor 輸出的 Mode 250，量度兩塊 Black Slave 的排程 skew。

設定檔不保存 USB port。每次操作前必須重新列舉，並把本次核對的完整 port 明確寫入每一條 upload／monitor command。以下 `112xxxx` 是 2026-08-31 實測例子；重新插線後不可直接沿用。

## 1. 列舉 USB ports

```bash
ls -1 /dev/cu.usbmodem*
python -B -m serial.tools.list_ports -v
```

本輪核對身份：

| Board | Port |
|---|---|
| Blue Master | `/dev/cu.usbmodem1127101` |
| Black Master | `/dev/cu.usbmodem1127301` |
| Black Slave 1 | `/dev/cu.usbmodem1121301` |
| Black Slave 2 | `/dev/cu.usbmodem1121201` |

Black motor mapping：

- Slave 1：address `13, 15, 19`
- Slave 2：address `10, 12, 17, 21`

## 2. 上載 Black Slave 1

在 UART Design repository 執行：

```bash
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 ports/S3/ESP32-S3_1_18_hiNew/config.json /config.json
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 slave/app.py /app.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 slave/action/sys_actions.py /action/sys_actions.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 slave/action/pixel_actions.py /action/pixel_actions.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 slave/tasks/pixel_task.py /tasks/pixel_task.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121301 slave/pixel/registry.json /pixel/registry.json
uvx mpremote connect /dev/cu.usbmodem1121301 reset
```

`repl_upload.py` / `mpremote exec` 會進入 raw REPL；最後的 `reset` 不可省略，
否則檔案雖然已上載，Slave 主程式仍然不會運行。`reset` 後 USB port 會短暫消失；
要重新執行第 1 節的列舉指令，不可假設 port 一定沒變。

## 3. 上載 Black Slave 2

```bash
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 ports/S3/ESP32-S3-1_18/config.json /config.json
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 slave/app.py /app.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 slave/action/sys_actions.py /action/sys_actions.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 slave/action/pixel_actions.py /action/pixel_actions.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 slave/tasks/pixel_task.py /tasks/pixel_task.py
python -B test/protocol/night_run/repl_upload.py /dev/cu.usbmodem1121201 slave/pixel/registry.json /pixel/registry.json
uvx mpremote connect /dev/cu.usbmodem1121201 reset
```

## 4. 上載 Black Master command sender

這一步只上載 Black Master 的 NC4 command sender，不取代整套 MicroPython runtime：

```bash
python -B tools/PC/hinu_motor_command_test.py deploy-master --port /dev/cu.usbmodem1127301
```

Real-project Black Master 使用開機自動循環版本；`--port` 必須填當次重新列舉並
核對的 project board port，不可使用上面的 test-kit 範例 port：

```bash
python -B tools/PC/hinu_motor_command_test.py deploy-project-master \
  --port /dev/cu.usbmodem<REAL_PROJECT_PORT>
uvx mpremote connect /dev/cu.usbmodem<REAL_PROJECT_PORT> reset
```

此命令部署 `/hinu_motor_master.py` 及 `/main.py`。開機後以
`MODE_STOP action=0 → MODE_SET(start_delay_ms=300)` 依次廣播 Mode 0（10s）、
Mode 1（10s）、Mode 2（180s），然後回到 Mode 0。RS485 仍採
EN9／TX10／RX11 及 listen-before-talk；只在實際發送時把 EN 拉高。

由 Black Master 發送 Mode 0、1、2 及安全停止：

```bash
python -B tools/PC/hinu_motor_command_test.py send-mode 0 --start-delay-ms 300 --port /dev/cu.usbmodem1127301
python -B tools/PC/hinu_motor_command_test.py send-mode 1 --start-delay-ms 300 --port /dev/cu.usbmodem1127301
python -B tools/PC/hinu_motor_command_test.py send-mode 2 --start-delay-ms 300 --port /dev/cu.usbmodem1127301
python -B tools/PC/hinu_motor_command_test.py stop --port /dev/cu.usbmodem1127301
```

如 Slave 因 USB output 阻塞而無法進入 REPL，可由 Black Master 廣播延遲 reboot：

```bash
uvx mpremote connect /dev/cu.usbmodem1127301 exec \
  'import hinu_motor_master as m; m.reboot_slaves(100)'
```

單獨監察一塊 Black board 時，用 serial monitor 而不是 `mpremote exec`：

```bash
pio device monitor --port /dev/cu.usbmodem1121301 --baud 115200
pio device monitor --port /dev/cu.usbmodem1121201 --baud 115200
```

## 5. 上載 Blue Master 同步壓測 firmware

在 HiNu repository 執行：

```bash
cd '/Users/all.are.mathematics/My Documents/FastLED project/Gundam Project/20260724_1-18_HiNu_Gundam'
pio run -e master_motor_sync_stress
pio run -e master_motor_sync_stress -t upload --upload-port /dev/cu.usbmodem1127101
```

此 firmware 只發送空輸出的 Mode 250，不會推動 UART-412 motor。它連續測試
`300, 100, 50, 20, 10, 5, 2, 1 ms` lead，每級 100 個樣本。每級集齊 100 筆後才輸出
一行 `[SYNC-STRESS-BATCH]`，避免逐筆 USB print 本身製造 jitter。合法 NC4 broadcast
的最大間距小於 350 ms，因此 Blue Slave 1／2 不會因 10 秒失聯 timeout 同時進入 dev mode。

`TIME_SYNC` broadcast 只用於維持時鐘，不可由各 Slave 同時回覆；只有 unicast `TIME_SYNC` RTT query 才回覆 `TIME_SYNC_RSP`。否則多塊 Slave 會在 RS485 同一時槽碰撞，令 MODE_SET 積壓並破壞同步。

## 6. 同時監測 Black Slave 1／2

回到 UART Design repository：

```bash
cd '/Users/all.are.mathematics/My Documents/FastLED project/UART Design'
python -B tools/PC/hinu_motor_sync_stress_monitor.py \
  --slave1-port /dev/cu.usbmodem1121301 \
  --slave2-port /dev/cu.usbmodem1121201 \
  --samples-per-lead 100 \
  --timeout-seconds 210
```

只顯示最終 JSON 統計：

```bash
python -B tools/PC/hinu_motor_sync_stress_monitor.py \
  --slave1-port /dev/cu.usbmodem1121301 \
  --slave2-port /dev/cu.usbmodem1121201 \
  --samples-per-lead 100 \
  --timeout-seconds 210 \
  --quiet
```

結果以相同 `(lead, tag)` 對齊兩塊板，再比較
`abs(jitter_slave1 - jitter_slave2)`。`missing_samples` 必須為 `0`。

> 量測定義：現時 `jitter` 是每塊 Slave 相對於「本機收到 MODE_SET 後建立的 deadline」
> 的違期量。它適合發現 task wake / logging outlier，但兩塊 MCU 的 ticks 未換算成共同
> master clock，所以報告中的 `0 ms` 不能單獨當作「物理 motor 絕對同刻起動」證明。
> 若要驗收接近真正 `0 ms`，協議需要記錄共同 master-clock start timestamp，
> 或以邏輯分析儀／高速攝影同時觀測兩塊 Slave 輸出。
