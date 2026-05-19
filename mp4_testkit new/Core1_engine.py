import time
import micropython

from lib.tail_codec import read_u32_le, write_u32_le


@micropython.viper
def _viper_copy(dst, src, n: int):
    d = ptr8(dst)
    s = ptr8(src)
    for i in range(n):
        d[i] = s[i]


def _yield():
    time.sleep_ms(0)


def _decode_jpeg_blocks(decoder, jpeg_data, block_hub, block_buffer_size, frame_idx):
    info = decoder.get_img_info(jpeg_data)
    total_blocks = int(info[2])

    for bi in range(total_blocks):
        block = decoder.decode(jpeg_data)
        if block is None:
            break

        block_len = len(block)
        out_view = block_hub.get_write_view()
        while out_view is None:
            out_view = block_hub.get_write_view()
            _yield()

        _viper_copy(out_view, block, block_len)
        tail_off = block_buffer_size
        write_u32_le(out_view, tail_off + 0, bi)
        write_u32_le(out_view, tail_off + 4, block_len)
        write_u32_le(out_view, tail_off + 8, total_blocks)
        write_u32_le(out_view, tail_off + 12, frame_idx)
        block_hub.commit()


def task_loop(bus):
    io_hub = bus.get_service("io_hub")
    block_hub = bus.get_service("block_hub")
    decoder = bus.get_service("decoder")
    jpeg_cache = bus.get_service("jpeg_cache")
    if bool(bus.shared.get("debug", False)):
        if jpeg_cache is None:
            print("[Engine] jpeg_cache: None")
        else:
            print("[Engine] jpeg_cache:", len(jpeg_cache))
        if block_hub is not None:
            print("[Engine] block streaming mode")

    max_jpeg_bytes = int(bus.shared.get("max_jpeg_bytes", 0) or 0)
    frame_bytes = int(bus.shared.get("frame_bytes", 0) or 0)
    block_buffer_size = int(bus.shared.get("block_buffer_size", 0) or 0)

    bus.shared["core1_ready"] = True

    cache_idx = 0
    while bus.shared.get("engine_run", True):
        if jpeg_cache is not None and bool(bus.shared.get("cache_active", False)):
            pace_frames = int(bus.shared.get("pace_frames", 1) or 1)
            if pace_frames < 1:
                pace_frames = 1

            frame_idx, in_buf, n = jpeg_cache[cache_idx]
            t0 = time.ticks_us()
            try:
                if block_hub is not None:
                    _decode_jpeg_blocks(decoder, in_buf[:n], block_hub, block_buffer_size, frame_idx)
                else:
                    frame_hub = bus.get_service("frame_hub")
                    out_view = frame_hub.get_write_view()
                    while out_view is None:
                        out_view = frame_hub.get_write_view()
                        _yield()
                    decoder.decode_into(in_buf[:n], out_view[:frame_bytes])
                    hdr_off = frame_bytes
                    write_u32_le(out_view, hdr_off + 0, frame_idx)
                    write_u32_le(out_view, hdr_off + 4, 0)
                    write_u32_le(out_view, hdr_off + 8, 0)
                    write_u32_le(out_view, hdr_off + 12, n)
                    frame_hub.commit()
            except Exception:
                _yield()
                cache_idx += pace_frames
                if cache_idx >= len(jpeg_cache):
                    cache_idx = 0
                    bus.shared["cache_active"] = False
                continue
            t1 = time.ticks_us()

            cache_idx += pace_frames
            if cache_idx >= len(jpeg_cache):
                cache_idx = 0
                bus.shared["cache_active"] = False
            continue

        in_view = io_hub.get_read_view()
        if in_view is None:
            _yield()
            continue

        tail_off = max_jpeg_bytes
        frame_idx = read_u32_le(in_view, tail_off + 0)
        n = read_u32_le(in_view, tail_off + 4)
        read_us = read_u32_le(in_view, tail_off + 8)

        if n <= 0:
            io_hub.release_read()
            _yield()
            continue

        t0 = time.ticks_us()
        try:
            if block_hub is not None:
                _decode_jpeg_blocks(decoder, in_view[:n], block_hub, block_buffer_size, frame_idx)
            else:
                frame_hub = bus.get_service("frame_hub")
                out_view = frame_hub.get_write_view()
                while out_view is None:
                    out_view = frame_hub.get_write_view()
                    _yield()
                decoder.decode_into(in_view[:n], out_view[:frame_bytes])
                hdr_off = frame_bytes
                write_u32_le(out_view, hdr_off + 0, frame_idx)
                write_u32_le(out_view, hdr_off + 4, 0)
                write_u32_le(out_view, hdr_off + 8, read_us)
                write_u32_le(out_view, hdr_off + 12, n)
                frame_hub.commit()
        except Exception:
            io_hub.release_read()
            _yield()
            continue
        t1 = time.ticks_us()
        io_hub.release_read()
