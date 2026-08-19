# app.py
from lib.schema_loader import SchemaStore
from lib.dispatch import Dispatcher
from lib.proto import StreamParser, MAX_PAYLOAD
# from lib.file_rx import FileRx # 已移除
from action.registry import register_all
from lib.sys_bus import bus

class App:
    def __init__(self):
        # 1. 核心組件
        self.store = SchemaStore()
        self.store.load_dir("/schema")
        self.store.finalize()
        self.disp = Dispatcher(self.store)

        # 3. 註冊行為
        register_all(self)

    def create_parser(self):
        # 協議負載上限統一由 lib.proto.MAX_PAYLOAD 決定 (純 payload, 不含 header/CRC)。
        # StreamParser 內部會自動加 9B header + 4B CRC 建立緩衝, 這裡不需再乘 2。
        return StreamParser(max_len=MAX_PAYLOAD)

    def handle_stream(self, parser, data, transport_name="Bus", send_func=None, **kwargs):
        """
        處理數據流，並確保解析出當前 buffer 內所有的封包
        """
        parser.feed(data)
        
        ctx = {
            "app": self,
            "transport": transport_name,
            "send": send_func
        }
        ctx.update(kwargs)
        
        # 🛠️ 關鍵：這是一個生成器，必須用 for 跑完
        packet_found = False
        for ver, addr, cmd, payload in parser.pop():
            packet_found = True
            self.disp.dispatch(cmd, payload, ctx)
        return packet_found