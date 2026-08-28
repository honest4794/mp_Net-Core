"""WebMaster 音訊 (MP3) 支援。

MP3 解碼/播放交給「瀏覽器原生 <audio>」, 本模組只負責:
  1. 列出 server media 目錄下的 MP3 檔
  2. 提供播放同步訊號的延遲調校值 (delay_ms) 給前端
  3. (前端播 <audio> 時, 經 WS 對 slave 下燈效同步指令)

後端零音訊依賴 (不需 ffmpeg/pyaudio)。
"""
import os
import logging

log = logging.getLogger("webmaster.audio")

MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "media"))


def list_mp3():
    """列出 media 目錄下的 .mp3 檔 (相對路徑清單)。"""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    result = []
    for name in sorted(os.listdir(MEDIA_DIR)):
        if name.lower().endswith(".mp3"):
            result.append({"name": name, "size": os.path.getsize(os.path.join(MEDIA_DIR, name))})
    return result


def resolve_mp3(name):
    """安全解析 mp3 路徑 (只允許在 MEDIA_DIR 內)。回傳絕對路徑或 None。"""
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    path = os.path.join(MEDIA_DIR, name)
    if os.path.isfile(path) and path.lower().endswith(".mp3"):
        return path
    return None
