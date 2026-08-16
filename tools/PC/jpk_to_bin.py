#!/usr/bin/env python3
"""JPK → RAW Bin 轉換器 (互動式，自動偵測解像度)

用法: python jpk_to_bin.py
"""

import os, sys, struct, hashlib
from PIL import Image
import io


def jpeg_to_rgb565(image_bytes, width, height):
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)
    rgb = img.tobytes()
    out = bytearray(width * height * 2)
    pi = 0
    for i in range(width * height):
        r = rgb[pi] >> 3
        g = rgb[pi + 1] >> 2
        b = rgb[pi + 2] >> 3
        out[i * 2] = (r << 3) | (g >> 3)
        out[i * 2 + 1] = ((g & 0x07) << 5) | b
        pi += 3
    return bytes(out)


def jpeg_to_rgb888(image_bytes, width, height):
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)
    return img.tobytes()


def I(msg, defv=""):
    r = input(msg).strip()
    return r if r else defv


def main():
    print("\nJPK → RAW Bin 轉換器\n" + "=" * 45)

    inp = I("輸入 .jpk 路徑 [output.jpk]: ", "output.jpk")
    if not os.path.exists(inp):
        print("❌ 找不到: {}".format(inp))
        sys.exit(1)

    fmt = I("像素格式 1=RGB565_BE 2=RGB888 [1]: ", "1")
    rgb888 = fmt == "2"
    mode_name = "RGB888" if rgb888 else "RGB565_BE"
    suffix = "_rgb888.bin" if rgb888 else "_rgb565.bin"

    base = inp.rsplit(".", 1)[0] if "." in inp else inp
    out_default = base + suffix
    out = I("輸出路徑 [{}]: ".format(out_default), out_default)
    if os.path.exists(out):
        sz = os.path.getsize(out)
        mb = sz / 1048576
        ans = I("  ⚠️ {} 已存在 ({:.1f} MB)，覆蓋? [Y/n]: ".format(out, mb), "y").lower()
        if ans and ans != "y" and ans != "":
            print("  已取消")
            sys.exit(0)

    print("\n讀取 {} ...".format(inp))
    with open(inp, "rb") as f:
        hdr = f.read(16)
        if len(hdr) != 16 or hdr[:4] != b"JPK1":
            print("❌ 不是有效的 JPK1 檔案")
            sys.exit(1)
        count, max_size = struct.unpack_from("<II", hdr, 4)
        print("  幀數: {}  最大 JPEG: {} bytes".format(count, max_size))

        # --- 自動偵測解像度 ---
        len_raw = f.read(4)
        if len(len_raw) != 4:
            print("❌ 讀不到第一幀長度")
            sys.exit(1)
        first_n = struct.unpack("<I", len_raw)[0]
        first_jpeg = f.read(first_n)
        try:
            img = Image.open(io.BytesIO(first_jpeg))
            w, hh = img.size
            print("  自動偵測: {}x{}".format(w, hh))
            agree = I("  確認? [Y/n]: ", "y").lower()
            if agree and agree != "y" and agree != "":
                w = int(I("  寬度: ") or w)
                hh = int(I("  高度: ") or hh)
        except Exception as e:
            print("❌ 無法解碼第一幀: {}".format(e))
            sys.exit(1)

        # 重新由頭開始讀 (seek back)
        f.seek(0)
        f.read(16)  # skip JPK1 header again

        frame_size = w * hh * (3 if rgb888 else 2)
        convert_fn = jpeg_to_rgb888 if rgb888 else jpeg_to_rgb565
        print("  輸出: {}x{} {} bytes/幀 ({})".format(w, hh, frame_size, mode_name))

        total_bytes = 0
        ok_count = 0
        fail_count = 0

        with open(out, "wb") as outf:
            for idx in range(count):
                len_raw = f.read(4)
                if len(len_raw) != 4:
                    print("  ⚠️ 幀 {} 讀不到長度".format(idx))
                    break
                n = struct.unpack("<I", len_raw)[0]
                jpeg_data = f.read(n)
                if len(jpeg_data) != n:
                    print("  ⚠️ 幀 {} 不完整".format(idx))
                    break

                try:
                    raw = convert_fn(jpeg_data, w, hh)
                    if len(raw) != frame_size:
                        print("  ⚠️ 幀 {} 輸出大小異常: {} vs {}".format(idx, len(raw), frame_size))
                        fail_count += 1
                        continue
                    outf.write(raw)
                    total_bytes += frame_size
                    ok_count += 1
                except Exception as e:
                    fail_count += 1
                    if fail_count <= 3:
                        print("  ⚠️ 幀 {} 解碼失敗: {}".format(idx, e))
                    continue

                if (idx + 1) % 200 == 0:
                    print("  ... {}/{} ({:.1f}%)".format(
                        idx + 1, count, (idx + 1) * 100 / count))

        print("\n✅ 轉換完成: {} 幀, {} bytes ({:.1f} MB)".format(
            ok_count, total_bytes, total_bytes / 1048576))
        if fail_count:
            print("⚠️ {} 幀跳過".format(fail_count))

        sha = hashlib.sha256()
        with open(out, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                sha.update(chunk)
        print("SHA256: {}".format(sha.hexdigest()))

    print("\n已完成 → {}".format(os.path.abspath(out)))
    print("用 storage_tool.py → 5 刪除舊 bin → 4 上傳此檔 → ESP32 reboot")


if __name__ == "__main__":
    main()
