"""WebMaster 協議層：封裝 mp_Net-Core 的 NC4 協議 (slave/lib/sys)。

復用 slave 韌體同一套 schema/proto/schema_codec, 保證與設備端二進制封包完全一致。
- SchemaStore 載入 slave/schema/*.json 後必須 finalize() (否則 decode 欄位全空)。
- Proto.pack() 回傳「指向共享 buffer 的 memoryview」, 下一次 pack 會覆蓋它 —
  呼叫端必須「立即消費」(send 出去), 不可跨 await 持有。這對 async WebSocket 是關鍵約束。
"""
import os
import sys

# slave 韌體部署到根目錄時 lib/ 是頂層套件 (from lib.sys.xxx); 這裡把 slave/ 放進 sys.path
_SLAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "slave"))
if _SLAVE_DIR not in sys.path:
    sys.path.insert(0, _SLAVE_DIR)

from lib.sys.proto import Proto, StreamParser          # noqa: E402
from lib.sys.schema_loader import SchemaStore          # noqa: E402
from lib.sys.schema_codec import SchemaCodec           # noqa: E402


SCHEMA_DIR = os.path.join(_SLAVE_DIR, "schema")


class Protocol:
    """NC4 協議封裝 (pack / unpack + 命令名稱對照)。"""

    def __init__(self, schema_dir=None):
        self.store = SchemaStore(dir_path=schema_dir or SCHEMA_DIR)
        self.store.finalize()

    def pack(self, cmd_id, args):
        """把 dict 打包成 NC4 幀 (memoryview, 需立即消費)。cmd_id 可為 int 或 "0x3001"。"""
        if isinstance(cmd_id, str) and cmd_id.lower().startswith("0x"):
            cmd_id = int(cmd_id, 16)
        cmd_def = self.store.get(int(cmd_id))
        if cmd_def is None:
            raise ValueError(f"Unknown command: {cmd_id}")
        payload = SchemaCodec.encode(cmd_def, args)
        return Proto.pack(int(cmd_id), payload)

    def unpack(self, cmd_id, payload_bytes):
        """把 payload 解成 dict (含欄位名)。cmd_id 為 int。"""
        cmd_def = self.store.get(int(cmd_id))
        if cmd_def is None:
            return None
        return SchemaCodec.decode(cmd_def, payload_bytes, store=self.store)

    def name(self, cmd_id):
        cmd_def = self.store.get(int(cmd_id))
        return cmd_def.get("name") if cmd_def else None


# 單例
protocol = Protocol()
