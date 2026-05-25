"""
Render tile maps to PNG via Pillow — FF-quality dungeon aesthetic.

v3: 28 px tiles · wall stone block texture · warm room torch glow ·
floor inner bevel · edge trim strip · stronger AO (depth 70 %, α 195) ·
torch spot glow at features · theme-matched ambient light colour.
"""
from __future__ import annotations
import io
import math
import random as _rnd
from PIL import Image, ImageDraw

# ── Tile IDs ──────────────────────────────────────────────────────────────────
WALL   = 0;  FLOOR  = 1;  DOOR   = 2;  WATER  = 3;  LAVA   = 4
TREES  = 5;  ROAD   = 6;  RUBBLE = 7;  PILLAR = 8;  CHEST  = 9
STAIRS = 10; TRAP   = 11; GRASS  = 12; DIRT   = 13; SNOW   = 14

FEATURE_TILES = {DOOR, PILLAR, CHEST, STAIRS, TRAP}
TERRAIN_TILES = {WATER, LAVA, TREES, ROAD, RUBBLE, GRASS, DIRT, SNOW}

# ── Theme palettes ─────────────────────────────────────────────────────────────
# warm = ambient light colour for torch/bioluminescent glow
THEMES: dict[str, dict] = {
    "standard":     dict(void=(10,9,15),    room=(92,74,52),    corr=(62,50,36),
                         ink=(4,3,6),       hi=(130,105,72),    accent=(210,152,52),
                         label=(245,220,170), face=(48,40,30),  warm=(255,168,72)),
    "generic":      dict(void=(10,9,15),    room=(92,74,52),    corr=(62,50,36),
                         ink=(4,3,6),       hi=(130,105,72),    accent=(210,152,52),
                         label=(245,220,170), face=(48,40,30),  warm=(255,168,72)),
    "cave":         dict(void=(10,9,8),     room=(72,58,44),    corr=(52,42,32),
                         ink=(5,4,4),       hi=(106,86,64),     accent=(128,88,48),
                         label=(215,190,155), face=(36,30,22),  warm=(255,158,62)),
    "crypt":        dict(void=(10,8,16),    room=(62,52,66),    corr=(46,38,52),
                         ink=(5,4,8),       hi=(96,80,100),     accent=(155,68,110),
                         label=(205,178,205), face=(30,24,40),  warm=(200,130,220)),
    "underdark":    dict(void=(6,6,16),     room=(46,44,70),    corr=(32,30,54),
                         ink=(3,3,10),      hi=(72,64,108),     accent=(38,128,220),
                         label=(158,148,220), face=(20,18,44),  warm=(80,140,255)),
    "bazzoxan":     dict(void=(6,6,16),     room=(46,44,70),    corr=(32,30,54),
                         ink=(3,3,10),      hi=(72,64,108),     accent=(38,128,220),
                         label=(158,148,220), face=(20,18,44),  warm=(80,140,255)),
    "sewers":       dict(void=(8,12,8),     room=(48,64,44),    corr=(36,50,32),
                         ink=(4,6,4),       hi=(74,98,66),      accent=(22,118,52),
                         label=(158,212,148), face=(22,34,18),  warm=(160,220,80)),
    "cerberus_lab": dict(void=(8,8,22),     room=(48,46,74),    corr=(36,34,58),
                         ink=(4,4,12),      hi=(82,76,112),     accent=(100,120,255),
                         label=(175,168,240), face=(24,22,52),  warm=(100,160,255)),
    "ruins_aeor":   dict(void=(10,12,18),   room=(54,60,72),    corr=(40,44,58),
                         ink=(5,6,9),       hi=(88,95,112),     accent=(72,108,188),
                         label=(185,200,228), face=(28,32,48),  warm=(120,160,220)),
    "temple":       dict(void=(12,10,8),    room=(88,72,52),    corr=(62,52,38),
                         ink=(6,5,4),       hi=(125,104,74),    accent=(200,150,42),
                         label=(238,212,168), face=(44,36,24),  warm=(255,200,80)),
    "tundra":       dict(void=(68,78,92),   room=(208,218,232), corr=(185,196,212),
                         ink=(48,58,68),    hi=(238,244,252),   accent=(128,148,172),
                         label=(48,58,75),  face=(148,162,180), warm=(200,220,255)),
    "forest":       dict(void=(8,18,8),     room=(38,84,32),    corr=(28,62,24),
                         ink=(4,9,4),       hi=(58,112,48),     accent=(72,148,58),
                         label=(188,232,158), face=(18,44,14),  warm=(180,220,80)),
    "coastal":      dict(void=(12,22,12),   room=(40,80,36),    corr=(30,62,28),
                         ink=(5,9,4),       hi=(62,104,52),     accent=(36,96,148),
                         label=(188,222,188), face=(20,42,16),  warm=(80,200,220)),
    "badlands":     dict(void=(36,26,16),   room=(118,92,62),   corr=(94,76,50),
                         ink=(18,12,8),     hi=(148,120,80),    accent=(188,88,24),
                         label=(235,200,148), face=(66,50,32),  warm=(255,160,60)),
    "plains":       dict(void=(16,30,14),   room=(48,94,38),    corr=(58,98,48),
                         ink=(8,15,6),      hi=(92,138,70),     accent=(92,128,58),
                         label=(212,242,170), face=(28,56,20),  warm=(200,240,80)),
    "jungle":       dict(void=(6,14,6),     room=(32,74,28),    corr=(24,58,20),
                         ink=(3,7,3),       hi=(52,106,40),     accent=(58,128,48),
                         label=(168,218,138), face=(14,38,10),  warm=(180,240,60)),
    "wastes":       dict(void=(36,26,16),   room=(118,92,62),   corr=(94,76,50),
                         ink=(18,12,8),     hi=(148,120,80),    accent=(210,68,12),
                         label=(235,200,148), face=(66,50,32),  warm=(255,140,40)),
    "mountain":     dict(void=(44,44,54),   room=(122,116,128), corr=(98,94,106),
                         ink=(22,22,28),    hi=(158,152,164),   accent=(90,102,134),
                         label=(212,212,232), face=(74,74,88),  warm=(220,220,255)),
    "savalirwood":  dict(void=(6,14,6),     room=(32,74,28),    corr=(24,58,20),
                         ink=(3,7,3),       hi=(52,106,40),     accent=(72,144,58),
                         label=(168,222,138), face=(14,38,10),  warm=(180,240,80)),
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


TILE_SIZE = 28


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rng_for(px: int, py: int) -> _rnd.Random:
    return _rnd.Random(px * 1000003 + py)

def _clamp(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, v))

def _tint(col: tuple, delta: int) -> tuple:
    return tuple(_clamp(c + delta) for c in col)

def _warm_bias(warm: tuple) -> tuple[int, int, int]:
    """RGB delta per unit of warmth, derived from the theme's ambient light colour."""
    return (
        (warm[0] - 128) // 11,
        (warm[1] - 128) // 14,
        (warm[2] - 128) // 11,
    )


# ── Wall stone texture ────────────────────────────────────────────────────────

def _draw_wall_stone(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int,
                     pal: dict) -> None:
    rng   = _rng_for(px, py)
    void  = pal["void"]
    stone = _tint(void, int(rng.random() * 10 + 5))
    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=stone)
    if ts < 10:
        return
    mortar  = _tint(void, -7)
    ty_idx  = py // ts
    # Horizontal mortar seam at mid-tile
    mid_y = py + ts // 2
    draw.line([(px, mid_y), (px + ts - 1, mid_y)], fill=mortar, width=1)
    # Vertical seam — offset every other row for brick bond
    offset  = 0 if ty_idx % 2 == 0 else ts // 2
    v_x     = px + (ts // 3 + offset) % ts
    if px <= v_x < px + ts:
        draw.line([(v_x, py), (v_x, mid_y - 1)], fill=mortar, width=1)
    # Random surface patches
    if rng.random() < 0.16:
        patch_col = _tint(stone, int(rng.random() * 16) - 8)
        pw = max(2, int(rng.random() * ts // 4))
        ph = max(1, int(rng.random() * ts // 6))
        pfx = px + int(rng.random() * (ts - pw - 2)) + 1
        pfy = py + int(rng.random() * (ts - ph - 2)) + 1
        draw.rectangle([pfx, pfy, pfx + pw, pfy + ph], fill=patch_col)


# ── Floor tile ────────────────────────────────────────────────────────────────

def _draw_floor_tile(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int,
                     base_col: tuple, dungeon_style: bool = False,
                     warmth: float = 0.0,
                     wbias: tuple[int,int,int] = (6, 1, -3)) -> None:
    rng = _rng_for(px, py)
    v   = int((rng.random() - 0.5) * 14)
    col = _tint(base_col, v)

    if warmth > 0.02:
        col = (
            _clamp(col[0] + int(warmth * wbias[0])),
            _clamp(col[1] + int(warmth * wbias[1])),
            _clamp(col[2] + int(warmth * wbias[2])),
        )

    draw.rectangle([px, py, px + ts - 1, py + ts - 1], fill=col)

    if dungeon_style and ts >= 10:
        grout = _tint(col, -32)
        hi    = _tint(col, 26)
        # Grout lines — right and bottom edges
        draw.line([(px, py + ts - 1), (px + ts - 2, py + ts - 1)], fill=grout, width=1)
        draw.line([(px + ts - 1, py), (px + ts - 1, py + ts - 2)], fill=grout, width=1)
        # Inner bevel — top and left edge highlight for chiseled stone look
        if ts >= 14:
            draw.line([(px + 1, py + 1), (px + ts - 3, py + 1)], fill=hi, width=1)
            draw.line([(px + 1, py + 1), (px + 1, py + ts - 3)], fill=hi, width=1)
        # Occasional crack
        if ts >= 16 and rng.random() < 0.08:
            crack = _tint(col, -40)
            x1 = px + ts // 4 + int(rng.random() * ts // 2)
            y1 = py + ts // 4 + int(rng.random() * ts // 2)
            draw.line([(x1, y1),
                       (x1 + int((rng.random()-.5)*ts//2),
                        y1 + int((rng.random()-.5)*ts//2))],
                      fill=crack, width=1)


# ── Feature sprites ───────────────────────────────────────────────────────────

def _draw_door(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    dw = max(5, int(ts * 0.58)); dh = max(6, int(ts * 0.82))
    dx = px + (ts - dw) // 2;   dy = py + (ts - dh) // 2
    draw.rectangle([dx+2, dy+2, dx+dw+2, dy+dh+2], fill=(0,0,0,100))
    draw.rectangle([dx, dy, dx+dw, dy+dh], fill=(105,54,18))
    top_h = max(2, int(dh * 0.36))
    draw.rectangle([dx, dy, dx+dw, dy+top_h], fill=(68,36,8))
    panel_pad = max(2, ts // 9)
    draw.rectangle([dx+panel_pad, dy+top_h+2, dx+dw-panel_pad, dy+dh-panel_pad], fill=(80,40,10))
    band_y = dy + int(dh * 0.55)
    draw.rectangle([dx, band_y, dx+dw, band_y+2], fill=(38,34,28))
    kx = dx + int(dw * 0.72); ky = dy + dh // 2
    draw.ellipse([kx-2, ky-2, kx+2, ky+2], fill=(218,165,56))
    draw.rectangle([dx, dy, dx+dw, dy+dh], outline=(22,8,4), width=1)


def _draw_pillar(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts // 2; my = py + ts // 2
    r  = max(4, int(ts * 0.40))
    draw.ellipse([mx-r+3, my-r+3, mx+r+3, my+r+3], fill=(0,0,0,100))
    draw.ellipse([mx-r, my-r, mx+r, my+r], fill=(68,44,20))
    rm = max(3, int(r * 0.76))
    draw.ellipse([mx-rm, my-rm, mx+rm, my+rm], fill=(162,128,84))
    if ts >= 16:
        for i in range(6):
            ang = math.pi * 2 * i / 6
            lx = int(mx + rm * 0.85 * math.cos(ang))
            ly = int(my + rm * 0.85 * math.sin(ang))
            draw.line([(mx,my),(lx,ly)], fill=_tint((162,128,84),-22), width=1)
    rh = max(2, int(r * 0.42))
    draw.ellipse([mx-r+2, my-r+2, mx-r+2+rh*2, my-r+2+rh], fill=(228,200,152))
    draw.ellipse([mx-r, my-r, mx+r, my+r], outline=(210,172,112), width=1)


def _draw_chest(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts // 2; my = py + ts // 2
    cw = max(6, int(ts * 0.64)); ch = max(5, int(ts * 0.50))
    cx = mx - cw // 2;           cy2 = my - ch // 2 - 1
    draw.rectangle([cx+2, cy2+2, cx+cw+2, cy2+ch+2], fill=(0,0,0,100))
    draw.rectangle([cx, cy2, cx+cw, cy2+ch], fill=(112,58,18))
    lid_h = max(2, int(ch * 0.36))
    draw.rectangle([cx, cy2, cx+cw, cy2+lid_h], fill=(70,36,8))
    draw.rectangle([cx, cy2+lid_h+1, cx+cw, cy2+lid_h+2], fill=(42,38,32))
    for cox, coy in [(cx,cy2),(cx+cw-3,cy2),(cx,cy2+ch-3),(cx+cw-3,cy2+ch-3)]:
        draw.rectangle([cox, coy, cox+3, coy+3], fill=(195,152,48))
    latch_y = cy2 + int(ch * 0.45)
    draw.line([cx+2, latch_y, cx+cw-2, latch_y], fill=(205,162,64), width=2)
    draw.ellipse([mx-3, latch_y-2, mx+3, latch_y+4], fill=(252,208,72))
    draw.rectangle([cx, cy2, cx+cw, cy2+ch], outline=(24,8,4), width=1)


def _draw_stairs(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    sw = max(8, int(ts*0.72)); sh = max(6, int(ts*0.68))
    x0 = px + (ts-sw)//2;       y0 = py + (ts-sh)//2
    ns = 6
    for si in range(ns):
        shrink = si * sw // (ns * 7)
        sx = x0 + shrink; sw2 = max(2, sw - shrink*2)
        sy = y0 + int(si * sh / ns); sh2 = max(1, int(sh / ns))
        col = (148,116,76) if si % 2 == 0 else (168,136,94)
        draw.rectangle([sx, sy, sx+sw2, sy+sh2], fill=col)
        draw.line([(sx, sy+sh2),(sx+sw2, sy+sh2)], fill=(0,0,0,70), width=1)
    mx2 = x0 + sw//2; ay = y0 + sh + 3
    if ay + 4 < py + ts:
        draw.polygon([(mx2, ay+4),(mx2-3,ay),(mx2+3,ay)], fill=(200,165,100))


def _draw_trap(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    mx = px + ts//2; my = py + ts//2
    for i, r in enumerate([int(ts*0.46), int(ts*0.32), int(ts*0.18)]):
        if r < 1: continue
        draw.ellipse([mx-r, my-r, mx+r, my+r], outline=(185,48,48, 55+i*44), width=1)
    pp = max(3, int(ts*0.25))
    draw.ellipse([mx-pp, my-pp, mx+pp, my+pp], fill=(90,32,32,180))
    draw.ellipse([mx-pp, my-pp, mx+pp, my+pp], outline=(185,48,48), width=1)
    draw.ellipse([mx-2, my-2, mx+2, my+2], fill=(200,60,60))


# ── Terrain tiles ─────────────────────────────────────────────────────────────

def _draw_water(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    for yi in range(ts):
        t = yi / max(1, ts-1)
        draw.line([(px, py+yi),(px+ts-1, py+yi)],
                  fill=(_clamp(int(18+t*12)), _clamp(int(42+t*24)), _clamp(int(138+t*32))))
    n_waves = max(2, ts // 5)
    for wi in range(n_waves):
        wy_base = py + ts * (wi+0.5) / n_waves
        pts = []
        for xi in range(ts+1):
            wy = int(wy_base + math.sin((px+xi)*0.55 + wi*3.7) * max(1, ts//10))
            pts.append((px+xi, _clamp(wy, py, py+ts-1)))
        if len(pts) >= 2:
            draw.line(pts, fill=(148,218,255, max(25, 100-wi*22)), width=1)
    rng = _rng_for(px, py)
    for _ in range(3):
        fx = px + int(rng.random() * ts)
        fy = py + int(rng.random() * ts)
        draw.ellipse([fx-1, fy-1, fx+1, fy+1], fill=(212,238,255,80))


def _draw_lava(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=(48,6,2))
    rng = _rng_for(px, py)
    for _ in range(4):
        bx = px+int(rng.random()*ts); by = py+int(rng.random()*ts)
        br = max(2, int(rng.random()*ts//3+1))
        h_ = int(140+rng.random()*115)
        draw.ellipse([bx-br,by-br,bx+br,by+br], fill=(_clamp(h_),_clamp(h_//3+20),0,175))
    for _ in range(3):
        x1=px+int(rng.random()*ts); y1=py+int(rng.random()*ts)
        x2=px+int(rng.random()*ts); y2=py+int(rng.random()*ts)
        draw.line([(x1,y1),(x2,y2)], fill=(255,110,12,210), width=1)


def _draw_trees(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=(12,30,8))
    rng = _rng_for(px, py)
    n = 1 if rng.random() > 0.38 else 2
    for _ in range(n):
        tcx = px + int(ts*(0.20+rng.random()*0.60))
        tcy = py + int(ts*(0.20+rng.random()*0.60))
        if ts >= 14:
            tw = max(1, ts//10)
            draw.rectangle([tcx-tw, tcy, tcx+tw, tcy+ts//4], fill=(58,32,8))
        cr = max(4, ts//3+1)
        draw.ellipse([tcx-cr+3, tcy-cr//2+3, tcx+cr+3, tcy+cr//2+3], fill=(0,0,0,75))
        gb = _clamp(52+int(rng.random()*40))
        draw.ellipse([tcx-cr, tcy-cr, tcx+cr, tcy+cr], fill=(14,gb,10))
        hr = max(3, cr - cr//3)
        draw.ellipse([tcx-hr-1, tcy-hr-2, tcx+hr//2, tcy+hr//2], fill=(22,_clamp(gb+32),14))


def _draw_rubble(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=(52,42,26))
    rng = _rng_for(px, py)
    for ri in range(6):
        rfx = px+int(rng.random()*(ts-3)); rfy = py+int(rng.random()*(ts-3))
        rfw = max(1, 2+int(rng.random()*ts//4)); rfh = max(1, 1+int(rng.random()*ts//5))
        draw.rectangle([rfx,rfy,rfx+rfw,rfy+rfh],
                       fill=(102,84,58) if ri%2==0 else (42,32,20))
        draw.line([(rfx,rfy+rfh),(rfx+rfw,rfy+rfh)], fill=(0,0,0,50), width=1)


def _draw_grass(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); gv = rng.random()
    base = (int(24+gv*18), int(72+gv*38), int(14+gv*14))
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=base)
    if ts >= 10:
        for _ in range(4):
            bx=px+int(rng.random()*ts); by=py+int(rng.random()*ts); br=max(1,ts//7)
            lv=int(rng.random()*22)-8
            draw.ellipse([bx-br,by-br,bx+br,by+br],
                         fill=(_clamp(base[0]+lv),_clamp(base[1]+lv+10),_clamp(base[2])))


def _draw_dirt(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); dv = rng.random()
    base = (int(132+dv*26), int(100+dv*22), int(56+dv*18))
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=base)
    if ts >= 10:
        for _ in range(3):
            bx=px+int(rng.random()*ts); by=py+int(rng.random()*ts); br=max(1,ts//8)
            v2=int(rng.random()*18)-9
            draw.ellipse([bx-br,by-br,bx+br,by+br],
                         fill=(_clamp(base[0]+v2),_clamp(base[1]+v2),_clamp(base[2]+v2)))


def _draw_snow(draw: ImageDraw.ImageDraw, px: int, py: int, ts: int) -> None:
    rng = _rng_for(px, py); sv = rng.random()
    base = (min(255,int(205+sv*48)), min(255,int(214+sv*40)), min(255,int(225+sv*30)))
    draw.rectangle([px, py, px+ts-1, py+ts-1], fill=base)
    if ts >= 12:
        for _ in range(3):
            draw.point((px+int(rng.random()*ts), py+int(rng.random()*ts)),
                       fill=(255,255,255,160))


def _draw_compass_rose(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                       sz: int, pal: dict) -> None:
    acc = pal.get("accent", (180,140,60))
    dim = tuple(max(0, c-55) for c in acc)
    lbl = pal.get("label", (200,180,140))
    h4  = sz // 4
    draw.polygon([(cx,cy-sz),(cx-h4,cy),(cx,cy-sz//3)], fill=acc)
    draw.polygon([(cx,cy-sz),(cx+h4,cy),(cx,cy-sz//3)], fill=_tint(acc,-20))
    draw.polygon([(cx,cy+sz),(cx-h4,cy),(cx,cy+sz//3)], fill=dim)
    draw.polygon([(cx,cy+sz),(cx+h4,cy),(cx,cy+sz//3)], fill=tuple(max(0,c-30) for c in dim))
    draw.polygon([(cx+sz,cy),(cx,cy-h4),(cx+sz//3,cy)], fill=dim)
    draw.polygon([(cx+sz,cy),(cx,cy+h4),(cx+sz//3,cy)], fill=tuple(max(0,c-20) for c in dim))
    draw.polygon([(cx-sz,cy),(cx,cy-h4),(cx-sz//3,cy)], fill=dim)
    draw.polygon([(cx-sz,cy),(cx,cy+h4),(cx-sz//3,cy)], fill=tuple(max(0,c-20) for c in dim))
    draw.ellipse([cx-4,cy-4,cx+4,cy+4], fill=acc)
    draw.ellipse([cx-2,cy-2,cx+2,cy+2], fill=lbl)
    draw.text((cx, cy-sz-6), "N", fill=lbl, anchor="mb")


# ── Main render ───────────────────────────────────────────────────────────────

def _in_room(tx: int, ty: int, rooms: list[dict]) -> bool:
    return any(r["x"] <= tx < r["x"]+r["w"] and r["y"] <= ty < r["y"]+r["h"] for r in rooms)


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

    # Pre-compute per-tile warmth from room centres (torch glow)
    warm_col = pal.get("warm", (255,168,72))
    wbias    = _warm_bias(warm_col)
    warmth_map: list[list[float]] = [[0.0]*W for _ in range(H)]
    if dungeon_style and rooms and tile_px >= 10:
        for room in rooms:
            cx_r = room["x"] + room["w"] / 2
            cy_r = room["y"] + room["h"] / 2
            radius = math.sqrt(room["w"]**2 + room["h"]**2) / 2 + 0.5
            for ty2 in range(max(0, room["y"]-1), min(H, room["y"]+room["h"]+1)):
                for tx2 in range(max(0, room["x"]-1), min(W, room["x"]+room["w"]+1)):
                    if tiles[ty2][tx2] == WALL:
                        continue
                    dist = math.sqrt((tx2+0.5-cx_r)**2 + (ty2+0.5-cy_r)**2)
                    w = max(0.0, 1.0 - dist/radius) ** 1.6
                    if w > warmth_map[ty2][tx2]:
                        warmth_map[ty2][tx2] = w

    # ── Pass 0: Wall stone texture ────────────────────────────────────────────
    if tile_px >= 8:
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    _draw_wall_stone(draw, rx*tile_px, ry*tile_px, tile_px, pal)

    # ── Pass 1: Floor / terrain tiles ────────────────────────────────────────
    for ry, row in enumerate(tiles):
        for rx, t in enumerate(row):
            if t == WALL:
                continue
            px, py   = rx*tile_px, ry*tile_px
            in_room  = _in_room(rx, ry, rooms) if rooms else True
            warmth   = warmth_map[ry][rx] if dungeon_style else 0.0

            if t in (FLOOR, *FEATURE_TILES):
                base = pal["room"] if in_room else pal["corr"]
                _draw_floor_tile(draw, px, py, tile_px, base, dungeon_style, warmth, wbias)
            elif t == WATER:   _draw_water(draw, px, py, tile_px)
            elif t == LAVA:    _draw_lava(draw, px, py, tile_px)
            elif t == TREES:   _draw_trees(draw, px, py, tile_px)
            elif t == ROAD:
                rng = _rng_for(px, py); v = int((rng.random()-0.5)*10)
                draw.rectangle([px, py, px+tile_px-1, py+tile_px-1],
                                fill=(_clamp(140+v),_clamp(118+v),_clamp(88+v)))
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
                px, py = rx*tile_px, ry*tile_px
                trim = _tint(pal["room"], -28)
                if rx > 0   and tiles[ry][rx-1] == WALL:
                    draw.rectangle([px, py, px+tw-1, py+tile_px-1], fill=trim)
                if rx+1 < W and tiles[ry][rx+1] == WALL:
                    draw.rectangle([px+tile_px-tw, py, px+tile_px-1, py+tile_px-1], fill=trim)
                if ry > 0   and tiles[ry-1][rx] == WALL:
                    draw.rectangle([px, py, px+tile_px-1, py+tw-1], fill=trim)
                if ry+1 < H and tiles[ry+1][rx] == WALL:
                    draw.rectangle([px, py+tile_px-tw, px+tile_px-1, py+tile_px-1], fill=trim)

    # ── Pass 2: Wall face rendering ───────────────────────────────────────────
    if tile_px >= 8:
        face_col = pal.get("face", _tint(pal["void"], 28))
        face_hi  = _tint(face_col, 24)
        face_h   = max(3, tile_px // 4)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx*tile_px, ry*tile_px
                if is_open(rx, ry+1):
                    draw.rectangle([px, py+tile_px-face_h, px+tile_px-1, py+tile_px-1],
                                   fill=face_col)
                    draw.line([(px, py+tile_px-face_h),(px+tile_px-1, py+tile_px-face_h)],
                              fill=face_hi, width=1)
                if is_open(rx+1, ry):
                    draw.rectangle([px+tile_px-face_h, py, px+tile_px-1, py+tile_px-1],
                                   fill=face_col)
                    draw.line([(px+tile_px-face_h, py),(px+tile_px-face_h, py+tile_px-1)],
                              fill=face_hi, width=1)

    # ── Pass 3: Ambient occlusion (strong quadratic shadow) ───────────────────
    if tile_px >= 8:
        ao      = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
        ao_draw = ImageDraw.Draw(ao)
        ao_depth = max(4, int(tile_px * 0.70))
        dirs = [
            (0, -1, lambda px,py,si: (px, py, px+tile_px-1, py+si)),
            (0,  1, lambda px,py,si: (px, py+tile_px-si-1, px+tile_px-1, py+tile_px-1)),
            (-1, 0, lambda px,py,si: (px, py, px+si, py+tile_px-1)),
            (1,  0, lambda px,py,si: (px+tile_px-si-1, py, px+tile_px-1, py+tile_px-1)),
        ]
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t == WALL:
                    continue
                px, py = rx*tile_px, ry*tile_px
                for dx, dy, rect_fn in dirs:
                    nx_, ny_ = rx+dx, ry+dy
                    if 0 <= ny_ < H and 0 <= nx_ < W and tiles[ny_][nx_] == WALL:
                        for si in range(ao_depth):
                            alpha = int(195 * (1 - si/ao_depth) ** 1.75)
                            ao_draw.rectangle(list(rect_fn(px,py,si)), fill=(0,0,0,alpha))
        img  = Image.alpha_composite(img, ao)
        draw = ImageDraw.Draw(img)

    # ── Pass 3.5: Room glow overlay (ambient torchlight) ─────────────────────
    if dungeon_style and rooms and tile_px >= 10:
        glow_img = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
        gd       = ImageDraw.Draw(glow_img)
        for room in rooms:
            cx_r = int((room["x"] + room["w"]/2) * tile_px)
            cy_r = int((room["y"] + room["h"]/2) * tile_px)
            r_max = max(int(max(room["w"],room["h"]) * tile_px / 2 * 0.95), tile_px*2)
            for si in range(24, 0, -1):
                frac  = si / 24
                alpha = int(42 * (1 - frac) ** 1.5)
                rc    = int(r_max * frac)
                gd.ellipse([cx_r-rc, cy_r-rc, cx_r+rc, cy_r+rc], fill=(*warm_col, alpha))
        img  = Image.alpha_composite(img, glow_img)
        draw = ImageDraw.Draw(img)

    # ── Pass 4: Feature overlays ──────────────────────────────────────────────
    if tile_px >= 8:
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t not in FEATURE_TILES:
                    continue
                px, py = rx*tile_px, ry*tile_px
                if   t == DOOR:   _draw_door(draw, px, py, tile_px)
                elif t == PILLAR: _draw_pillar(draw, px, py, tile_px)
                elif t == CHEST:  _draw_chest(draw, px, py, tile_px)
                elif t == STAIRS: _draw_stairs(draw, px, py, tile_px)
                elif t == TRAP:   _draw_trap(draw, px, py, tile_px)

    # ── Pass 4.5: Torch spots at doors / stairs / chests ─────────────────────
    if dungeon_style and tile_px >= 10:
        torch_img = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
        td        = ImageDraw.Draw(torch_img)
        t_radius  = int(tile_px * 1.7)
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t not in (DOOR, STAIRS, CHEST):
                    continue
                cx_t = rx*tile_px + tile_px//2
                cy_t = ry*tile_px + tile_px//2
                for ri in range(t_radius, 0, -1):
                    alpha = int(65 * (1 - ri/t_radius) ** 2.0)
                    td.ellipse([cx_t-ri, cy_t-ri, cx_t+ri, cy_t+ri], fill=(*warm_col, alpha))
        img  = Image.alpha_composite(img, torch_img)
        draw = ImageDraw.Draw(img)

    # ── Pass 5: Ink wall outlines ─────────────────────────────────────────────
    if tile_px >= 6:
        ink = pal["ink"]; hi = pal["hi"]
        for ry, row in enumerate(tiles):
            for rx, t in enumerate(row):
                if t != WALL:
                    continue
                px, py = rx*tile_px, ry*tile_px
                if is_open(rx, ry+1):
                    draw.line([(px, py+tile_px),(px+tile_px, py+tile_px)], fill=ink, width=2)
                    draw.line([(px, py+tile_px-1),(px+tile_px, py+tile_px-1)], fill=hi, width=1)
                if is_open(rx, ry-1):
                    draw.line([(px, py),(px+tile_px, py)], fill=ink, width=2)
                if is_open(rx+1, ry):
                    draw.line([(px+tile_px, py),(px+tile_px, py+tile_px)], fill=ink, width=2)
                if is_open(rx-1, ry):
                    draw.line([(px, py),(px, py+tile_px)], fill=ink, width=2)

    # ── Pass 6: Room labels ───────────────────────────────────────────────────
    if tile_px >= 12:
        lbl_col = pal.get("label", (200,180,140))
        for room in rooms:
            rw_r = room.get("w",0); rh_r = room.get("h",0)
            rt   = room.get("type", room.get("room_type",""))
            if rw_r < 4 or rh_r < 4 or not rt:
                continue
            cx2 = (room["x"] + rw_r//2) * tile_px
            cy2 = (room["y"] + rh_r//2) * tile_px
            text = rt.replace("_"," ")[:14]
            fs   = max(8, int(tile_px * 0.42))
            tw2  = len(text)*(fs//2+1)+10; th2 = fs+10
            draw.rectangle([cx2-tw2//2, cy2-th2//2, cx2+tw2//2, cy2+th2//2],
                           fill=(6,4,3,215))
            draw.text((cx2, cy2), text, fill=lbl_col, anchor="mm")

    # ── Pass 7: Edge vignette ─────────────────────────────────────────────────
    vig = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
    vd  = ImageDraw.Draw(vig)
    steps = 20; thickness = max(2, min(img_w, img_h)//(steps*3))
    for i in range(steps):
        alpha = int(130 * (i/steps) ** 1.4)
        pad   = i * thickness * 2
        if pad >= img_w-pad or pad >= img_h-pad:
            break
        vd.rectangle([pad, pad, img_w-pad, img_h-pad], outline=(0,0,0,alpha), width=thickness*2)
    img = Image.alpha_composite(img, vig)

    # ── Pass 8: Compass rose ──────────────────────────────────────────────────
    if tile_px >= 8 and img_w >= 80 and img_h >= 60:
        draw = ImageDraw.Draw(img)
        cr_sz = max(18, min(W,H)*tile_px//16)
        _draw_compass_rose(draw, img_w-cr_sz-16, img_h-cr_sz-16, cr_sz, pal)

    rgb = Image.new("RGB", img.size, pal["void"])
    rgb.paste(img, mask=img.split()[3])
    buf = io.BytesIO()
    rgb.save(buf, format="PNG")
    buf.seek(0)
    return buf


def scale_for_discord(map_data: dict, max_px: int = 1280) -> io.BytesIO:
    tiles  = map_data.get("tiles", [[]])
    w = len(tiles[0]) if tiles else 1
    h = len(tiles)
    tile_px = max(6, min(max_px // max(w,1), max_px // max(h,1), TILE_SIZE))
    return render(map_data, tile_px=tile_px)
