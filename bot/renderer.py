"""
Render tile maps to PNG via Pillow.

Improvements over v1:
- Larger default tile size (22 px)
- Per-tile floor texture with grout lines and occasional stone cracks
- Wall faces: bright strip on the open-facing side of each wall = 3D depth
- Stronger quadratic ambient occlusion
- Richer water (gradient + multi-pass waves + foam)
- Trees with trunk, layered canopy, and shadow
- Grass with texture blobs, lava with glow blobs
- Removed flat grid overlay — grout lines do the work instead
- Larger compass rose
"""
from __future__ import annotations
import io
import math
import random as _rnd
from PIL import Image, ImageDraw

# ── Tile IDs ─────────────────────────────────────────────────────────────────
WALL   = 0;  FLOOR  = 1;  DOOR   = 2;  WATER  = 3;  LAVA   = 4
TREES  = 5;  ROAD   = 6;  RUBBLE = 7;  PILLAR = 8;  CHEST  = 9
STAIRS = 10; TRAP   = 11; GRASS  = 12; DIRT   = 13; SNOW   = 14

FEATURE_TILES = {DOOR, PILLAR, CHEST, STAIRS, TRAP}
TERRAIN_TILES = {WATER, LAVA, TREES, ROAD, RUBBLE, GRASS, DIRT, SNOW}

# ── Theme palettes ────────────────────────────────────────────────────────────
THEMES: dict[str, dict] = {
    "standard":     dict(void=(18,18,24),    room=(68,58,44),     corr=(50,44,34),     ink=(5,3,2),      hi=(100,80,56),    accent=(130,88,44),   label=(210,188,148), face=(38,34,28)),
    "generic":      dict(void=(18,18,24),    room=(68,58,44),     corr=(50,44,34),     ink=(5,3,2),      hi=(100,80,56),    accent=(130,88,44),   label=(210,188,148), face=(38,34,28)),
    "cave":         dict(void=(14,12,10),    room=(58,50,40),     corr=(44,38,30),     ink=(7,6,5),      hi=(90,76,58),     accent=(88,66,44),    label=(205,185,155), face=(32,28,22)),
    "crypt":        dict(void=(12,10,14),    room=(54,48,52),     corr=(40,34,40),     ink=(6,4,8),      hi=(88,74,84),     accent=(110,66,88),   label=(188,168,188), face=(28,24,32)),
    "underdark":    dict(void=(8,8,14),      room=(42,40,56),     corr=(30,28,44),     ink=(4,4,10),     hi=(66,60,90),     accent=(34,110,175),  label=(148,140,200), face=(18,18,35)),
    "bazzoxan":     dict(void=(8,8,14),      room=(42,40,56),     corr=(30,28,44),     ink=(4,4,10),     hi=(66,60,90),     accent=(34,110,175),  label=(148,140,200), face=(18,18,35)),
    "sewers":       dict(void=(10,14,10),    room=(44,54,40),     corr=(34,42,30),     ink=(5,8,5),      hi=(70,88,62),     accent=(22,100,44),   label=(155,200,145), face=(20,30,18)),
    "cerberus_lab": dict(void=(10,10,20),    room=(44,42,62),     corr=(34,32,52),     ink=(5,5,12),     hi=(76,70,100),    accent=(88,101,242),  label=(160,155,225), face=(22,22,48)),
    "ruins_aeor":   dict(void=(12,14,18),    room=(48,54,62),     corr=(38,40,50),     ink=(6,7,9),      hi=(80,86,100),    accent=(64,96,170),   label=(180,192,218), face=(26,30,42)),
    "temple":       dict(void=(14,12,10),    room=(62,54,42),     corr=(46,40,32),     ink=(7,6,5),      hi=(94,80,62),     accent=(148,108,32),  label=(215,196,160), face=(34,28,22)),
    "tundra":       dict(void=(75,85,98),    room=(198,208,220),  corr=(178,190,204),  ink=(55,65,75),   hi=(228,234,240),  accent=(118,138,158), label=(55,65,78),    face=(140,155,172)),
    "forest":       dict(void=(10,20,10),    room=(34,76,30),     corr=(28,58,24),     ink=(5,10,5),     hi=(54,100,44),    accent=(64,128,54),   label=(185,225,155), face=(18,40,14)),
    "coastal":      dict(void=(15,25,15),    room=(36,72,32),     corr=(30,60,26),     ink=(6,10,5),     hi=(58,94,48),     accent=(32,84,128),   label=(185,218,185), face=(20,38,16)),
    "badlands":     dict(void=(40,30,20),    room=(105,84,58),    corr=(88,72,48),     ink=(20,15,10),   hi=(135,110,74),   accent=(168,84,22),   label=(225,194,145), face=(62,48,32)),
    "plains":       dict(void=(20,35,18),    room=(42,82,34),     corr=(56,90,46),     ink=(10,18,8),    hi=(84,124,64),    accent=(84,116,52),   label=(205,234,165), face=(26,50,20)),
    "jungle":       dict(void=(8,16,8),      room=(30,68,26),     corr=(24,54,20),     ink=(4,8,4),      hi=(48,95,38),     accent=(54,116,44),   label=(165,214,135), face=(14,36,10)),
    "wastes":       dict(void=(40,30,20),    room=(105,84,58),    corr=(88,72,48),     ink=(20,15,10),   hi=(135,110,74),   accent=(190,64,12),   label=(225,194,145), face=(62,48,32)),
    "mountain":     dict(void=(50,50,60),    room=(115,110,120),  corr=(94,92,102),    ink=(25,25,30),   hi=(150,145,156),  accent=(84,95,125),   label=(205,205,225), face=(72,72,85)),
    "savalirwood":  dict(void=(8,16,8),      room=(30,68,26),     corr=(24,54,20),     ink=(4,8,4),      hi=(48,95,38),     accent=(64,128,54),   label=(165,218,135), face=(14,36,10)),
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
    if sub in _WILDEMOUNT_THEME_MAP:
        return THEMES[_WILDEMOUNT_THEME_MAP[sub]]
    mtype = map_data.get("map_type", "dungeon")
    if mtype in ("outdoor", "wildemount"):
        if "tundra" in sub or "eiselcross" in sub: return THEMES["tundra"]
        if "coastal" in sub or "port" in sub:       return THEMES["coastal"]
        if "savalir" in sub:                        return THEMES["savalirwood"]
        if "forest" in sub:                         return THEMES["forest"]
        if "waste" in sub or "xhorhas" in sub:      return THEMES["badlands"]
        if "mountain" in sub:                       return THEMES["mountain"]
        return THEMES["plains"]
    return THEMES["standard"]


TILE_SIZE = 22


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rng_for(px: int, py: int) -> _rnd.Random:
    return _rnd.Random(px * 1000003 + py)

def _clamp(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, v))

def _tint(col: tuple, delta: int) -> tuple:
    return tuple(_clamp(c + delta) for c in col)


# ── Floor tile with texture ───────────────────────────────────────────────────

def _draw_floor_tile(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int,
                     base_col: tuple, dungeon_style: bool = False) -> None:
    rng = _rng_for(px, py)
    v = int((rng.random() - 0.5) * 14)
    col = _tint(base_col, v)
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=col)

    if dungeon_style and ts >= 10:
        # Grout: 1px darker line on bottom and right edge
        grout = _tint(base_col, -22)
        draw.line([(px, py + ts - 1), (px + ts - 1, py + ts - 1)], fill=grout, width=1)
        draw.line([(px + ts - 1, py), (px + ts - 1, py + ts - 1)],   fill=grout, width=1)
        # Occasional stone crack
        if ts >= 14 and rng.random() < 0.11:
            crack = _tint(base_col, -30)
            x1 = px + int(rng.random() * ts * 0.6) + ts // 5
            y1 = py + int(rng.random() * ts * 0.6) + ts // 5
            x2 = px + int(rng.random() * ts * 0.6) + ts // 5
            y2 = py + int(rng.random() * ts * 0.6) + ts // 5
            draw.line([(x1, y1), (x2, y2)], fill=crack, width=1)


# ── Feature drawing helpers ───────────────────────────────────────────────────

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
    r = max(3, int(ts * 0.38))
    draw.ellipse([m - r + 2, n - r + 2, m + r + 2, n + r + 2], fill=(0, 0, 0, 90))
    draw.ellipse([m - r, n - r, m + r, n + r], fill=(72, 46, 22))
    rm = max(2, int(r * 0.72))
    draw.ellipse([m - rm, n - rm, m + rm, n + rm], fill=(155, 120, 78))
    rh = max(1, int(r * 0.38))
    draw.ellipse([m - r + 2, n - r + 2, m - r + 2 + rh * 2, n - r + 2 + rh], fill=(218, 190, 145))
    draw.ellipse([m - r, n - r, m + r, n + r], outline=(200, 162, 105), width=1)


def _draw_chest(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    m = px + ts // 2; n = py + ts // 2
    cw = max(5, int(ts * 0.60)); ch = max(4, int(ts * 0.46))
    cx = m - cw // 2; cy = n - ch // 2 - 1
    draw.rectangle([cx + 1, cy + 1, cx + cw + 1, cy + ch + 1], fill=(0, 0, 0, 90))
    draw.rectangle([cx, cy, cx + cw, cy + ch], fill=(100, 54, 20))
    draw.rectangle([cx, cy, cx + cw, cy + int(ch * 0.38)], fill=(64, 34, 8))
    latch_y = cy + int(ch * 0.42)
    draw.line([cx + 2, latch_y, cx + cw - 2, latch_y], fill=(205, 158, 64), width=2)
    draw.ellipse([m - 3, latch_y - 2, m + 3, latch_y + 4], fill=(245, 198, 68))
    draw.rectangle([cx, cy, cx + cw, cy + ch], outline=(26, 8, 4), width=1)


def _draw_stairs(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    sw = max(6, int(ts * 0.70)); sh = max(5, int(ts * 0.64))
    x0 = px + (ts - sw) // 2; y0 = py + (ts - sh) // 2
    ns = 5
    for si in range(ns):
        shrink = si * sw // (ns * 9)
        sx = x0 + shrink; sw2 = sw - shrink * 2
        sy = int(y0 + si * sh / ns); sh2 = max(1, int(sh * 0.74 / ns))
        col = (142, 110, 74) if si % 2 == 0 else (160, 128, 90)
        draw.rectangle([sx, sy, sx + sw2, sy + sh2], fill=col)
        draw.line([sx, sy + sh2, sx + sw2, sy + sh2], fill=(0, 0, 0, 60), width=1)


def _draw_trap(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    m = px + ts // 2; n = py + ts // 2
    for i, r in enumerate([int(ts * 0.44), int(ts * 0.30), int(ts * 0.16)]):
        if r < 1: continue
        draw.ellipse([m - r, n - r, m + r, n + r], outline=(170, 48, 48, 55 + i * 42), width=1)
    draw.ellipse([m - 2, n - 2, m + 2, n + 2], fill=(170, 48, 48, 200))


# ── Terrain tiles ─────────────────────────────────────────────────────────────

def _draw_water(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    # Vertical gradient — darker at top (deeper)
    for yi in range(ts):
        t = yi / max(1, ts - 1)
        r = _clamp(int(20 + t * 14))
        g = _clamp(int(48 + t * 22))
        b = _clamp(int(130 + t * 30))
        draw.line([(px, py + yi), (px + ts - 1, py + yi)], fill=(r, g, b))
    # Wave lines — multiple passes at different phases
    n_waves = max(2, ts // 5)
    for wi in range(n_waves):
        wy_base = py + ts * (wi + 0.5) / n_waves
        pts = []
        for xi in range(ts + 1):
            wy = int(wy_base + math.sin((px + xi + wi * 3.7) * 0.55) * max(1, ts // 10))
            pts.append((px + xi, _clamp(wy, py, py + ts - 1)))
        if len(pts) >= 2:
            alpha = max(20, 90 - wi * 20)
            draw.line(pts, fill=(145, 215, 255, alpha), width=1)
    # Foam specks
    rng = _rng_for(px, py)
    for _ in range(2):
        fx = px + int(rng.random() * ts)
        fy = py + int(rng.random() * ts)
        draw.ellipse([fx - 1, fy - 1, fx + 1, fy + 1], fill=(205, 235, 255, 70))


def _draw_lava(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(52, 8, 2))
    rng = _rng_for(px, py)
    # Glow blobs
    for _ in range(3):
        bx = px + int(rng.random() * ts)
        by = py + int(rng.random() * ts)
        br = max(2, int(rng.random() * ts // 3))
        heat = int(150 + rng.random() * 105)
        draw.ellipse([bx - br, by - br, bx + br, by + br],
                     fill=(_clamp(heat), _clamp(heat // 3), 0, 160))
    # Bright cracks
    for _ in range(2):
        x1 = px + int(rng.random() * ts); y1 = py + int(rng.random() * ts)
        x2 = px + int(rng.random() * ts); y2 = py + int(rng.random() * ts)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 100, 0, 200), width=1)


def _draw_trees(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(14, 34, 10))
    rng = _rng_for(px, py)
    n_trees = 1 if rng.random() > 0.45 else 2
    for _ in range(n_trees):
        tcx = px + int(ts * (0.22 + rng.random() * 0.56))
        tcy = py + int(ts * (0.22 + rng.random() * 0.56))
        # Trunk
        if ts >= 14:
            trunk_w = max(1, ts // 9)
            trunk_h = max(2, ts // 4)
            draw.rectangle([tcx - trunk_w, tcy, tcx + trunk_w, tcy + trunk_h],
                           fill=(52, 30, 8))
        # Canopy shadow
        cr = max(3, ts // 3 + 1)
        draw.ellipse([tcx - cr + 2, tcy - cr + 1, tcx + cr + 2, tcy + cr + 1],
                     fill=(0, 0, 0, 65))
        # Main canopy
        gb = _clamp(54 + int(rng.random() * 38))
        draw.ellipse([tcx - cr, tcy - cr, tcx + cr, tcy + cr], fill=(16, gb, 12))
        # Highlight (upper-left, smaller)
        hr = max(2, cr - cr // 3)
        draw.ellipse([tcx - hr - 1, tcy - hr - 1, tcx + hr // 2, tcy + hr // 2],
                     fill=(24, _clamp(gb + 30), 18))


def _draw_rubble(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(56, 44, 28))
    rng = _rng_for(px, py)
    for ri in range(5):
        rfx = px + int(rng.random() * (ts - 2))
        rfy = py + int(rng.random() * (ts - 2))
        rfw = max(1, 2 + int(rng.random() * 5))
        rfh = max(1, 1 + int(rng.random() * 3))
        col = (98, 80, 56) if ri % 2 == 0 else (44, 34, 22)
        draw.rectangle([rfx, rfy, rfx + rfw, rfy + rfh], fill=col)


def _draw_grass(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py)
    gv = rng.random()
    base = (int(26 + gv * 16), int(70 + gv * 36), int(16 + gv * 12))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    # Texture blobs
    if ts >= 10:
        for _ in range(3):
            bx = px + int(rng.random() * ts)
            by = py + int(rng.random() * ts)
            br = max(1, ts // 6)
            lighter = int(rng.random() * 20) - 5
            blob = (_clamp(base[0] + lighter), _clamp(base[1] + lighter + 8), _clamp(base[2]))
            draw.ellipse([bx - br, by - br, bx + br, by + br], fill=blob)


def _draw_dirt(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py)
    dv = rng.random()
    base = (int(128 + dv * 24), int(98 + dv * 20), int(58 + dv * 16))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    if ts >= 10:
        for _ in range(2):
            bx = px + int(rng.random() * ts)
            by = py + int(rng.random() * ts)
            br = max(1, ts // 7)
            v2 = int(rng.random() * 16) - 8
            draw.ellipse([bx - br, by - br, bx + br, by + br],
                         fill=(_clamp(base[0] + v2), _clamp(base[1] + v2), _clamp(base[2] + v2)))


def _draw_snow(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py)
    sv = rng.random()
    base = (min(255, int(205 + sv * 45)), min(255, int(212 + sv * 38)), min(255, int(222 + sv * 30)))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    if ts >= 12:
        for _ in range(2):
            sx2 = px + int(rng.random() * ts)
            sy2 = py + int(rng.random() * ts)
            draw.point((sx2, sy2), fill=(255, 255, 255, 140))


def _draw_compass_rose(draw: ImageDraw.ImageDraw, cx: int, cy: int, sz: int, pal: dict) -> None:
    acc = pal.get("accent", (180, 140, 60))
    dim = tuple(max(0, c - 55) for c in acc)
    lbl = pal.get("label", (200, 180, 140))
    h4 = sz // 4
    draw.polygon([(cx, cy - sz), (cx - h4, cy), (cx, cy - sz // 3)], fill=acc)
    draw.polygon([(cx, cy - sz), (cx + h4, cy), (cx, cy - sz // 3)], fill=dim)
    draw.polygon([(cx, cy + sz), (cx - h4, cy), (cx, cy + sz // 3)], fill=dim)
    draw.polygon([(cx, cy + sz), (cx + h4, cy), (cx, cy + sz // 3)],
                 fill=tuple(max(0, c - 30) for c in dim))
    draw.polygon([(cx + sz, cy), (cx, cy - h4), (cx + sz // 3, cy)], fill=dim)
    draw.polygon([(cx + sz, cy), (cx, cy + h4), (cx + sz // 3, cy)],
                 fill=tuple(max(0, c - 20) for c in dim))
    draw.polygon([(cx - sz, cy), (cx, cy - h4), (cx - sz // 3, cy)], fill=dim)
    draw.polygon([(cx - sz, cy), (cx, cy + h4), (cx - sz // 3, cy)],
                 fill=tuple(max(0, c - 20) for c in dim))
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=lbl)
    draw.text((cx, cy - sz - 5), "N", fill=lbl, anchor="mb")


# ── Main render function ──────────────────────────────────────────────────────

def _in_room(tx: int, ty: int, rooms: list[dict]) -> bool:
    return any(r["x"] <= tx < r["x"] + r["w"] and r["y"] <= ty < r["y"] + r["h"] for r in rooms)


def render(map_data: dict, tile_px: int = TILE_SIZE) -> io.BytesIO:
    tiles  = map_data["tiles"]
    h = len(tiles); w = len(tiles[0]) if h else 0
    rooms  = map_data.get("rooms", [])
    img_w, img_h = w * tile_px, h * tile_px
    pal    = _theme_for(map_data)
    mtype  = map_data.get("map_type", "dungeon")
    dungeon_style = mtype in ("dungeon", "interior", "wildemount")

    img  = Image.new("RGBA", (img_w, img_h), (*pal["void"], 255))
    draw = ImageDraw.Draw(img)

    def is_open(nx: int, ny: int) -> bool:
        return 0 <= ny < h and 0 <= nx < w and tiles[ny][nx] != WALL

    # ── Pass 1: base tiles ────────────────────────────────────────────────────
    for ry, row in enumerate(tiles):
        for rx, t in enumerate(row):
            if t == WALL:
                continue
            px, py = rx * tile_px, ry * tile_px
            in_room = _in_room(rx, ry, rooms) if rooms else True

            if t in (FLOOR, *FEATURE_TILES):
                base = pal["room"] if in_room else pal["corr"]
                _draw_floor_tile(draw, px, py, tile_px, base, dungeon_style)
            elif t == WATER:  _draw_water(draw, px, py, tile_px)
            elif t == LAVA:   _draw_lava(draw, px, py, tile_px)
            elif t == TREES:  _draw_trees(draw, px, py, tile_px)
            elif t == ROAD:
                rng = _rng_for(px, py)
                v = int((rng.random() - 0.5) * 10)
                draw.rectangle([px, py, px + tile_px - 1, py + tile_px - 1],
                                fill=(_clamp(136 + v), _clamp(115 + v), _clamp(86 + v)))
            elif t == RUBBLE: _draw_rubble(draw, px, py, tile_px)
            elif t == GRASS:  _draw_grass(draw, px, py, tile_px)
            elif t == DIRT:   _draw_dirt(draw, px, py, tile_px)
            elif t == SNOW:   _draw_snow(draw, px, py, tile_px)

    # ── Pass 2: wall faces — bright strip on open-facing side ────────────────
    if tile_px >= 8:
        face_col  = pal.get("face", _tint(pal["void"], 30))
        face_hi   = _tint(face_col, 18)
        face_h    = max(2, tile_px // 5)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                # South face — wall with open space below it
                if is_open(rx, ry + 1):
                    draw.rectangle([px, py + tile_px - face_h,
                                    px + tile_px - 1, py + tile_px - 1], fill=face_col)
                    draw.line([(px, py + tile_px - face_h),
                               (px + tile_px - 1, py + tile_px - face_h)],
                              fill=face_hi, width=1)
                # East face — wall with open space to its right
                if is_open(rx + 1, ry):
                    draw.rectangle([px + tile_px - face_h, py,
                                    px + tile_px - 1, py + tile_px - 1], fill=face_col)

    # ── Pass 3: ambient occlusion — quadratic gradient into walls ────────────
    if tile_px >= 8:
        ao      = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        ao_draw = ImageDraw.Draw(ao)
        ao_depth = max(3, int(tile_px * 0.55))
        dirs = [
            (0, -1, lambda px, py, si: (px, py, px + tile_px - 1, py + si)),
            (0,  1, lambda px, py, si: (px, py + tile_px - si - 1, px + tile_px - 1, py + tile_px - 1)),
            (-1, 0, lambda px, py, si: (px, py, px + si, py + tile_px - 1)),
            (1,  0, lambda px, py, si: (px + tile_px - si - 1, py, px + tile_px - 1, py + tile_px - 1)),
        ]
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                for dx, dy, rect_fn in dirs:
                    nx_, ny_ = rx + dx, ry + dy
                    if 0 <= ny_ < h and 0 <= nx_ < w and tiles[ny_][nx_] == WALL:
                        for si in range(ao_depth):
                            frac = si / ao_depth
                            alpha = int(155 * (1 - frac) ** 1.9)
                            r = rect_fn(px, py, si)
                            ao_draw.rectangle(list(r), fill=(0, 0, 0, alpha))
        img  = Image.alpha_composite(img, ao)
        draw = ImageDraw.Draw(img)

    # ── Pass 4: feature overlays ──────────────────────────────────────────────
    if tile_px >= 8:
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t not in FEATURE_TILES:
                    continue
                px, py = rx * tile_px, ry * tile_px
                if   t == DOOR:   _draw_door(draw, px, py, tile_px)
                elif t == PILLAR: _draw_pillar(draw, px, py, tile_px)
                elif t == CHEST:  _draw_chest(draw, px, py, tile_px)
                elif t == STAIRS: _draw_stairs(draw, px, py, tile_px)
                elif t == TRAP:   _draw_trap(draw, px, py, tile_px)

    # ── Pass 5: ink wall outlines ─────────────────────────────────────────────
    if tile_px >= 6:
        ink = pal["ink"]; hi = pal["hi"]
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

    # ── Pass 6: room labels ───────────────────────────────────────────────────
    if tile_px >= 12:
        lbl_col = pal.get("label", (200, 180, 140))
        for room in rooms:
            rw_r = room.get("w", 0); rh_r = room.get("h", 0)
            rt = room.get("type", room.get("room_type", ""))
            if rw_r < 4 or rh_r < 4 or not rt:
                continue
            cx2 = (room["x"] + rw_r // 2) * tile_px
            cy2 = (room["y"] + rh_r // 2) * tile_px
            text = rt.replace("_", " ")[:14]
            fs = max(7, int(tile_px * 0.40))
            tw = len(text) * (fs // 2 + 1) + 8; th = fs + 8
            draw.rectangle([cx2 - tw // 2, cy2 - th // 2, cx2 + tw // 2, cy2 + th // 2],
                           fill=(8, 6, 4, 200))
            draw.text((cx2, cy2), text, fill=lbl_col, anchor="mm")

    # ── Pass 7: edge vignette ─────────────────────────────────────────────────
    vig = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    steps     = 16
    thickness = max(2, min(img_w, img_h) // (steps * 3))
    for i in range(steps):
        alpha = int(100 * ((i / steps) ** 1.5))
        pad = i * thickness * 2
        if pad >= img_w - pad or pad >= img_h - pad:
            break
        vd.rectangle([pad, pad, img_w - pad, img_h - pad],
                     outline=(0, 0, 0, alpha), width=thickness * 2)
    img = Image.alpha_composite(img, vig)

    # ── Pass 8: compass rose ──────────────────────────────────────────────────
    if tile_px >= 8 and img_w >= 80 and img_h >= 60:
        draw = ImageDraw.Draw(img)
        cr_sz = max(16, min(w, h) * tile_px // 18)
        _draw_compass_rose(draw, img_w - cr_sz - 14, img_h - cr_sz - 14, cr_sz, pal)

    # Flatten RGBA → RGB
    rgb = Image.new("RGB", img.size, pal["void"])
    rgb.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    rgb.save(buf, format="PNG")
    buf.seek(0)
    return buf


def scale_for_discord(map_data: dict, max_px: int = 1280) -> io.BytesIO:
    """Render at a tile size that keeps the image under max_px in each dimension."""
    tiles  = map_data.get("tiles", [[]])
    w = len(tiles[0]) if tiles else 1
    h = len(tiles)
    tile_px = max(6, min(max_px // max(w, 1), max_px // max(h, 1), TILE_SIZE))
    return render(map_data, tile_px=tile_px)
