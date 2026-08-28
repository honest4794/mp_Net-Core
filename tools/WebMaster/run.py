"""WebMaster 啟動腳本。

用法 (在 tools/WebMaster 目錄下):
    python3 -B run.py            # 預設 0.0.0.0:8000
    python3 -B run.py 9000       # 自訂 port
"""
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

import uvicorn  # noqa: E402


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
