# Agent 執行規則

## USB upload／monitor port

- Master／Slave 的 USB port 以每次操作前的實際列舉為準；設定檔不保存 upload／monitor port。
- 每次 MicroPython upload／monitor 命令都明確傳入已核對的 port，例如 `mpremote connect <port> ...` 或 serial monitor 的 `--port <port>`；不得由舊紀錄推斷目前板身份。

- 執行任何 Python 程式時，一律加上 `-B` 旗標（例如 `python -B xxx.py`），或先設定環境變數 `PYTHONDONTWRITEBYTECODE=1`
- 禁止在專案目錄內產生 `__pycache__` 資料夾或 `*.pyc` 檔案
- 若不慎產生，請在結束前自行清除：
  ```bash
  find . -type d -name __pycache__ -exec rm -rf {} +
  ```
