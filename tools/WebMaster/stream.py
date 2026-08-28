"""WebMaster 串流控制 + RAM 實時播放。

命令對應 slave 端 stream_actions / stream_task:
  0x3009 STREAM_STATE_SET  準備檔案 (file_name 可帶 /ram/xxx)
  0x300A STREAM_PLAY       開始播放 (start_frame 中途加入)
  0x3005 STREAM_PAUSE      暫停/恢復
  0x3002 STREAM_STOP       停止
  0x3004 STREAM_SEEK       跳轉
  0x3001 STREAM_INFO       同步 fps
"""
import logging

log = logging.getLogger("webmaster.stream")


async def prepare(dev, file_name, block_id=0, play_mode=0):
    await dev.send(0x3009, {
        "file_name": file_name,
        "block_id": block_id,
        "play_mode": play_mode,
    })


async def play(dev, start_frame=0):
    await dev.send(0x300A, {"start_frame": start_frame})


async def pause(dev, paused=True):
    await dev.send(0x3005, {"pause": 1 if paused else 0})


async def stop(dev):
    await dev.send(0x3002, {})


async def seek(dev, target_frame):
    await dev.send(0x3004, {"target_block": 0, "target_frame": target_frame})


async def set_fps(dev, fps):
    await dev.send(0x3001, {
        "total_blocks": 0,
        "frames_per_block": 0,
        "fps": int(fps),
    })
