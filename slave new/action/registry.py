# /action/registry.py
# 統一註冊入口：把各 action 模組掛上去

from lib.sys_bus import bus
from action import file_actions
# from action import fs_actions
from action import status_actions
from action import stream_actions
from action import sys_actions
from action import heartbeat_actions
from action import ram_bench_actions
from action import now_actions
from action import hw_actions
from action import waiting_to_trash_actions

# jpeg_actions 依賴 TFT/LCD(播放器寫 LCD),沒有 LCD 時跳過整段 import
# (沒接 TFT 時 import 仍會成功,但播放毫無意義且可能拖垮雙核心啟動)。
_HAS_LCD = bus.has_lcd()
if _HAS_LCD:
    from action import jpeg_actions

def register_all(app):
    file_actions.register(app)
#     fs_actions.register(app)
    status_actions.register(app)
    stream_actions.register(app)
    sys_actions.register(app)
    heartbeat_actions.register(app)
    ram_bench_actions.register(app)
    if _HAS_LCD:
        jpeg_actions.register(app)
    else:
        print("[Action] ⏭ jpeg_actions skipped — no LCD/TFT on bus")
    now_actions.register(app)
    hw_actions.register(app)
    waiting_to_trash_actions.register(app)
