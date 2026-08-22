# Agent 執行規則

- 執行任何 Python 程式時，一律加上 `-B` 旗標（例如 `python -B xxx.py`），或先設定環境變數 `PYTHONDONTWRITEBYTECODE=1`
- 禁止在專案目錄內產生 `__pycache__` 資料夾或 `*.pyc` 檔案
- 若不慎產生，請在結束前自行清除：
  ```bash
  find . -type d -name __pycache__ -exec rm -rf {} +
  ```
