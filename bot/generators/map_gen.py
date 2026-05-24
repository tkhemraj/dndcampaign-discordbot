"""
Procedural map generation — ported from the dndcampaign web app generator.

Tile values:
  0 = wall/void     1 = floor       2 = door
  3 = water         4 = lava        5 = tree/dense vegetation
  6 = road/path     7 = rubble      8 = pillar
  9 = chest        10 = stairs     11 = trap marker
 12 = grass        13 = sand/dirt  14 = snow/ice
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Room:
    x: int; y: int; w: int; h: int
    room_type: str = "generic"

    @property
    def cx(self): return self.x + self.w // 2
    @property
    def cy(self): return self.y + self.h // 2
    def intersects(self, other: "Room", pad=1) -> bool:
        return (self.x - pad < other.x + other.w and self.x + self.w + pad > other.x and
                self.y - pad < other.y + other.h and self.y + self.h + pad > other.y)


@dataclass
class MapResult:
    map_type: str
    subtype: str
    width: int
    height: int
    tiles: list[list[int]]
    rooms: list[dict] = field(default_factory=list)
    features: list[dict] = field(default_factory=list)
    legend: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "map_type": self.map_type,
            "subtype": self.subtype,
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "rooms": self.rooms,
            "features": self.features,
            "legend": self.legend,
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate(map_type: str, subtype: str | None, width: int = 80, height: int = 40, seed: int | None = None) -> MapResult:
    rng = random.Random(seed)
    if map_type == "dungeon":
        return _dungeon(subtype or "generic", width, height, rng)
    elif map_type == "outdoor":
        return _outdoor(subtype or "forest", width, height, rng)
    elif map_type == "interior":
        return _interior(subtype or "tavern", width, height, rng)
    elif map_type == "wildemount":
        return _wildemount(subtype or "xhorhas_wastes", width, height, rng)
    raise ValueError(f"Unknown map_type: {map_type}")


# ---------------------------------------------------------------------------
# Dungeon — BSP room placement
# ---------------------------------------------------------------------------

DUNGEON_ROOM_TYPES: dict[str, list[str]] = {
    "generic":      ["entrance", "corridor_room", "treasure", "monster_lair", "empty", "empty", "empty"],
    "cave":         ["natural_cave", "underground_lake", "crystal_chamber", "monster_den", "hot_spring"],
    "temple":       ["shrine", "ritual_chamber", "crypt", "offering_hall", "inner_sanctum"],
    "ruins_aeor":   ["arcane_lab", "time_anomaly_chamber", "frozen_corridor", "collapsed_vault", "beacon_room"],
    # Web-app subtypes
    "underdark":    ["cave_passage", "underground_lake", "mushroom_grove", "aboleth_pool", "bioluminescent"],
    "bazzoxan":     ["cave_passage", "underground_lake", "monster_den", "natural_cave", "crystal_chamber"],
    "crypt":        ["burial_chamber", "crypt", "ossuary", "ritual_chamber", "collapsed_vault"],
    "sewers":       ["sewer_junction", "overflow_chamber", "filtration_room", "access_tunnel", "rat_warren"],
    "cerberus_lab": ["arcane_lab", "beacon_room", "time_anomaly_chamber", "collapsed_vault", "ritual_chamber"],
}

def _dungeon(subtype: str, W: int, H: int, rng: random.Random) -> MapResult:
    grid = [[0] * W for _ in range(H)]
    rooms: list[Room] = []
    types = DUNGEON_ROOM_TYPES.get(subtype, DUNGEON_ROOM_TYPES["generic"])

    is_sewers = subtype == "sewers"
    attempts = 0
    while len(rooms) < 15 and attempts < 400:
        attempts += 1
        # Sewers use smaller, narrower rooms
        if is_sewers:
            w = rng.randint(3, 7); h = rng.randint(3, 5)
        else:
            w = rng.randint(4, 10); h = rng.randint(4, 8)
        x = rng.randint(1, W - w - 1)
        y = rng.randint(1, H - h - 1)
        room = Room(x, y, w, h, rng.choice(types))
        if any(room.intersects(r) for r in rooms):
            continue
        rooms.append(room)
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                grid[ry][rx] = 1

    # Connect rooms with corridors; place a door at the bend
    for i in range(1, len(rooms)):
        a, b = rooms[i - 1], rooms[i]
        _corridor(grid, a.cx, a.cy, b.cx, b.cy, rng)
        # Door at the corridor bend
        if rng.random() < 0.6:
            if rng.random() < 0.5:
                bx, by = b.cx, a.cy
            else:
                bx, by = a.cx, b.cy
            if 0 < by < H and 0 < bx < W and grid[by][bx] == 1:
                grid[by][bx] = 2

    # Add doors at room entrances
    for room in rooms:
        _add_doors(grid, room, rng)

    # Scatter features per room
    features: list[dict] = []
    for idx, room in enumerate(rooms):
        if idx == 0:
            # Entrance stairs
            grid[room.cy][room.cx] = 10
            features.append({"x": room.cx, "y": room.cy, "type": "stairs_up"})
        elif idx == len(rooms) - 1:
            # Boss room — chest
            grid[room.cy][room.cx] = 9
            features.append({"x": room.cx, "y": room.cy, "type": "chest"})
        else:
            feats = _room_features(room, rng, subtype, W, H, grid)
            features.extend(feats)
            for f in feats:
                if 0 <= f["y"] < H and 0 <= f["x"] < W:
                    grid[f["y"]][f["x"]] = f.get("tile", 9)

    legend = {
        "0": "Wall", "1": "Floor", "2": "Door", "7": "Rubble",
        "8": "Pillar", "9": "Chest", "10": "Stairs", "11": "Trap",
    }
    if subtype in ("underdark", "bazzoxan"):
        legend["3"] = "Underground Pool"
    if subtype == "sewers":
        legend["3"] = "Sewer Channel"
    if subtype == "cerberus_lab":
        legend["9"] = "Beacon / Artefact"

    return MapResult(
        map_type="dungeon", subtype=subtype, width=W, height=H, tiles=grid,
        rooms=[{"x": r.x, "y": r.y, "w": r.w, "h": r.h, "type": r.room_type} for r in rooms],
        features=features, legend=legend,
    )


def _corridor(grid, x1, y1, x2, y2, rng):
    if rng.random() < 0.5:
        _hline(grid, x1, x2, y1)
        _vline(grid, y1, y2, x2)
    else:
        _vline(grid, y1, y2, x1)
        _hline(grid, x1, x2, y2)


def _hline(grid, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = 1


def _vline(grid, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            grid[y][x] = 1


def _add_doors(grid, room: Room, rng: random.Random):
    H, W = len(grid), len(grid[0])
    candidates = []
    for rx in range(room.x, room.x + room.w):
        for ry in [room.y - 1, room.y + room.h]:
            if 0 < ry < H and grid[ry][rx] == 1:
                candidates.append((rx, ry))
    for ry in range(room.y, room.y + room.h):
        for rx in [room.x - 1, room.x + room.w]:
            if 0 < rx < W and grid[ry][rx] == 1:
                candidates.append((rx, ry))
    for dx, dy in rng.sample(candidates, min(2, len(candidates))):
        grid[dy][dx] = 2


def _room_features(room: Room, rng: random.Random, subtype: str, W: int, H: int, grid: list) -> list[dict]:
    features = []
    interior_xs = range(room.x + 1, room.x + room.w - 1)
    interior_ys = range(room.y + 1, room.y + room.h - 1)
    pts = [(x, y) for x in interior_xs for y in interior_ys]
    if not pts:
        return features

    rt = room.room_type

    # Treasure / chest
    if rt in ("treasure", "beacon_room", "collapsed_vault") and rng.random() < 0.8:
        x, y = rng.choice(pts)
        features.append({"x": x, "y": y, "type": "chest", "tile": 9})

    # Traps
    if rt in ("crypt", "monster_lair", "monster_den", "ossuary", "ritual_chamber") and rng.random() < 0.6:
        x, y = rng.choice(pts)
        features.append({"x": x, "y": y, "type": "trap", "tile": 11})

    # Pillars (temple, shrine, inner sanctum, arcane lab)
    if rt in ("shrine", "ritual_chamber", "inner_sanctum", "arcane_lab", "cerberus_lab", "time_anomaly_chamber"):
        for px, py in rng.sample(pts, min(4, len(pts))):
            features.append({"x": px, "y": py, "type": "pillar", "tile": 8})

    # Water pools — underdark / bazzoxan / sewers
    if subtype in ("underdark", "bazzoxan") and rng.random() < 0.5:
        for _ in range(2):
            fx = room.x + 1 + rng.randint(0, max(0, room.w - 3))
            fy = room.y + 1 + rng.randint(0, max(0, room.h - 3))
            if 0 <= fy < H and 0 <= fx < W and grid[fy][fx] == 1:
                features.append({"x": fx, "y": fy, "type": "pool", "tile": 3})

    if subtype == "sewers" and room.w > 4:
        # Water channel down the middle of the room
        for x in range(room.x + 1, room.x + room.w - 1):
            if 0 <= room.cy < H and 0 <= x < W and grid[room.cy][x] == 1:
                features.append({"x": x, "y": room.cy, "type": "sewer_channel", "tile": 3})

    # Crypt — rubble in corners
    if subtype == "crypt" and rng.random() < 0.5:
        if grid[room.y + 1][room.x + 1] == 1:
            features.append({"x": room.x + 1, "y": room.y + 1, "type": "rubble", "tile": 7})

    # Underground lake
    if rt == "underground_lake" and rng.random() < 0.9:
        features.append({"x": room.cx, "y": room.cy, "type": "water", "tile": 3})

    return features


# ---------------------------------------------------------------------------
# Outdoor — zone-based terrain
# ---------------------------------------------------------------------------

OUTDOOR_CONFIGS: dict[str, dict] = {
    "forest":       {"base": 12, "feature": 5,  "water": 3,  "road": True,  "density": 0.25},
    "plains":       {"base": 12, "feature": 12, "water": 3,  "road": True,  "density": 0.10},
    "tundra":       {"base": 14, "feature": 14, "water": 3,  "road": False, "density": 0.10},
    "badlands":     {"base": 13, "feature": 7,  "water": None,"road": False, "density": 0.10},
    "coastal":      {"base": 12, "feature": 5,  "water": 3,  "road": True,  "density": 0.12},
    "jungle":       {"base": 12, "feature": 5,  "water": 3,  "road": False, "density": 0.30},
    # Web-app additions
    "mountain":     {"base": 7,  "feature": 14, "water": 3,  "road": False, "density": 0.12},
    "wastes":       {"base": 13, "feature": 7,  "water": 4,  "road": False, "density": 0.08},
    "savalirwood":  {"base": 12, "feature": 5,  "water": 3,  "road": False, "density": 0.28},
}

def _outdoor(subtype: str, W: int, H: int, rng: random.Random) -> MapResult:
    cfg = OUTDOOR_CONFIGS.get(subtype, OUTDOOR_CONFIGS["forest"])
    grid = [[cfg["base"]] * W for _ in range(H)]

    # Scatter terrain features
    density = cfg["density"]
    for y in range(H):
        for x in range(W):
            if rng.random() < density:
                grid[y][x] = cfg["feature"]
    # Extra clusters
    for _ in range(20):
        cx = rng.randint(0, W - 1); cy = rng.randint(0, H - 1)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < H and 0 <= nx < W and rng.random() < 0.7:
                    grid[ny][nx] = cfg["feature"]

    # River / lava flow
    if cfg["water"] is not None:
        ry = 5 + rng.randint(0, H - 10)
        for x in range(W):
            ry = max(1, min(H - 2, ry + rng.randint(-1, 1)))
            grid[ry][x] = cfg["water"]
            if rng.random() < 0.4 and ry + 1 < H:
                grid[ry + 1][x] = cfg["water"]

    # Road
    if cfg["road"]:
        road_y = rng.randint(H // 3, 2 * H // 3)
        for x in range(W):
            grid[road_y][x] = 6
            road_y = max(1, min(H - 2, road_y + rng.randint(-1, 1)))

    # Scatter landmarks
    features = _scatter_outdoor_features(grid, W, H, subtype, rng)

    legend = {
        "3": "Water", "4": "Lava", "5": "Trees", "6": "Road",
        "7": "Rubble/Rocks", "12": "Grass", "13": "Dirt/Sand", "14": "Snow/Ice",
    }
    if subtype == "mountain":
        legend["7"] = "Rocky Outcrops"; legend["14"] = "Snow Caps"
    if subtype == "wastes":
        legend["4"] = "Lava Flow"; legend["13"] = "Blighted Soil"

    return MapResult(
        map_type="outdoor", subtype=subtype, width=W, height=H, tiles=grid,
        features=features, legend=legend,
    )


def _scatter_outdoor_features(grid, W, H, subtype, rng) -> list[dict]:
    features = []
    count = rng.randint(3, 7)
    for _ in range(count):
        x = rng.randint(2, W - 3); y = rng.randint(2, H - 3)
        if subtype in ("tundra", "badlands", "wastes", "mountain"):
            ftype = rng.choice(["ruins", "frozen_corpse", "strange_monolith", "campfire", "cave_entrance"])
        elif subtype == "savalirwood":
            ftype = rng.choice(["ancient_tree", "standing_stones", "ruins", "campfire", "fairy_ring"])
        else:
            ftype = rng.choice(["ruins", "campfire", "standing_stones", "ambush_point", "bridge", "cave_entrance"])
        features.append({"x": x, "y": y, "type": ftype, "tile": 7})
        grid[y][x] = 7
    return features


# ---------------------------------------------------------------------------
# Interior — template-based
# ---------------------------------------------------------------------------

def _interior(subtype: str, W: int, H: int, rng: random.Random) -> MapResult:
    grid = [[0] * W for _ in range(H)]

    TEMPLATES = {
        "tavern":  _template_tavern,
        "castle":  _template_castle,
        "ship":    _template_ship,
        "temple":  _template_temple,
        "mansion": _template_mansion,
    }
    builder = TEMPLATES.get(subtype, _template_tavern)
    rooms, features = builder(grid, W, H, rng)

    return MapResult(
        map_type="interior", subtype=subtype, width=W, height=H, tiles=grid,
        rooms=[{"x": r.x, "y": r.y, "w": r.w, "h": r.h, "type": r.room_type} for r in rooms],
        features=features,
        legend={"0": "Wall", "1": "Floor", "2": "Door", "8": "Pillar", "9": "Furniture/Object"},
    )


def _carve_room(grid, room: Room, tile=1):
    for y in range(room.y, room.y + room.h):
        for x in range(room.x, room.x + room.w):
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                grid[y][x] = tile


def _template_tavern(grid, W, H, rng):
    rooms, features = [], []
    hall = Room(2, 2, W - 4, H // 2, "common_room")
    rooms.append(hall); _carve_room(grid, hall)
    for bx in range(hall.x + 2, hall.x + hall.w - 2, 2):
        grid[hall.y + 2][bx] = 8
    for i in range(3):
        rw, rh = 8, 6
        rx = 2 + i * (rw + 1); ry = H // 2 + 1
        if rx + rw < W - 1:
            r = Room(rx, ry, rw, rh, f"guest_room_{i+1}")
            rooms.append(r); _carve_room(grid, r)
            grid[ry][rx + rw // 2] = 2
    cellar = Room(W - 14, H // 2 + 1, 12, H - H // 2 - 3, "cellar")
    rooms.append(cellar); _carve_room(grid, cellar)
    grid[cellar.y][cellar.cx] = 2
    grid[hall.y + hall.h - 1][hall.cx] = 2
    features.append({"x": hall.cx, "y": hall.y + 3, "type": "fireplace", "tile": 4})
    return rooms, features


def _template_castle(grid, W, H, rng):
    rooms, features = [], []
    for y in range(2, H - 2):
        for x in range(2, W - 2):
            grid[y][x] = 1
    for y in range(6, H - 6):
        for x in range(6, W - 6):
            grid[y][x] = 0
    rooms.append(Room(2, 2, W - 4, 4, "great_hall"))
    for tx, ty in [(2, 2), (W - 8, 2), (2, H - 8), (W - 8, H - 8)]:
        tr = Room(tx, ty, 6, 6, "tower")
        rooms.append(tr); _carve_room(grid, tr)
        grid[ty + 2][tx + 2] = 8; grid[ty + 2][tx + 3] = 8
    throne = Room(W // 2 - 5, 3, 10, 8, "throne_room")
    rooms.append(throne); _carve_room(grid, throne)
    grid[throne.y + throne.h - 1][throne.cx] = 2
    features.append({"x": throne.cx, "y": throne.y + 1, "type": "throne", "tile": 9})
    grid[H - 3][W // 2] = 2; grid[H - 3][W // 2 + 1] = 2
    return rooms, features


def _template_ship(grid, W, H, rng):
    rooms, features = [], []
    hw = min(W - 4, 20); sx = (W - hw) // 2
    for y in range(2, H - 2):
        taper = abs(y - H // 2) * hw // (H // 2 + 1)
        lx = sx + taper // 2; rx = sx + hw - taper // 2
        for x in range(lx, rx):
            grid[y][x] = 1
    mx = W // 2
    for y in range(3, H - 3):
        grid[y][mx] = 8
    for ry, rt in [(3, "captain_cabin"), (H - 7, "cargo_hold"), (H // 2 - 2, "crew_quarters")]:
        r = Room(sx + 2, ry, hw - 4, 4, rt)
        rooms.append(r)
        grid[ry + 2][sx + 4] = 2
    features.append({"x": sx + 2, "y": 3, "type": "helm", "tile": 9})
    return rooms, features


def _template_temple(grid, W, H, rng):
    rooms, features = [], []
    nave = Room(4, 4, W - 8, H - 8, "nave")
    rooms.append(nave); _carve_room(grid, nave)
    for px in range(nave.x + 2, nave.x + nave.w - 2, 3):
        grid[nave.y + 2][px] = 8
        grid[nave.y + nave.h - 3][px] = 8
    altar = Room(W // 2 - 5, 4, 10, 8, "altar_chamber")
    rooms.append(altar); _carve_room(grid, altar)
    grid[altar.y + altar.h - 1][altar.cx] = 2
    features.append({"x": altar.cx, "y": altar.y + 2, "type": "altar", "tile": 9})
    for sx, rt in [(4, "side_chapel_left"), (W - 12, "side_chapel_right")]:
        chapel = Room(sx, H // 2 - 4, 8, 8, rt)
        rooms.append(chapel); _carve_room(grid, chapel)
        grid[chapel.cy][chapel.x + chapel.w - 1] = 2
    grid[nave.y + nave.h - 1][nave.cx] = 2
    grid[nave.y + nave.h - 1][nave.cx + 1] = 2
    return rooms, features


def _template_mansion(grid, W, H, rng):
    rooms, features = [], []
    layout = [
        (2, 2, W // 2 - 2, H // 3, "entrance_hall"),
        (W // 2, 2, W // 2 - 2, H // 3, "dining_room"),
        (2, H // 3 + 1, W // 3 - 1, H // 3, "library"),
        (W // 3, H // 3 + 1, W // 3, H // 3, "study"),
        (2 * W // 3, H // 3 + 1, W // 3 - 2, H // 3, "kitchen"),
        (2, 2 * H // 3, W // 2 - 2, H // 3 - 2, "master_bedroom"),
        (W // 2, 2 * H // 3, W // 2 - 2, H // 3 - 2, "servants_quarters"),
    ]
    for rx, ry, rw, rh, rt in layout:
        r = Room(rx, ry, max(rw, 4), max(rh, 4), rt)
        rooms.append(r); _carve_room(grid, r)
        grid[r.cy][r.x + r.w - 1] = 2
    features.append({"x": rooms[0].cx, "y": rooms[0].cy, "type": "grand_staircase", "tile": 10})
    return rooms, features


# ---------------------------------------------------------------------------
# Wildemount-specific maps
# ---------------------------------------------------------------------------

WILDEMOUNT_SUBTYPES: dict[str, tuple[str, str]] = {
    "xhorhas_wastes":    ("outdoor",   "badlands"),
    "aeor_ruins":        ("dungeon",   "ruins_aeor"),
    "rosohna_streets":   ("interior",  "mansion"),
    "rosohna":           ("interior",  "mansion"),
    "dwendalian_keep":   ("interior",  "castle"),
    "menagerie_port":    ("outdoor",   "coastal"),
    "savalirwood":       ("outdoor",   "savalirwood"),
    "eiselcross_tundra": ("outdoor",   "tundra"),
    "eiselcross":        ("outdoor",   "tundra"),
    "kryn_temple":       ("interior",  "temple"),
    "cerberus_lab":      ("dungeon",   "cerberus_lab"),
    "cavern_bazzoxan":   ("dungeon",   "bazzoxan"),
    "bazzoxan":          ("dungeon",   "bazzoxan"),
    "underdark":         ("dungeon",   "underdark"),
}

def _wildemount(subtype: str, W: int, H: int, rng: random.Random) -> MapResult:
    base_type, base_sub = WILDEMOUNT_SUBTYPES.get(subtype, ("dungeon", "generic"))

    if base_type == "dungeon":
        result = _dungeon(base_sub, W, H, rng)
    elif base_type == "outdoor":
        result = _outdoor(base_sub, W, H, rng)
    else:
        result = _interior(base_sub, W, H, rng)

    result.map_type = "wildemount"
    result.subtype = subtype

    # Inject Wildemount-flavoured feature labels
    for feat in result.features:
        if feat.get("type") == "chest" and subtype == "aeor_ruins":
            feat["type"] = "luxon_beacon_fragment"
        elif feat.get("type") == "altar" and subtype == "kryn_temple":
            feat["type"] = "luxon_altar"
        elif feat.get("type") == "ruins" and subtype == "xhorhas_wastes":
            feat["type"] = rng.choice(["betrayer_god_shrine", "pre_calamity_ruin", "kryn_outpost_remnant"])
        elif feat.get("type") == "chest" and subtype == "cerberus_lab":
            feat["type"] = rng.choice(["dunamancy_crystal", "forbidden_research", "soul_anchor"])

    return result


# ---------------------------------------------------------------------------
# Available types (for slash command choices)
# ---------------------------------------------------------------------------

MAP_TYPES: dict[str, list[str]] = {
    "dungeon":    ["generic", "cave", "temple", "ruins_aeor", "underdark", "crypt", "sewers", "cerberus_lab", "bazzoxan"],
    "outdoor":    ["forest", "plains", "tundra", "badlands", "coastal", "jungle", "mountain", "wastes", "savalirwood"],
    "interior":   ["tavern", "castle", "ship", "temple", "mansion"],
    "wildemount": [
        "xhorhas_wastes", "aeor_ruins", "rosohna", "dwendalian_keep",
        "menagerie_port", "savalirwood", "eiselcross", "kryn_temple",
        "cerberus_lab", "bazzoxan",
    ],
}
