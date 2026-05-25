"""
Render tile maps to PNG via Pillow — cinematic dungeon aesthetic.

v4: 32 px tiles · Gaussian-blurred torch glow & AO · large stone floor slab
joints · 3-D wall blocks (per-brick face shading) · deeper torch halos ·
decorative map border · post-process contrast + saturation.
"""
from __future__ import annotations
import io
import math
import random as _rnd
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# ── Tile IDs ──────────────────────────────────────────────────────────────────
WALL   = 0;  FLOOR  = 1;  DOOR   = 2;  WATER  = 3;  LAVA   = 4
TREES  = 5;  ROAD   = 6;  RUBBLE = 7;  PILLAR = 8;  CHEST  = 9
STAIRS = 10; TRAP   = 11; GRASS  = 12; DIRT   = 13; SNOW   = 14

FEATURE_TILES = {DOOR, PILLAR, CHEST, STAIRS, TRAP}
TERRAIN_TILES = {WATER, LAVA, TREES, ROAD, RUBBLE, GRASS, DIRT, SNOW}

# ── Theme palettes ─────────────────────────────────────────────────────────────
THEMES: dict[str, dict] = {
    "standard":     dict(void=(10,9,15),    room=(92,74,52),    corr=(56,44,30),
                         ink=(4,3,6),       hi=(138,110,76),    accent=(218,158,52),
                         label=(250,224,172), face=(48,40,30),  warm=(255,168,72)),
    "generic":      dict(void=(10,9,15),    room=(92,74,52),    corr=(56,44,30),
                         ink=(4,3,6),       hi=(138,110,76),    accent=(218,158,52),
                         label=(250,224,172), face=(48,40,30),  warm=(255,168,72)),
    "cave":         dict(void=(10,9,8),     room=(72,58,44),    corr=(52,42,32),
                         ink=(5,4,4),       hi=(108,88,64),     accent=(138,92,48),
                         label=(218,192,158), face=(36,30,22),  warm=(255,158,62)),
    "crypt":        dict(void=(10,8,18),    room=(64,52,68),    corr=(46,36,52),
                         ink=(5,4,9),       hi=(98,82,104),     accent=(168,72,118),
                         label=(210,182,212), face=(30,24,42),  warm=(210,138,228)),
    "underdark":    dict(void=(6,6,18),     room=(46,44,72),    corr=(30,28,54),
                         ink=(3,3,10),      hi=(74,66,112),     accent=(42,138,228),
                         label=(162,152,228), face=(20,18,46),  warm=(88,148,255)),
    "bazzoxan":     dict(void=(6,6,18),     room=(46,44,72),    corr=(30,28,54),
                         ink=(3,3,10),      hi=(74,66,112),     accent=(42,138,228),
                         label=(162,152,228), face=(20,18,46),  warm=(88,148,255)),
    "sewers":       dict(void=(8,14,8),     room=(48,66,44),    corr=(34,50,30),
                         ink=(4,7,4),       hi=(76,102,66),     accent=(22,128,56),
                         label=(162,218,152), face=(22,36,18),  warm=(168,228,80)),
    "cerberus_lab": dict(void=(8,8,24),     room=(50,48,78),    corr=(34,32,58),
                         ink=(4,4,13),      hi=(84,78,116),     accent=(108,128,255),
                         label=(180,172,248), face=(24,22,54),  warm=(108,168,255)),
    "ruins_aeor":   dict(void=(10,12,20),   room=(56,62,76),    corr=(40,46,60),
                         ink=(5,6,10),      hi=(92,98,118),     accent=(76,114,198),
                         label=(190,206,236), face=(28,32,50),  warm=(128,168,228)),
    "temple":       dict(void=(14,11,8),    room=(90,74,54),    corr=(62,52,38),
                         ink=(7,5,4),       hi=(128,106,76),    accent=(208,154,42),
                         label=(244,216,172), face=(46,38,24),  warm=(255,206,80)),
    "tundra":       dict(void=(68,80,96),   room=(212,222,238), corr=(188,200,216),
                         ink=(48,60,72),    hi=(242,248,255),   accent=(132,152,178),
                         label=(48,60,78),  face=(152,166,184), warm=(208,228,255)),
    "forest":       dict(void=(8,20,8),     room=(40,86,34),    corr=(28,64,22),
                         ink=(4,10,4),      hi=(60,116,48),     accent=(76,154,58),
                         label=(192,238,162), face=(18,46,14),  warm=(188,228,80)),
    "coastal":      dict(void=(12,24,14),   room=(42,82,38),    corr=(30,64,28),
                         ink=(5,10,5),      hi=(64,108,54),     accent=(38,100,154),
                         label=(192,228,192), face=(20,44,18),  warm=(84,208,228)),
    "badlands":     dict(void=(38,28,16),   room=(122,96,64),   corr=(96,78,50),
                         ink=(19,13,8),     hi=(152,124,82),    accent=(198,92,24),
                         label=(240,206,152), face=(68,52,32),  warm=(255,164,60)),
    "plains":       dict(void=(16,32,14),   room=(50,96,40),    corr=(58,100,48),
                         ink=(8,16,6),      hi=(96,142,72),     accent=(96,132,60),
                         label=(218,248,178), face=(28,58,20),  warm=(208,244,82)),
    "jungle":       dict(void=(6,16,6),     room=(34,76,28),    corr=(24,60,20),
                         ink=(3,8,3),       hi=(54,110,42),     accent=(62,132,50),
                         label=(172,224,142), face=(14,40,10),  warm=(188,244,62)),
    "wastes":       dict(void=(38,28,16),   room=(122,96,64),   corr=(96,78,50),
                         ink=(19,13,8),     hi=(152,124,82),    accent=(218,70,12),
                         label=(240,206,152), face=(68,52,32),  warm=(255,144,40)),
    "mountain":     dict(void=(46,46,58),   room=(126,120,132), corr=(100,96,108),
                         ink=(23,23,30),    hi=(162,156,168),   accent=(94,106,138),
                         label=(216,216,238), face=(76,76,90),  warm=(224,224,255)),
    "savalirwood":  dict(void=(6,16,6),     room=(34,76,28),    corr=(24,60,20),
                         ink=(3,8,3),       hi=(54,110,42),     accent=(76,148,60),
                         label=(172,228,142), face=(14,40,10),  warm=(188,244,82)),
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


TILE_SIZE = 32


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rng_for(px: int, py: int) -> _rnd.Random:
    return _rnd.Random(px * 1000003 + py)

def _clamp(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, v))

def _tint(col: tuple, delta: int) -> tuple:
    return tuple(_clamp(c + delta) for c in col)

def _warm_bias(warm: tuple) -> tuple[int, int, int]:
    return (
        (warm[0] - 128) // 11,
        (warm[1] - 128) // 14,
        (warm[2] - 128) // 11,
    )


# ── Wall stone texture (v4: per-brick 3-D shading) ────────────────────────────

def _draw_wall_stone(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int,
                     pal: dict) -> None:
    rng   = _rng_for(px, py)
    void  = pal["void"]
    v     = int(rng.random() * 14 + 4)
    stone = _tint(void, v)
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=stone)
    if ts < 10:
        return

    mortar = _tint(void, -16)
    ty_idx = py // ts
    mid_y  = py + ts // 2

    # Horizontal mortar seam — 2 px wide for definition
    draw.rectangle([px, mid_y - 1, px + ts - 1, mid_y + 1], fill=mortar)

    # Staggered vertical mortars (brick bond)
    off = 0 if ty_idx % 2 == 0 else ts // 2
    for frac in (1/3, 2/3):
        vx = px + int((frac * ts + off) % ts)
        if px < vx < px + ts - 1:
            draw.rectangle([vx - 1, py, vx + 1, mid_y - 2], fill=mortar)
        vx2 = px + int((frac * ts + ts // 2 - off) % ts)
        if px < vx2 < px + ts - 1:
            draw.rectangle([vx2 - 1, mid_y + 2, vx2 + 1, py + ts - 1], fill=mortar)

    # Per-brick 3-D face shading (highlight top-left / shadow bottom-right)
    if ts >= 14:
        hi = _tint(stone, 32)
        sh = _tint(stone, -30)
        for by, ey in [(py, mid_y - 2), (mid_y + 2, py + ts - 1)]:
            draw.line([(px + 1, by + 1), (px + ts - 2, by + 1)], fill=hi, width=1)
            draw.line([(px + 1, by + 1), (px + 1,      ey - 1)], fill=hi, width=1)
            draw.line([(px + ts - 2, by + 2), (px + ts - 2, ey - 1)], fill=sh, width=1)
            draw.line([(px + 2,      ey - 1), (px + ts - 2, ey - 1)], fill=sh, width=1)

    # Occasional surface weathering
    if rng.random() < 0.20:
        pw  = max(2, int(rng.random() * ts // 3))
        ph  = max(1, int(rng.random() * ts // 5))
        pfx = px + 1 + int(rng.random() * max(1, ts - pw - 2))
        pfy = py + 1 + int(rng.random() * max(1, ts - ph - 2))
        if pfy > mid_y + 2 or pfy + ph < mid_y - 2:
            draw.rectangle([pfx, pfy, pfx + pw, pfy + ph],
                           fill=_tint(stone, int(rng.random() * 20) - 10))


# ── Floor tile ────────────────────────────────────────────────────────────────

def _draw_floor_tile(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int,
                     base_col: tuple, dungeon_style: bool = False,
                     warmth: float = 0.0,
                     wbias: tuple[int,int,int] = (6, 1, -3)) -> None:
    rng = _rng_for(px, py)
    v   = int((rng.random() - 0.5) * 16)
    col = _tint(base_col, v)

    if warmth > 0.02:
        col = (
            _clamp(col[0] + int(warmth * wbias[0])),
            _clamp(col[1] + int(warmth * wbias[1])),
            _clamp(col[2] + int(warmth * wbias[2])),
        )

    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=col)

    if dungeon_style and ts >= 10:
        grout = _tint(col, -40)
        hi    = _tint(col, 30)
        # Grout lines — right and bottom (2 px for depth)
        draw.line([(px,      py + ts - 1), (px + ts - 1, py + ts - 1)], fill=grout, width=2)
        draw.line([(px + ts - 1, py),      (px + ts - 1, py + ts - 1)], fill=grout, width=2)
        # Inner bevel (top and left) — 2 px for a more chiseled look
        if ts >= 14:
            draw.line([(px + 2, py + 2), (px + ts - 4, py + 2)], fill=hi, width=1)
            draw.line([(px + 2, py + 2), (px + 2,      py + ts - 4)], fill=hi, width=1)
        # Occasional crack
        if ts >= 16 and rng.random() < 0.07:
            crack = _tint(col, -48)
            x1 = px + ts // 4 + int(rng.random() * ts // 2)
            y1 = py + ts // 4 + int(rng.random() * ts // 2)
            draw.line([(x1, y1),
                       (x1 + int((rng.random() - .5) * ts // 2),
                        y1 + int((rng.random() - .5) * ts // 2))],
                      fill=crack, width=1)


# ── Stone-slab grid overlay ───────────────────────────────────────────────────

def _draw_slab_lines(draw: ImageDraw.ImageDraw, rooms: list[dict],
                     tile_px: int, pal: dict) -> None:
    """Draw large-format stone slab joints across room floors."""
    for room in rooms:
        rng = _rng_for(room["x"] * 7, room["y"] * 13)
        slab_w = rng.randint(2, 3)
        slab_h = rng.randint(1, 2)
        mortar = _tint(pal["room"], -52)
        hi     = _tint(pal["room"], 22)
        rx, ry, rw, rh = room["x"], room["y"], room["w"], room["h"]
        # Vertical slab breaks
        x = rx
        while x < rx + rw:
            x += slab_w
            if x >= rx + rw:
                break
            lx = x * tile_px
            y0 = ry * tile_px + 3
            y1 = (ry + rh) * tile_px - 4
            draw.line([(lx, y0), (lx, y1)],     fill=mortar, width=2)
            draw.line([(lx + 1, y0), (lx + 1, y1)], fill=hi, width=1)
        # Horizontal slab breaks
        y = ry
        while y < ry + rh:
            y += slab_h
            if y >= ry + rh:
                break
            ly = y * tile_px
            x0 = rx * tile_px + 3
            x1 = (rx + rw) * tile_px - 4
            draw.line([(x0, ly), (x1, ly)],     fill=mortar, width=2)
            draw.line([(x0, ly + 1), (x1, ly + 1)], fill=hi, width=1)


# ── Feature sprites ───────────────────────────────────────────────────────────

def _draw_door(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    dw = max(5, int(ts * 0.58)); dh = max(6, int(ts * 0.82))
    dx = px + (ts - dw) // 2;   dy = py + (ts - dh) // 2
    # Shadow
    draw.rectangle([dx + 3, dy + 3, dx + dw + 3, dy + dh + 3], fill=(0, 0, 0, 110))
    # Body
    draw.rectangle([dx, dy, dx + dw, dy + dh], fill=(108, 56, 18))
    # Top arch darkness
    top_h = max(2, int(dh * 0.36))
    draw.rectangle([dx, dy, dx + dw, dy + top_h], fill=(70, 36, 8))
    # Panel
    pad = max(2, ts // 9)
    draw.rectangle([dx + pad, dy + top_h + 2, dx + dw - pad, dy + dh - pad],
                   fill=(82, 42, 10))
    # Band
    by = dy + int(dh * 0.55)
    draw.rectangle([dx, by, dx + dw, by + 2], fill=(40, 36, 28))
    # Highlight edges
    draw.line([(dx + 1, dy + 1), (dx + dw - 1, dy + 1)], fill=(148, 84, 38), width=1)
    draw.line([(dx + 1, dy + 1), (dx + 1, dy + dh - 1)], fill=(148, 84, 38), width=1)
    # Knob
    kx = dx + int(dw * 0.72); ky = dy + dh // 2
    draw.ellipse([kx - 3, ky - 3, kx + 3, ky + 3], fill=(228, 175, 56))
    draw.ellipse([kx - 2, ky - 2, kx + 2, ky + 2], fill=(252, 212, 88))
    # Outline
    draw.rectangle([dx, dy, dx + dw, dy + dh], outline=(22, 8, 4), width=1)


def _draw_pillar(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts // 2; my = py + ts // 2
    r  = max(4, int(ts * 0.40))
    draw.ellipse([mx - r + 4, my - r + 4, mx + r + 4, my + r + 4], fill=(0, 0, 0, 120))
    draw.ellipse([mx - r, my - r, mx + r, my + r], fill=(72, 48, 20))
    rm = max(3, int(r * 0.76))
    draw.ellipse([mx - rm, my - rm, mx + rm, my + rm], fill=(168, 134, 86))
    if ts >= 18:
        for i in range(8):
            ang = math.pi * 2 * i / 8
            lx = int(mx + rm * 0.86 * math.cos(ang))
            ly = int(my + rm * 0.86 * math.sin(ang))
            draw.line([(mx, my), (lx, ly)], fill=_tint((168, 134, 86), -26), width=1)
    rh = max(2, int(r * 0.44))
    draw.ellipse([mx - r + 2, my - r + 2, mx - r + 2 + rh * 2, my - r + 2 + rh],
                 fill=(238, 210, 162))
    draw.ellipse([mx - r, my - r, mx + r, my + r], outline=(220, 180, 118), width=1)


def _draw_chest(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts // 2; my = py + ts // 2
    cw = max(6, int(ts * 0.66)); ch = max(5, int(ts * 0.52))
    cx = mx - cw // 2;           cy2 = my - ch // 2 - 1
    draw.rectangle([cx + 3, cy2 + 3, cx + cw + 3, cy2 + ch + 3], fill=(0, 0, 0, 120))
    draw.rectangle([cx, cy2, cx + cw, cy2 + ch], fill=(116, 60, 18))
    lid_h = max(2, int(ch * 0.38))
    draw.rectangle([cx, cy2, cx + cw, cy2 + lid_h], fill=(72, 38, 8))
    draw.line([(cx + 1, cy2 + 1), (cx + cw - 1, cy2 + 1)], fill=(148, 82, 36), width=1)
    draw.rectangle([cx, cy2 + lid_h + 1, cx + cw, cy2 + lid_h + 2], fill=(44, 40, 32))
    for cox, coy in [(cx, cy2), (cx + cw - 3, cy2),
                     (cx, cy2 + ch - 3), (cx + cw - 3, cy2 + ch - 3)]:
        draw.rectangle([cox, coy, cox + 3, coy + 3], fill=(205, 162, 50))
    latch_y = cy2 + int(ch * 0.45)
    draw.line([cx + 2, latch_y, cx + cw - 2, latch_y], fill=(218, 172, 66), width=2)
    draw.ellipse([mx - 3, latch_y - 3, mx + 3, latch_y + 3], fill=(255, 218, 72))
    draw.rectangle([cx, cy2, cx + cw, cy2 + ch], outline=(24, 8, 4), width=1)


def _draw_stairs(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    sw = max(8, int(ts * 0.74)); sh = max(6, int(ts * 0.70))
    x0 = px + (ts - sw) // 2;   y0 = py + (ts - sh) // 2
    ns = 7
    for si in range(ns):
        shrink = si * sw // (ns * 6)
        sx = x0 + shrink; sw2 = max(2, sw - shrink * 2)
        sy = y0 + int(si * sh / ns); sh2 = max(1, int(sh / ns))
        col = (152, 120, 78) if si % 2 == 0 else (172, 140, 96)
        draw.rectangle([sx, sy, sx + sw2, sy + sh2], fill=col)
        draw.line([(sx, sy), (sx + sw2, sy)], fill=_tint(col, 28), width=1)
        draw.line([(sx, sy + sh2), (sx + sw2, sy + sh2)], fill=(0, 0, 0, 80), width=1)
    mx2 = x0 + sw // 2; ay = y0 + sh + 4
    if ay + 5 < py + ts:
        draw.polygon([(mx2, ay + 5), (mx2 - 4, ay), (mx2 + 4, ay)],
                     fill=(210, 175, 106))


def _draw_trap(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts // 2; my = py + ts // 2
    for i, r in enumerate([int(ts * 0.46), int(ts * 0.32), int(ts * 0.18)]):
        if r < 1: continue
        draw.ellipse([mx - r, my - r, mx + r, my + r],
                     outline=(200, 52, 52, 55 + i * 50), width=1)
    pp = max(3, int(ts * 0.26))
    draw.ellipse([mx - pp, my - pp, mx + pp, my + pp], fill=(98, 34, 34, 185))
    draw.ellipse([mx - pp, my - pp, mx + pp, my + pp], outline=(200, 52, 52), width=1)
    draw.ellipse([mx - 2, my - 2, mx + 2, my + 2], fill=(215, 68, 68))


# ── Terrain tiles ─────────────────────────────────────────────────────────────

def _draw_water(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    # Depth gradient (dark → lighter)
    for yi in range(ts):
        t = yi / max(1, ts - 1)
        draw.line([(px, py + yi), (px + ts - 1, py + yi)],
                  fill=(_clamp(int(16 + t * 14)),
                        _clamp(int(40 + t * 28)),
                        _clamp(int(142 + t * 36))))
    n_waves = max(2, ts // 5)
    for wi in range(n_waves):
        wy_base = py + ts * (wi + 0.5) / n_waves
        pts = []
        for xi in range(ts + 1):
            wy = int(wy_base + math.sin((px + xi) * 0.55 + wi * 3.7) * max(1, ts // 10))
            pts.append((px + xi, _clamp(wy, py, py + ts - 1)))
        if len(pts) >= 2:
            draw.line(pts, fill=(152, 224, 255, max(28, 110 - wi * 24)), width=1)
    rng = _rng_for(px, py)
    for _ in range(4):
        fx = px + int(rng.random() * ts)
        fy = py + int(rng.random() * ts)
        draw.ellipse([fx - 1, fy - 1, fx + 1, fy + 1], fill=(218, 244, 255, 90))


def _draw_lava(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(52, 8, 2))
    rng = _rng_for(px, py)
    for _ in range(5):
        bx = px + int(rng.random() * ts); by = py + int(rng.random() * ts)
        br = max(2, int(rng.random() * ts // 3 + 1))
        h_ = int(138 + rng.random() * 117)
        draw.ellipse([bx - br, by - br, bx + br, by + br],
                     fill=(_clamp(h_), _clamp(h_ // 3 + 22), 0, 180))
    for _ in range(3):
        x1 = px + int(rng.random() * ts); y1 = py + int(rng.random() * ts)
        x2 = px + int(rng.random() * ts); y2 = py + int(rng.random() * ts)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 118, 14, 220), width=1)


def _draw_trees(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(12, 32, 8))
    rng = _rng_for(px, py)
    n = 1 if rng.random() > 0.38 else 2
    for _ in range(n):
        tcx = px + int(ts * (0.20 + rng.random() * 0.60))
        tcy = py + int(ts * (0.20 + rng.random() * 0.60))
        if ts >= 14:
            tw = max(1, ts // 10)
            draw.rectangle([tcx - tw, tcy, tcx + tw, tcy + ts // 4], fill=(60, 34, 8))
        cr = max(4, ts // 3 + 1)
        draw.ellipse([tcx - cr + 4, tcy - cr // 2 + 4, tcx + cr + 4, tcy + cr // 2 + 4],
                     fill=(0, 0, 0, 80))
        gb = _clamp(54 + int(rng.random() * 42))
        draw.ellipse([tcx - cr, tcy - cr, tcx + cr, tcy + cr], fill=(14, gb, 10))
        hr = max(3, cr - cr // 3)
        draw.ellipse([tcx - hr - 1, tcy - hr - 2, tcx + hr // 2, tcy + hr // 2],
                     fill=(22, _clamp(gb + 34), 14))


def _draw_rubble(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=(54, 44, 26))
    rng = _rng_for(px, py)
    for ri in range(7):
        rfx = px + int(rng.random() * (ts - 3))
        rfy = py + int(rng.random() * (ts - 3))
        rfw = max(1, 2 + int(rng.random() * ts // 4))
        rfh = max(1, 1 + int(rng.random() * ts // 5))
        draw.rectangle([rfx, rfy, rfx + rfw, rfy + rfh],
                       fill=(106, 88, 60) if ri % 2 == 0 else (44, 34, 20))
        draw.line([(rfx, rfy + rfh), (rfx + rfw, rfy + rfh)],
                  fill=(0, 0, 0, 60), width=1)


def _draw_grass(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); gv = rng.random()
    base = (int(24 + gv * 18), int(74 + gv * 40), int(14 + gv * 14))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    if ts >= 10:
        for _ in range(5):
            bx = px + int(rng.random() * ts)
            by = py + int(rng.random() * ts)
            br = max(1, ts // 7)
            lv = int(rng.random() * 24) - 9
            draw.ellipse([bx - br, by - br, bx + br, by + br],
                         fill=(_clamp(base[0] + lv), _clamp(base[1] + lv + 10),
                               _clamp(base[2])))


def _draw_dirt(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); dv = rng.random()
    base = (int(134 + dv * 26), int(102 + dv * 22), int(56 + dv * 18))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    if ts >= 10:
        for _ in range(3):
            bx = px + int(rng.random() * ts)
            by = py + int(rng.random() * ts)
            br = max(1, ts // 8)
            v2 = int(rng.random() * 18) - 9
            draw.ellipse([bx - br, by - br, bx + br, by + br],
                         fill=(_clamp(base[0] + v2), _clamp(base[1] + v2),
                               _clamp(base[2] + v2)))


def _draw_snow(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); sv = rng.random()
    base = (min(255, int(208 + sv * 46)), min(255, int(216 + sv * 38)),
            min(255, int(228 + sv * 28)))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=base)
    if ts >= 12:
        for _ in range(4):
            draw.point((px + int(rng.random() * ts), py + int(rng.random() * ts)),
                       fill=(255, 255, 255, 170))


def _draw_compass_rose(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                       sz: int, pal: dict) -> None:
    acc = pal.get("accent", (188, 148, 60))
    dim = tuple(max(0, c - 60) for c in acc)
    lbl = pal.get("label", (208, 188, 148))
    h4  = sz // 4
    draw.polygon([(cx, cy - sz), (cx - h4, cy), (cx, cy - sz // 3)], fill=acc)
    draw.polygon([(cx, cy - sz), (cx + h4, cy), (cx, cy - sz // 3)],
                 fill=_tint(acc, -22))
    draw.polygon([(cx, cy + sz), (cx - h4, cy), (cx, cy + sz // 3)], fill=dim)
    draw.polygon([(cx, cy + sz), (cx + h4, cy), (cx, cy + sz // 3)],
                 fill=tuple(max(0, c - 32) for c in dim))
    draw.polygon([(cx + sz, cy), (cx, cy - h4), (cx + sz // 3, cy)], fill=dim)
    draw.polygon([(cx + sz, cy), (cx, cy + h4), (cx + sz // 3, cy)],
                 fill=tuple(max(0, c - 22) for c in dim))
    draw.polygon([(cx - sz, cy), (cx, cy - h4), (cx - sz // 3, cy)], fill=dim)
    draw.polygon([(cx - sz, cy), (cx, cy + h4), (cx - sz // 3, cy)],
                 fill=tuple(max(0, c - 22) for c in dim))
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=acc)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=lbl)
    draw.text((cx, cy - sz - 7), "N", fill=lbl, anchor="mb")


# ── Main render ───────────────────────────────────────────────────────────────

def _in_room(tx: int, ty: int, rooms: list[dict]) -> bool:
    return any(r["x"] <= tx < r["x"] + r["w"] and r["y"] <= ty < r["y"] + r["h"]
               for r in rooms)


def render(map_data: dict, tile_px: int = TILE_SIZE) -> io.BytesIO:
    tiles  = map_data["tiles"]
    H = len(tiles); W = len(tiles[0]) if H else 0
    rooms  = map_data.get("rooms", [])
    img_w, img_h = W * tile_px, H * tile_px
    pal    = _theme_for(map_data)
    mtype  = map_data.get("map_type", "dungeon")
    dungeon_style = mtype in ("dungeon", "interior", "wildemount")

    img  = Image.new("RGBA", (img_w, img_h), (*pal["void"], 255))
    draw = ImageDraw.Draw(img)

    def is_open(nx: int, ny: int) -> bool:
        return 0 <= ny < H and 0 <= nx < W and tiles[ny][nx] != WALL

    # Pre-compute per-tile warmth (torch glow from room centres)
    warm_col = pal.get("warm", (255, 168, 72))
    wbias    = _warm_bias(warm_col)
    warmth_map: list[list[float]] = [[0.0] * W for _ in range(H)]
    if dungeon_style and rooms and tile_px >= 10:
        for room in rooms:
            cx_r  = room["x"] + room["w"] / 2
            cy_r  = room["y"] + room["h"] / 2
            radius = math.sqrt(room["w"] ** 2 + room["h"] ** 2) / 2 + 0.5
            for ty2 in range(max(0, room["y"] - 1),
                             min(H, room["y"] + room["h"] + 1)):
                for tx2 in range(max(0, room["x"] - 1),
                                 min(W, room["x"] + room["w"] + 1)):
                    if tiles[ty2][tx2] == WALL:
                        continue
                    dist = math.sqrt((tx2 + 0.5 - cx_r) ** 2 +
                                     (ty2 + 0.5 - cy_r) ** 2)
                    w = max(0.0, 1.0 - dist / radius) ** 1.6
                    if w > warmth_map[ty2][tx2]:
                        warmth_map[ty2][tx2] = w

    # ── Pass 0: Wall stone texture ─────────────────────────────────────────────
    if tile_px >= 8:
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    _draw_wall_stone(draw, rx * tile_px, ry * tile_px, tile_px, pal)

    # ── Pass 1: Floor / terrain tiles ─────────────────────────────────────────
    for ry, row in enumerate(tiles):
        for rx, t in enumerate(row):
            if t == WALL:
                continue
            px, py   = rx * tile_px, ry * tile_px
            in_room  = _in_room(rx, ry, rooms) if rooms else True
            warmth   = warmth_map[ry][rx] if dungeon_style else 0.0

            if t in (FLOOR, *FEATURE_TILES):
                base = pal["room"] if in_room else pal["corr"]
                _draw_floor_tile(draw, px, py, tile_px, base,
                                 dungeon_style, warmth, wbias)
            elif t == WATER:   _draw_water(draw, px, py, tile_px)
            elif t == LAVA:    _draw_lava(draw, px, py, tile_px)
            elif t == TREES:   _draw_trees(draw, px, py, tile_px)
            elif t == ROAD:
                rng = _rng_for(px, py); v = int((rng.random() - 0.5) * 12)
                draw.rectangle([px, py, px + tile_px - 1, py + tile_px - 1],
                                fill=(_clamp(144 + v), _clamp(122 + v),
                                      _clamp(90 + v)))
            elif t == RUBBLE:  _draw_rubble(draw, px, py, tile_px)
            elif t == GRASS:   _draw_grass(draw, px, py, tile_px)
            elif t == DIRT:    _draw_dirt(draw, px, py, tile_px)
            elif t == SNOW:    _draw_snow(draw, px, py, tile_px)

    # ── Pass 1.5: Floor edge trim inside rooms ────────────────────────────────
    if dungeon_style and tile_px >= 12 and rooms:
        tw = max(2, tile_px // 9)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL or t not in (FLOOR, *FEATURE_TILES):
                    continue
                if not _in_room(rx, ry, rooms):
                    continue
                px, py = rx * tile_px, ry * tile_px
                trim   = _tint(pal["room"], -34)
                if rx > 0       and tiles[ry][rx - 1] == WALL:
                    draw.rectangle([px, py, px + tw - 1, py + tile_px - 1], fill=trim)
                if rx + 1 < W   and tiles[ry][rx + 1] == WALL:
                    draw.rectangle([px + tile_px - tw, py,
                                    px + tile_px - 1, py + tile_px - 1], fill=trim)
                if ry > 0       and tiles[ry - 1][rx] == WALL:
                    draw.rectangle([px, py, px + tile_px - 1, py + tw - 1], fill=trim)
                if ry + 1 < H   and tiles[ry + 1][rx] == WALL:
                    draw.rectangle([px, py + tile_px - tw,
                                    px + tile_px - 1, py + tile_px - 1], fill=trim)

    # ── Pass 1.6: Stone slab grid (large mortar joints) ───────────────────────
    if dungeon_style and tile_px >= 16 and rooms:
        _draw_slab_lines(draw, rooms, tile_px, pal)

    # ── Pass 2: Wall face rendering ───────────────────────────────────────────
    if tile_px >= 8:
        face_col = pal.get("face", _tint(pal["void"], 30))
        face_hi  = _tint(face_col, 28)
        face_h   = max(3, tile_px // 4)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                if is_open(rx, ry + 1):
                    draw.rectangle([px, py + tile_px - face_h,
                                    px + tile_px - 1, py + tile_px - 1], fill=face_col)
                    draw.line([(px, py + tile_px - face_h),
                               (px + tile_px - 1, py + tile_px - face_h)],
                              fill=face_hi, width=1)
                if is_open(rx + 1, ry):
                    draw.rectangle([px + tile_px - face_h, py,
                                    px + tile_px - 1, py + tile_px - 1], fill=face_col)
                    draw.line([(px + tile_px - face_h, py),
                               (px + tile_px - face_h, py + tile_px - 1)],
                              fill=face_hi, width=1)

    # ── Pass 3: Ambient occlusion — blurred soft shadow ───────────────────────
    if tile_px >= 8:
        ao      = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        ao_draw = ImageDraw.Draw(ao)
        ao_depth = max(4, int(tile_px * 0.72))
        dirs = [
            (0, -1, lambda p, q, si: (p, q, p + tile_px - 1, q + si)),
            (0,  1, lambda p, q, si: (p, q + tile_px - si - 1, p + tile_px - 1, q + tile_px - 1)),
            (-1, 0, lambda p, q, si: (p, q, p + si, q + tile_px - 1)),
            (1,  0, lambda p, q, si: (p + tile_px - si - 1, q, p + tile_px - 1, q + tile_px - 1)),
        ]
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                for dx, dy, rect_fn in dirs:
                    nx_, ny_ = rx + dx, ry + dy
                    if 0 <= ny_ < H and 0 <= nx_ < W and tiles[ny_][nx_] == WALL:
                        for si in range(ao_depth):
                            alpha = int(200 * (1 - si / ao_depth) ** 1.8)
                            ao_draw.rectangle(list(rect_fn(px, py, si)),
                                              fill=(0, 0, 0, alpha))
        # Gaussian blur softens the shadow edge
        ao  = ao.filter(ImageFilter.GaussianBlur(radius=max(2, tile_px // 7)))
        img = Image.alpha_composite(img, ao)
        draw = ImageDraw.Draw(img)

    # ── Pass 3.5: Room glow overlay (Gaussian-blurred torchlight) ─────────────
    if dungeon_style and rooms and tile_px >= 10:
        glow_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        gd       = ImageDraw.Draw(glow_img)
        for room in rooms:
            cx_r = int((room["x"] + room["w"] / 2) * tile_px)
            cy_r = int((room["y"] + room["h"] / 2) * tile_px)
            r_max = max(int(max(room["w"], room["h"]) * tile_px / 2 * 0.98),
                        tile_px * 2)
            for si in range(50, 0, -1):
                frac  = si / 50
                alpha = int(52 * (1 - frac) ** 1.3)
                rc    = int(r_max * frac)
                gd.ellipse([cx_r - rc, cy_r - rc, cx_r + rc, cy_r + rc],
                            fill=(*warm_col, alpha))
        # Blur turns flat discs into soft cinematic torch glow
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=tile_px))
        img  = Image.alpha_composite(img, glow_img)
        draw = ImageDraw.Draw(img)

    # ── Pass 4: Feature overlays ───────────────────────────────────────────────
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

    # ── Pass 4.5: Torch halos at features (large + blurred) ───────────────────
    if dungeon_style and tile_px >= 10:
        torch_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        td        = ImageDraw.Draw(torch_img)
        t_radius  = int(tile_px * 2.6)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t not in (DOOR, STAIRS, CHEST):
                    continue
                ctx = rx * tile_px + tile_px // 2
                cty = ry * tile_px + tile_px // 2
                for ri in range(t_radius, 0, -1):
                    alpha = int(72 * (1 - ri / t_radius) ** 2.2)
                    td.ellipse([ctx - ri, cty - ri, ctx + ri, cty + ri],
                                fill=(*warm_col, alpha))
        torch_img = torch_img.filter(
            ImageFilter.GaussianBlur(radius=max(4, tile_px // 2)))
        img  = Image.alpha_composite(img, torch_img)
        draw = ImageDraw.Draw(img)

    # ── Pass 5: Ink wall outlines ──────────────────────────────────────────────
    if tile_px >= 6:
        ink = pal["ink"]; hi = pal["hi"]
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx * tile_px, ry * tile_px
                if is_open(rx, ry + 1):
                    draw.line([(px, py + tile_px), (px + tile_px, py + tile_px)],
                              fill=ink, width=2)
                    draw.line([(px, py + tile_px - 1), (px + tile_px, py + tile_px - 1)],
                              fill=hi, width=1)
                if is_open(rx, ry - 1):
                    draw.line([(px, py), (px + tile_px, py)], fill=ink, width=2)
                if is_open(rx + 1, ry):
                    draw.line([(px + tile_px, py), (px + tile_px, py + tile_px)],
                              fill=ink, width=2)
                if is_open(rx - 1, ry):
                    draw.line([(px, py), (px, py + tile_px)], fill=ink, width=2)

    # ── Pass 6: Room labels ────────────────────────────────────────────────────
    if tile_px >= 12:
        lbl_col = pal.get("label", (208, 188, 148))
        for room in rooms:
            rw_r = room.get("w", 0); rh_r = room.get("h", 0)
            rt   = room.get("type", room.get("room_type", ""))
            if rw_r < 4 or rh_r < 4 or not rt:
                continue
            cx2 = (room["x"] + rw_r // 2) * tile_px
            cy2 = (room["y"] + rh_r // 2) * tile_px
            text = rt.replace("_", " ")[:14]
            fs   = max(8, int(tile_px * 0.42))
            tw2  = len(text) * (fs // 2 + 1) + 12; th2 = fs + 12
            draw.rectangle([cx2 - tw2 // 2, cy2 - th2 // 2,
                             cx2 + tw2 // 2, cy2 + th2 // 2],
                           fill=(6, 4, 3, 220))
            draw.text((cx2, cy2), text, fill=lbl_col, anchor="mm")

    # ── Pass 7: Deep edge vignette ─────────────────────────────────────────────
    vig = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    steps     = 28
    thickness = max(2, min(img_w, img_h) // (steps * 3))
    for i in range(steps):
        alpha = int(145 * (i / steps) ** 1.5)
        pad   = i * thickness * 2
        if pad >= img_w - pad or pad >= img_h - pad:
            break
        vd.rectangle([pad, pad, img_w - pad, img_h - pad],
                     outline=(0, 0, 0, alpha), width=thickness * 2)
    img = Image.alpha_composite(img, vig)

    # ── Pass 7.5: Decorative map border ───────────────────────────────────────
    if tile_px >= 10 and img_w >= 140:
        draw = ImageDraw.Draw(img)
        acc  = pal.get("accent", (188, 148, 60))
        # Outer line
        draw.rectangle([4, 4, img_w - 5, img_h - 5],
                        outline=(*acc, 180), width=1)
        # Inner line
        acc_dim = _tint(acc, -35)
        draw.rectangle([9, 9, img_w - 10, img_h - 10],
                        outline=(*acc_dim, 130), width=1)
        # Corner ornaments
        for ocx, ocy in [(9, 9), (img_w - 10, 9),
                          (9, img_h - 10), (img_w - 10, img_h - 10)]:
            draw.ellipse([ocx - 3, ocy - 3, ocx + 3, ocy + 3],
                          fill=(*acc, 200))

    # ── Pass 8: Compass rose ───────────────────────────────────────────────────
    if tile_px >= 8 and img_w >= 80 and img_h >= 60:
        draw  = ImageDraw.Draw(img)
        cr_sz = max(20, min(W, H) * tile_px // 14)
        _draw_compass_rose(draw, img_w - cr_sz - 20, img_h - cr_sz - 20, cr_sz, pal)

    # ── Flatten to RGB ─────────────────────────────────────────────────────────
    rgb = Image.new("RGB", img.size, pal["void"])
    rgb.paste(img, mask=img.split()[3])

    # ── Pass 9: Post-process — contrast + saturation boost ────────────────────
    rgb = ImageEnhance.Contrast(rgb).enhance(1.10)
    rgb = ImageEnhance.Color(rgb).enhance(1.18)

    buf = io.BytesIO()
    rgb.save(buf, format="PNG", optimize=False)
    buf.seek(0)
    return buf


def scale_for_discord(map_data: dict, max_px: int = 1280) -> io.BytesIO:
    tiles  = map_data.get("tiles", [[]])
    w = len(tiles[0]) if tiles else 1
    h = len(tiles)
    tile_px = max(6, min(max_px // max(w, 1), max_px // max(h, 1), TILE_SIZE))
    return render(map_data, tile_px=tile_px)
