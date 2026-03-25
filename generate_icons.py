#!/usr/bin/env python3
"""
generate_icons.py — ほめストック用 PWA アイコン生成
依存なし（Python 標準ライブラリのみ）で PNG を生成する。

使い方:
    python generate_icons.py
"""

import os
import struct
import zlib

# アイコン色: くすみピンク #F5A7C0
ICON_COLOR = (245, 167, 192)
# 中心の絵文字は SVG で描画（PNG には埋め込まない）
# シンプルな円形グラデーション背景アイコンを生成


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc    = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def create_png(path: str, size: int, center_color: tuple, rim_color: tuple) -> None:
    """
    グラデーション風の円形アイコン PNG を生成する（ライブラリ不要）。
    """
    # RGBA ピクセルデータを生成
    pixels = []
    half   = size / 2
    for y in range(size):
        row = []
        for x in range(size):
            dx     = x - half
            dy     = y - half
            dist   = (dx * dx + dy * dy) ** 0.5
            radius = half * 0.92      # 円の半径
            aa     = half * 0.04      # アンチエイリアス幅

            if dist > radius + aa:
                # 完全に外側 → 透明
                row += [0, 0, 0, 0]
            elif dist > radius - aa:
                # エッジ（アンチエイリアス）
                t     = (radius + aa - dist) / (2 * aa)
                alpha = int(t * 255)
                t2    = dist / radius
                r = int(center_color[0] * (1 - t2) + rim_color[0] * t2)
                g = int(center_color[1] * (1 - t2) + rim_color[1] * t2)
                b = int(center_color[2] * (1 - t2) + rim_color[2] * t2)
                row += [r, g, b, alpha]
            else:
                # 内側 → グラデーション
                t = dist / radius
                r = int(center_color[0] * (1 - t) + rim_color[0] * t)
                g = int(center_color[1] * (1 - t) + rim_color[1] * t)
                b = int(center_color[2] * (1 - t) + rim_color[2] * t)
                row += [r, g, b, 255]
        pixels.append(row)

    # 桜の花びら模様（簡易）
    blossom_cx, blossom_cy = half, half
    petal_r = size * 0.22
    petal_dist = size * 0.20
    import math
    petal_centers = [
        (blossom_cx + petal_dist * math.cos(math.radians(a)),
         blossom_cy + petal_dist * math.sin(math.radians(a)))
        for a in [270, 342, 54, 126, 198]
    ]

    for y in range(size):
        row_px = pixels[y]
        for x in range(size):
            dx   = x - blossom_cx
            dy   = y - blossom_cy
            dist = (dx * dx + dy * dy) ** 0.5
            px_idx = x * 4
            # 中心の小さな円（白）
            if dist < size * 0.06:
                row_px[px_idx:px_idx+4] = [255, 255, 255, 255]
                continue
            # 花びら
            for (pcx, pcy) in petal_centers:
                pd = ((x - pcx)**2 + (y - pcy)**2) ** 0.5
                if pd < petal_r:
                    # 白っぽい花びら色
                    t = pd / petal_r
                    pr = int(255 * (1-t) + ICON_COLOR[0] * t)
                    pg = int(240 * (1-t) + ICON_COLOR[1] * t)
                    pb = int(245 * (1-t) + ICON_COLOR[2] * t)
                    cur_a = row_px[px_idx + 3]
                    if cur_a > 0:
                        row_px[px_idx:px_idx+4] = [pr, pg, pb, cur_a]

    # PNG バイナリ組み立て (RGBA = color type 6)
    sig  = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))

    raw_rows = bytearray()
    for row in pixels:
        raw_rows.append(0)  # filter type None
        raw_rows.extend(row)

    idat = _chunk(b"IDAT", zlib.compress(bytes(raw_rows), level=6))
    iend = _chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(sig + ihdr + idat + iend)
    print(f"  生成: {path}")


if __name__ == "__main__":
    print("ほめストック アイコン生成中...")
    CENTER = (255, 220, 235)   # 明るいピンク（中心）
    RIM    = (220, 130, 165)   # 濃いピンク（外縁）

    create_png("icons/icon-192.png", 192, CENTER, RIM)
    create_png("icons/icon-512.png", 512, CENTER, RIM)
    print("完了！icons/ フォルダにアイコンが生成されました。")
