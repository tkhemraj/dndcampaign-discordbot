"""Render tile maps to PNG via Pillow."""
from __future__ import annotations
import io
from PIL import Image, ImageDraw

TILE_COLOURS = {
    0:  (18, 18, 24),
    1:  (44, 40, 34),
    2:  (120, 80, 40),
    3:  (30, 60, 120),
    4:  (180, 60, 10),
    5:  (20, 70, 20),
    6:  (80, 70, 55),
    7:  (65, 58, 50),
    8:  (50, 45, 45),
    9:  (180, 140, 20),
    10: (100, 90, 110),
    11: (180, 30, 30),
    12: (30, 90, 30),
    13: (160, 130, 80),
    14: (180, 200, 220),
}

TILE_ICONS = {2: "D", 9: "C", 10: "↑", 11: "!"}
TILE_SIZE = 16


def render(map_data: dict, tile_px: int = TILE_SIZE) -> io.BytesIO:
    tiles = map_data["tiles"]
    h, w = len(tiles), len(tiles[0]) if tiles else 0
    img = Image.new("RGB", (w * tile_px, h * tile_px), TILE_COLOURS[0])
    draw = ImageDraw.Draw(img)

    for row_i, row in enumerate(tiles):
        for col_i, tile_id in enumerate(row):
            colour = TILE_COLOURS.get(tile_id, TILE_COLOURS[0])
            x0, y0 = col_i * tile_px, row_i * tile_px
            draw.rectangle([x0, y0, x0 + tile_px - 1, y0 + tile_px - 1], fill=colour)
            icon = TILE_ICONS.get(tile_id)
            if icon and tile_px >= 12:
                draw.text((x0 + tile_px // 2, y0 + tile_px // 2), icon, fill=(240, 220, 180), anchor="mm")

    if tile_px >= 8:
        for col_i in range(w + 1):
            draw.line([(col_i * tile_px, 0), (col_i * tile_px, h * tile_px)], fill=(0, 0, 0), width=1)
        for row_i in range(h + 1):
            draw.line([(0, row_i * tile_px), (w * tile_px, row_i * tile_px)], fill=(0, 0, 0), width=1)

    if tile_px >= 12:
        for room in map_data.get("rooms", []):
            if room.get("w", 0) >= 4 and room.get("h", 0) >= 4:
                cx = (room["x"] + room["w"] // 2) * tile_px
                cy = (room["y"] + room["h"] // 2) * tile_px
                draw.text((cx, cy), room.get("type", "")[:8], fill=(200, 180, 140), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def scale_for_discord(map_data: dict, max_px: int = 1024) -> io.BytesIO:
    tiles = map_data.get("tiles", [[]])
    w = len(tiles[0]) if tiles else 1
    h = len(tiles)
    tile_px = max(4, min(max_px // max(w, 1), max_px // max(h, 1), TILE_SIZE))
    return render(map_data, tile_px=tile_px)
