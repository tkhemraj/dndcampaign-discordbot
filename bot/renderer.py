"""
Render tile maps to PNG via Pillow.

Enhanced renderer ported from the dndcampaign web app — adds theme palettes,
ambient occlusion, wall ink outlines, detailed feature shapes (doors, pillars,
chests, stairs, traps, water, trees, rubble, lava), room labels with background
boxes, a compass rose, and an edge vignette.
"""
from __future__ import annotations
import io
import math
import random as _rnd
from PIL import Image, ImageDraw

# ── Tile IDs ────────────────────────────────────────────────────────────────────
WALL   = 0;  FLOOR  = 1;  DOOR   = 2;  WATER  = 3;  LAVA   = 4
TREES  = 5;  ROAD   = 6;  RUBBLE = 7;  PILLAR = 8;  CHEST  = 9
STAIRS = 10; TRAP   = 11; GRASS  = 12; DIRT   = 13; SNOW   = 14

FEATURE_TILES = {DOOR, PILLAR, CHEST, STAIRS, TRAP}
TERRAIN_TILES = {WATER, LAVA, TREES, ROAD, RUBBLE, GRASS, DIRT, SNOW}

# ── Theme palettes ──────────────────────────────────────────────────────────────
# void  = wall colour     room  = room floor colour
# corr  = corridor colour ink   = wall outline colour
# hi    = edge highlight  accent = feature tint
# label = room label text colour

THEMES: dict[str, dict] = {
    "standard":     dict(void=(18,18,24),    room=(62,54,42),     corr=(48,42,34),     ink=(5,3,2),      hi=(90,72,52),     accent=(120,80,40),   label=(200,180,140)),
    "generic":      dict(void=(18,18,24),    room=(62,54,42),     corr=(48,42,34),     ink=(5,3,2),      hi=(90,72,52),     accent=(120,80,40),   label=(200,180,140)),
    "cave":         dict(void=(14,12,10),    room=(54,46,38),     corr=(42,36,28),     ink=(7,6,5),      hi=(82,70,54),     accent=(80,60,40),    label=(200,180,150)),
    "crypt":        dict(void=(12,10,14),    room=(50,44,48),     corr=(38,32,38),     ink=(6,4,8),      hi=(80,68,78),     accent=(100,60,80),   label=(180,160,180)),
    "underdark":    dict(void=(8,8,14),      room=(38,36,50),     corr=(28,26,40),     ink=(4,4,10),     hi=(60,55,80),     accent=(30,100,160),  label=(140,135,190)),
    "bazzoxan":     dict(void=(8,8,14),      room=(38,36,50),     corr=(28,26,40),     ink=(4,4,10),     hi=(60,55,80),     accent=(30,100,160),  label=(140,135,190)),
    "sewers":       dict(void=(10,14,10),    room=(42,50,38),     corr=(32,40,28),     ink=(5,8,5),      hi=(65,80,58),     accent=(20,90,40),    label=(150,195,140)),
    "cerberus_lab": dict(void=(10,10,20),    room=(42,40,58),     corr=(32,30,48),     ink=(5,5,12),     hi=(70,65,95),     accent=(88,101,242),  label=(155,150,220)),
    "ruins_aeor":   dict(void=(12,14,18),    room=(46,50,58),     corr=(36,38,46),     ink=(6,7,9),      hi=(75,80,95),     accent=(60,90,160),   label=(175,185,210)),
    "temple":       dict(void=(14,12,10),    room=(58,50,40),     corr=(44,38,30),     ink=(7,6,5),      hi=(88,75,58),     accent=(140,100,30),  label=(210,190,155)),
    "tundra":       dict(void=(80,90,100),   room=(200,210,220),  corr=(180,192,205),  ink=(60,70,80),   hi=(230,235,240),  accent=(120,140,160), label=(60,70,80)),
    "forest":       dict(void=(10,20,10),    room=(32,72,28),     corr=(28,56,22),     ink=(5,10,5),     hi=(50,95,40),     accent=(60,120,50),   label=(180,220,150)),
    "coastal":      dict(void=(15,25,15),    room=(35,68,30),     corr=(30,58,25),     ink=(6,10,5),     hi=(55,90,45),     accent=(30,80,120),   label=(180,215,180)),
    "badlands":     dict(void=(40,30,20),    room=(100,80,55),    corr=(85,68,45),     ink=(20,15,10),   hi=(130,105,70),   accent=(160,80,20),   label=(220,190,140)),
    "plains":       dict(void=(20,35,18),    room=(40,78,32),     corr=(55,88,45),     ink=(10,18,8),    hi=(80,120,60),    accent=(80,110,50),   label=(200,230,160)),
    "jungle":       dict(void=(8,16,8),      room=(28,65,24),     corr=(22,52,18),     ink=(4,8,4),      hi=(45,90,35),     accent=(50,110,40),   label=(160,210,130)),
    "wastes":       dict(void=(40,30,20),    room=(100,80,55),    corr=(85,68,45),     ink=(20,15,10),   hi=(130,105,70),   accent=(180,60,10),   label=(220,190,140)),
    "mountain":     dict(void=(50,50,60),    room=(110,105,115),  corr=(90,88,98),     ink=(25,25,30),   hi=(145,140,150),  accent=(80,90,120),   label=(200,200,220)),
    "savalirwood":  dict(void=(8,16,8),      room=(28,65,24),     corr=(22,52,18),     ink=(4,8,4),      hi=(45,90,35),     accent=(60,120,50),   label=(160,215,130)),
}

_WILDEMOUNT_THEME_MAP: dict[str, str] = {
    "aeor_ruins":      "ruins_aeor",
    "kryn_temple":     "temple",
    "dwendalian_keep": "standard",
    "rosohna":         "crypt",
    "xhorhas_wastes":  "badlands",
    "menagerie_port":  "coastal",
    "eiselcross":      "tundra",
    "savalirwood":     "savalirwood",
    "cerberus_lab":    "cerberus_lab",
    "bazzoxan":        "bazzoxan",
    "underdark":       "underdark",
}

def _theme_for(map_data: dict) -> dict:
    sub = map_data.get("subtype", "")
    if sub in THEMES:
        return THEMES[sub]
    # Wildemount subtypes that don't match THEMES directly
    if sub in _WILDEMOUNT_THEME_MAP:
        return THEMES[_WILDEMOUNT_THEME_MAP[sub]]
    mtype = map_data.get("map_type", "dungeon")
    if mtype in ("outdoor", "wildemount"):
        if "tundra" in sub or "eiselcross" in sub:
            return THEMES["tundra"]
        if "coastal" in sub or "port" in sub:
            return THEMES["coastal"]
        if "savalir" in sub:
            return THEMES["savalirwood"]
        if "forest" in sub:
            return THEMES["forest"]
        if "waste" in sub or "xhorhas" in sub or "badlands" in sub:
            return THEMES["badlands"]
        if "mountain" in sub:
            return THEMES["mountain"]
        return THEMES["plains"]
    return THEMES["standard"]


TILE_SIZE = 16


# ── Feature drawing helpers ─────────────────────────────────────────────────────

def _rng_for(px: int, py: int) -> _rnd.Random:
    return _rnd.Random(px * 1000003 + py)


def _draw_door(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    dw = max(4, int(ts * 0.55)); dh = max(5, int(ts * 0.80))
    dx = px + (ts - dw) // 2; dy = py + (ts - dh) // 2
    draw.rectangle([dx + 1, dy + 1, dx + dw + 1, dy + dh + 1], fill=(0, 0, 0, 90))
    draw.rectangle([dx, dy, dx + dw, dy + dh], fill=(90, 46, 16))
    top_h = max(1, int(dh * 0.38))
    draw.rectangle([dx, dy, dx + dw, dy + top_h], fill=(62, 32, 8))
    draw.rectangle([dx + 2, dy + top_h + 1, dx + dw - 2, dy + dh - 2], fill=(72, 34, 8))
    kx = dx + int(dw * 0.75); ky = dy + dh // 2
    draw.ellipse([kx - 2, ky - 2, kx + 2, ky + 2], fill=(200, 151, 60))
    draw.rectangle([dx, dy, dx + dw, dy + dh], outline=(26, 8, 4), width=1)


def _draw_pillar(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    m = px + ts // 2; n = py + ts // 2
    r = max(3, int(ts * 0.35))
    draw.ellipse([m - r + 2, n - r + 2, m + r + 2, n + r + 2], fill=(0, 0, 0, 80))
    draw.ellipse([m - r, n - r, m + r, n + r], fill=(76, 48, 24))
    rm = max(2, int(r * 0.7))
    draw.ellipse([m - rm, n - rm, m + rm, n + rm], fill=(160, 124, 82))
    rh = max(1, int(r * 0.35))
    draw.ellipse([m - r + 2, n - r + 2, m - r + 2 + rh, n - r + 2 + rh], fill=(214, 186, 142))
    draw.ellipse([m - r, n - r, m + r, n + r], outline=(200, 162, 105), width=1)


def _draw_chest(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    m = px + ts // 2; n = py + ts // 2
    cw = max(5, int(ts * 0.58)); ch = max(4, int(ts * 0.44))
    cx = m - cw // 2; cy = n - ch // 2 - 1
    draw.rectangle([cx + 1, cy + 1, cx + cw + 1, cy + ch + 1], fill=(0, 0, 0, 80))
    draw.rectangle([cx, cy, cx + cw, cy + ch], fill=(92, 50, 18))
    draw.rectangle([cx, cy, cx + cw, cy + int(ch * 0.38)], fill=(62, 32, 8))
    latch_y = cy + int(ch * 0.41)
    draw.line([cx + 2, latch_y, cx + cw - 2, latch_y], fill=(200, 151, 60), width=2)
    draw.ellipse([m - 3, latch_y - 2, m + 3, latch_y + 4], fill=(240, 192, 64))
    draw.rectangle([cx, cy, cx + cw, cy + ch], outline=(26, 8, 4), width=1)


def _draw_stairs(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    sw = max(6, int(ts * 0.68)); sh = max(5, int(ts * 0.62))
    x0 = px + (ts - sw) // 2; y0 = py + (ts - sh) // 2
    ns = 5
    for si in range(ns):
        shrink = si * sw // (ns * 10)
        sx = x0 + shrink; sw2 = sw - shrink * 2
        sy = int(y0 + si * sh / ns); sh2 = max(1, int(sh * 0.72 / ns))
        col = (140, 108, 72) if si % 2 == 0 else (156, 124, 88)
        draw.rectangle([sx, sy, sx + sw2, sy + sh2], fill=col)
        draw.line([sx, sy + sh2, sx + sw2, sy + sh2], fill=(0, 0, 0, 60), width=1)


def _draw_trap(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    m = px + ts // 2; n = py + ts // 2
    for i, r in enumerate([int(ts * 0.42), int(ts * 0.28), int(ts * 0.14)]):
        if r < 1:
            continue
        alpha = 55 + i * 40
        draw.ellipse([m - r, n - r, m + r, n + r], outline=(165, 45, 45, alpha), width=1)
    draw.ellipse([m - 2, n - 2, m + 2, n + 2], fill=(165, 45, 45, 200))


def _draw_water(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    for yi in range(ts):
        t = yi / max(1, ts)
        draw.line([px, py + yi, px + ts - 1, py + yi],
                  fill=(int(30 + t * 8), int(60 + t * 12), int(120 + t * 18)))
    # Wave highlights
    for wi in range(min(3, ts // 4)):
        wy = py + int((wi + 0.65) * ts / 3.1)
        pts = [(px + xi, wy + int(math.sin((px + xi + wi) * 0.85) * 1.5)) for xi in range(ts)]
        if len(pts) >= 2:
            draw.line(pts, fill=(120, 200, 255, 55), width=1)


def _draw_lava(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(56, 9, 2))
    rng = _rng_for(px, py)
    for _ in range(3):
        x1 = px + int(rng.random() * ts); y1 = py + int(rng.random() * ts)
        x2 = px + int(rng.random() * ts); y2 = py + int(rng.random() * ts)
        draw.line([x1, y1, x2, y2], fill=(255, 85, 0, 180), width=1)


def _draw_trees(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(20, 50, 16))
    rng = _rng_for(px, py)
    count = 1 + int(rng.random() > 0.58)
    for ti in range(count):
        tcx = px + 4 + int(rng.random() * max(1, ts - 8))
        tcy = py + 4 + int(rng.random() * max(1, ts - 8))
        trad = max(2, 4 + int(rng.random() * 5))
        green = 72 + int(rng.random() * 45)
        draw.ellipse([tcx - trad, tcy - trad, tcx + trad, tcy + trad], fill=(22, green, 15))
        sh = max(1, int(trad * 0.52))
        draw.ellipse([tcx - sh + 1, tcy - sh + 1, tcx + sh + 1, tcy + sh + 1], fill=(0, 0, 0, 55))


def _draw_rubble(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(58, 46, 30))
    rng = _rng_for(px, py)
    for ri in range(4):
        rfx = px + int(rng.random() * ts); rfy = py + int(rng.random() * ts)
        rfw = max(1, 2 + int(rng.random() * 4)); rfh = max(1, 1 + int(rng.random() * 3))
        draw.rectangle([rfx, rfy, rfx + rfw, rfy + rfh],
                       fill=(95, 78, 55) if ri % 2 == 0 else (48, 38, 25))


def _draw_grass(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    gv = _rng_for(px, py).random()
    draw.rectangle([px, py, px + ts - 1, py + ts - 1],
                   fill=(int(28 + gv * 14), int(72 + gv * 32), int(18 + gv * 10)))


def _draw_dirt(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    dv = _rng_for(px, py).random()
    draw.rectangle([px, py, px + ts - 1, py + ts - 1],
                   fill=(int(130 + dv * 22), int(100 + dv * 18), int(60 + dv * 14)))


def _draw_snow(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    sv = _rng_for(px, py).random()
    draw.rectangle([px, py, px + ts - 1, py + ts - 1],
                   fill=(min(255, int(208 + sv * 42)), min(255, int(215 + sv * 35)), min(255, int(225 + sv * 28))))


def _draw_compass_rose(draw: ImageDraw.ImageDraw, cx: int, cy: int, sz: int, pal: dict) -> None:
    acc = pal.get("accent", (180, 140, 60))
    dim = tuple(max(0, c - 50) for c in acc)
    lbl = pal.get("label", (200, 180, 140))
    h4 = sz // 4
    # N — bright
    draw.polygon([(cx, cy - sz), (cx - h4, cy), (cx, cy - sz // 3)], fill=acc)
    draw.polygon([(cx, cy - sz), (cx + h4, cy), (cx, cy - sz // 3)], fill=dim)
    # S — dimmer
    draw.polygon([(cx, cy + sz), (cx - h4, cy), (cx, cy + sz // 3)], fill=dim)
    draw.polygon([(cx, cy + sz), (cx + h4, cy), (cx, cy + sz // 3)], fill=tuple(max(0, c - 30) for c in dim))
    # E
    draw.polygon([(cx + sz, cy), (cx, cy - h4), (cx + sz // 3, cy)], fill=dim)
    draw.polygon([(cx + sz, cy), (cx, cy + h4), (cx + sz // 3, cy)], fill=tuple(max(0, c - 20) for c in dim))
    # W
    draw.polygon([(cx - sz, cy), (cx, cy - h4), (cx - sz // 3, cy)], fill=dim)
    draw.polygon([(cx - sz, cy), (cx, cy + h4), (cx - sz // 3, cy)], fill=tuple(max(0, c - 20) for c in dim))
    # Centre dot
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=lbl)
    # N label
    draw.text((cx, cy - sz - 4), "N", fill=lbl, anchor="mb")


# ── Main render function ────────────────────────────────────────────────────────

def _in_room(tx: int, ty: int, rooms: list[dict]) -> bool:
    return any(r["x"] <= tx < r["x"] + r["w"] and r["y"] <= ty < r["y"] + r["h"] for r in rooms)


def render(map_data: dict, tile_px: int = TILE_SIZE) -> io.BytesIO:
    tiles = map_data["tiles"]
    h = len(tiles); w = len(tiles[0]) if h else 0
    rooms = map_data.get("rooms", [])
    img_w, img_h = w * tile_px, h * tile_px
    pal = _theme_for(map_data)

    img = Image.new("RGBA", (img_w, img_h), (*pal["void"], 255))
    draw = ImageDraw.Draw(img)

    # ── Pass 1: base tiles ────────────────────────────────────────────────────
    for ry, row in enumerate(tiles):
        for rx, t in enumerate(row):
            if t == WALL:
                continue
            px, py = rx * tile_px, ry * tile_px
            in_room = _in_room(rx, ry, rooms) if rooms else True

            if t in (FLOOR, *FEATURE_TILES):
                col = pal["room"] if in_room else pal["corr"]
                draw.rectangle([px, py, px + tile_px - 1, py + tile_px - 1], fill=col)
            elif t == WATER:
                _draw_water(draw, px, py, tile_px)
            elif t == LAVA:
                _draw_lava(draw, px, py, tile_px)
            elif t == TREES:
                _draw_trees(draw, px, py, tile_px)
            elif t == ROAD:
                draw.rectangle([px, py, px + tile_px - 1, py + tile_px - 1], fill=(138, 117, 88))
            elif t == RUBBLE:
                _draw_rubble(draw, px, py, tile_px)
            elif t == GRASS:
                _draw_grass(draw, px, py, tile_px)
            elif t == DIRT:
                _draw_dirt(draw, px, py, tile_px)
            elif t == SNOW:
                _draw_snow(draw, px, py, tile_px)

    # ── Pass 2: ambient occlusion (darken floor tiles adjacent to walls) ──────
    if tile_px >= 8:
        ao = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        ao_draw = ImageDraw.Draw(ao)
        ao_depth = max(2, int(tile_px * 0.5))
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                neighbours = [
                    (0, -1, px, py, px + tile_px - 1, py + ao_depth),
                    (0,  1, px, py + tile_px - ao_depth, px + tile_px - 1, py + tile_px - 1),
                    (-1, 0, px, py, px + ao_depth, py + tile_px - 1),
                    (1,  0, px + tile_px - ao_depth, py, px + tile_px - 1, py + tile_px - 1),
                ]
                for nx, ny, x0, y0, x1, y1 in [
                    (rx + dx, ry + dy, *rect)
                    for dx, dy, *rect in neighbours
                ]:
                    if 0 <= ny < h and 0 <= nx < w and tiles[ny][nx] == WALL:
                        for si in range(ao_depth):
                            alpha = int(100 * (1 - si / ao_depth))
                            ao_draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, alpha // ao_depth))
        img = Image.alpha_composite(img, ao)
        draw = ImageDraw.Draw(img)

    # ── Pass 3: feature overlays ──────────────────────────────────────────────
    if tile_px >= 8:
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t not in FEATURE_TILES:
                    continue
                px, py = rx * tile_px, ry * tile_px
                if t == DOOR:
                    _draw_door(draw, px, py, tile_px)
                elif t == PILLAR:
                    _draw_pillar(draw, px, py, tile_px)
                elif t == CHEST:
                    _draw_chest(draw, px, py, tile_px)
                elif t == STAIRS:
                    _draw_stairs(draw, px, py, tile_px)
                elif t == TRAP:
                    _draw_trap(draw, px, py, tile_px)

    # ── Pass 4: ink wall outlines ─────────────────────────────────────────────
    if tile_px >= 6:
        ink = pal["ink"]; hi = pal["hi"]

        def is_open(nx, ny):
            return 0 <= ny < h and 0 <= nx < w and tiles[ny][nx] != WALL

        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                if is_open(rx, ry + 1):
                    draw.line([(px, py + tile_px), (px + tile_px, py + tile_px)], fill=ink, width=2)
                    draw.line([(px, py + tile_px - 1), (px + tile_px, py + tile_px - 1)], fill=hi, width=1)
                if is_open(rx, ry - 1):
                    draw.line([(px, py), (px + tile_px, py)], fill=ink, width=2)
                if is_open(rx + 1, ry):
                    draw.line([(px + tile_px, py), (px + tile_px, py + tile_px)], fill=ink, width=2)
                if is_open(rx - 1, ry):
                    draw.line([(px, py), (px, py + tile_px)], fill=ink, width=2)

    # ── Pass 5: subtle grid ────────────────────────────────────────────────────
    if tile_px >= 8:
        gl = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gc = (0, 0, 0, 18)
        for xi in range(w + 1):
            gd.line([(xi * tile_px, 0), (xi * tile_px, img_h)], fill=gc, width=1)
        for yi in range(h + 1):
            gd.line([(0, yi * tile_px), (img_w, yi * tile_px)], fill=gc, width=1)
        img = Image.alpha_composite(img, gl)
        draw = ImageDraw.Draw(img)

    # ── Pass 6: room labels with background box ────────────────────────────────
    if tile_px >= 12:
        lbl_col = pal.get("label", (200, 180, 140))
        for room in rooms:
            rw_r, rh_r = room.get("w", 0), room.get("h", 0)
            rt = room.get("type", room.get("room_type", ""))
            if rw_r < 4 or rh_r < 4 or not rt:
                continue
            cx = (room["x"] + rw_r // 2) * tile_px
            cy = (room["y"] + rh_r // 2) * tile_px
            text = rt.replace("_", " ")[:12]
            fs = max(7, int(tile_px * 0.38))
            tw = len(text) * (fs // 2 + 1) + 6; th = fs + 6
            draw.rectangle([cx - tw // 2, cy - th // 2, cx + tw // 2, cy + th // 2],
                           fill=(10, 8, 5, 190))
            draw.text((cx, cy), text, fill=lbl_col, anchor="mm")

    # ── Pass 7: edge vignette ─────────────────────────────────────────────────
    vig = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    steps = 14
    thickness = max(2, min(img_w, img_h) // (steps * 3))
    for i in range(steps):
        alpha = int(90 * ((i / steps) ** 1.4))
        pad_x = i * thickness * 2; pad_y = i * thickness * 2
        if pad_x >= img_w - pad_x or pad_y >= img_h - pad_y:
            break
        vd.rectangle([pad_x, pad_y, img_w - pad_x, img_h - pad_y],
                     outline=(0, 0, 0, alpha), width=thickness * 2)
    img = Image.alpha_composite(img, vig)

    # ── Pass 8: compass rose ───────────────────────────────────────────────────
    if tile_px >= 10 and img_w >= 80 and img_h >= 60:
        draw = ImageDraw.Draw(img)
        cr_sz = max(14, min(w, h) * tile_px // 22)
        _draw_compass_rose(draw, img_w - cr_sz - 12, img_h - cr_sz - 12, cr_sz, pal)

    # Flatten RGBA → RGB using the void colour as background
    rgb = Image.new("RGB", img.size, pal["void"])
    rgb.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    rgb.save(buf, format="PNG")
    buf.seek(0)
    return buf


def scale_for_discord(map_data: dict, max_px: int = 1024) -> io.BytesIO:
    """Render at a tile size that keeps the image under max_px in each dimension."""
    tiles = map_data.get("tiles", [[]])
    w = len(tiles[0]) if tiles else 1
    h = len(tiles)
    tile_px = max(4, min(max_px // max(w, 1), max_px // max(h, 1), TILE_SIZE))
    return render(map_data, tile_px=tile_px)
