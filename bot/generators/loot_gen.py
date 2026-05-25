"""CR-aware loot generator with Wildemount flavour."""
from __future__ import annotations
import random
from dataclasses import dataclass, field


# ── Item tables ───────────────────────────────────────────────────────────────

_MUNDANE: dict[str, list[tuple[str, int]]] = {
    "low": [
        ("Dwendalian copper trade token", 2),
        ("Cobalt Soul pamphlet (heavily annotated)", 5),
        ("Myriad coded correspondence", 10),
        ("Vial of dried Xhorhasian poison", 15),
        ("Kryn soldier's prayer bead", 5),
        ("Small obsidian idol of a Betrayer God", 20),
        ("Tattered Revelry map, coastline marked", 15),
        ("Iron lockbox (empty, scratched)", 5),
        ("Wildemount merchant's bill of sale", 8),
        ("Dented bronze flask with dried dunamite residue", 10),
    ],
    "mid": [
        ("Cerberus Assembly research journal", 75),
        ("Luxon devotional manuscript, illuminated", 60),
        ("Kryn Dynasty battle plans (outdated)", 50),
        ("Myriad ledger, three ciphered entries", 80),
        ("Silver holy symbol of the Moonweaver", 40),
        ("Cobalt Soul dossier on a sitting Assembly mage", 100),
        ("Jade figurine of a kryn warrior on horseback", 90),
        ("Sealed writ from a Dwendalian magistrate", 55),
        ("Navigator's charts of the Menagerie Coast", 70),
        ("Set of Volstrucker-issue signal mirrors", 45),
    ],
    "high": [
        ("Cerberus Assembly arcane contract, signed in blood", 400),
        ("Volstrucker operational ledger, names intact", 500),
        ("Beacon resonance diagram, partial", 600),
        ("Assembly mage's personal spellbook, 3 spells", 800),
        ("Platinum statue of Erathis — Cobalt Soul contraband", 700),
        ("Myriad syndicate membership token, active", 450),
        ("Aeorian relic: crystallised memory fragment", 600),
        ("Dwendalian noble's signet ring (House Trebain)", 350),
        ("Rolled Eiselcross survey, marked coordinates", 500),
        ("Chest of rare spices from the Menagerie Coast", 300),
    ],
    "epic": [
        ("Volstrucker kill order, counter-signed", 2000),
        ("Living Assembly contract — soul-binding clause", 3000),
        ("Intact Aeor pre-Calamity communication device", 2500),
        ("Personal correspondence between two Paragons", 1800),
        ("Uncut Luxon shard, resonance signature unknown", 4000),
        ("Aeorian golem control key", 2800),
        ("Sealed Cerberus Assembly dossier on the Bright Queen", 2200),
        ("Undying Mind research notes — complete", 3500),
    ],
}

_GEMS: dict[str, list[tuple[str, int]]] = {
    "low": [
        ("Chips of quartz", 5), ("Hematite bead", 10), ("Obsidian shard", 10),
        ("Malachite fragment", 15), ("Onyx chip", 25),
    ],
    "mid": [
        ("Onyx (polished)", 50), ("Bloodstone", 50), ("Carnelian", 75),
        ("Chrysoprase", 50), ("Zircon", 50), ("Beryl", 100),
    ],
    "high": [
        ("Alexandrite", 500), ("Aquamarine", 500), ("Tourmaline", 100),
        ("Spinel (red)", 100), ("Topaz", 500), ("Chrysoberyl", 300),
    ],
    "epic": [
        ("Sapphire", 1000), ("Ruby (flawless)", 5000), ("Emerald", 1000),
        ("Jacinth", 5000), ("Diamond", 5000), ("Dunamancy crystal (charged)", 3000),
    ],
}

_MAGIC: dict[str, list[str]] = {
    "common": [
        "Sending Stone (cracked — sends but rarely receives)",
        "Cloak of Billowing (Revelry-issue, smells of brine)",
        "Boots of False Tracks (leaves kryn soldier prints)",
        "Pot of Awakening (produces Xhorhasian darkwillow tea)",
        "Instrument of Illusions (lute, plays phantom accompaniment)",
        "Coin of Delving (Cobalt Soul-marked, glows near secrets)",
        "Clockwork Amulet (Assembly hallmark, slightly warm)",
        "Hat of Vermin (produces a single cave rat on command)",
        "Heward's Handy Spice Pouch (Menagerie Coast blend)",
        "Pipe of Smoke Monsters (shapes resemble Betrayer symbols)",
    ],
    "uncommon": [
        "Bag of Holding (stamped with a defunct Myriad seal)",
        "Dwendalian Dueling Blade +1 (Empire military issue)",
        "Cloak of Protection (Cobalt Soul expositor's cloak)",
        "Gauntlets of Ogre Power (Cerberus Assembly provenance)",
        "Helm of Telepathy (Aeor salvage, cracked lens)",
        "Goggles of Night (Kryn Dynasty field-issue)",
        "Ring of Mind Shielding (Volstrucker counter-intel tool)",
        "Brooch of Shielding (Dwendalian court fashion)",
        "Pearl of Power (resonates faintly with dunamancy)",
        "Wand of Magic Missiles (Assembly training-grade)",
        "Dust of Disappearance (Myriad smuggler's supply)",
        "Amulet of Proof Against Detection (Volstrucker-issue)",
        "Staff of the Python (Xhorhasian serpent-cult relic)",
        "Immovable Rod (Cobalt Soul archival stacking device)",
        "Circlet of Blasting (Cerberus Assembly experimental)",
    ],
    "rare": [
        "Beacon Fragment — grants 1/day Guidance as a free action",
        "Resonance Blade +2 (Kryn echo-forged, vibrates in anti-magic)",
        "Aeorian Memory Crystal (contains 3 levels of stored spells)",
        "Mantle of Spell Resistance (Volstrucker black-ops issue)",
        "Staff of Fire (Assembly Archmage confiscated item)",
        "Sword of Life Stealing +2 (Cerberus Assembly field prototype)",
        "Necklace of Prayer Beads (Luxon-inscribed, Kryn temple find)",
        "Robe of Eyes (Cobalt Soul Grand Curator's formal wear)",
        "Ring of Spell Storing (filled with two Assembly cantrips)",
        "Belt of Hill Giant Strength (Dwendalian military contract item)",
        "Figurine of Wondrous Power — Obsidian Steed (Betrayer relic)",
        "Wand of Paralysis (Cerberus Assembly interrogation tool)",
        "Cloak of Displacement (Myriad master operative's equipment)",
        "Helm of Brilliance (Aeor salvage, three sunstones intact)",
    ],
    "very_rare": [
        "Dunamancy Focus (potent) — 1/day cast Slow or Haste (3rd level free)",
        "Aeorian Resonance Armor +2 (shifts resistance on attunement)",
        "Volstrucker Mark Dagger +3 (casts Invisibility on hit, 1/day)",
        "Luxon Shard — Fragments of the Divine (advantage on death saves)",
        "Temporal Lasso (restrains target in time loop, 1/day)",
        "Staff of the Magi (Cerberus Assembly senior archmage's staff)",
        "Mantle of the Bright Queen (Kryn Dynasty regalia, resists radiant)",
        "Ring of Regeneration (Aeor bio-research artifact)",
        "Sword of Sharpness +3 (Dwendalian treasury blade, named 'Edgewright')",
        "Tome of Clear Thought (annotated by an Assembly scholar)",
    ],
    "legendary": [
        "Eye of the Luxon — 1/day cast Beacon of Hope (no concentration)",
        "Aeorian Resonance Engine (grants flight, 3 charges of Time Stop)",
        "Living Assembly Contract — binds a soul to the wielder's service",
        "Crown of Stars (Betrayer-forged, 7 motes; cast Fireball at will)",
        "Vorpal Sword (Dwendalian royal blade — 'The King's Apology')",
        "Robe of the Archmagi (Cerberus Assembly Annex recovered item)",
    ],
}

# ── CR → loot tier config ─────────────────────────────────────────────────────

def _tier(cr: int) -> str:
    if cr <= 3:  return "low"
    if cr <= 7:  return "mid"
    if cr <= 12: return "high"
    return "epic"


def _gold_roll(cr: int, rng: random.Random) -> int:
    if cr == 0:
        return rng.randint(1, 6) * 2
    if cr <= 3:
        return rng.randint(2, 12) * 5
    if cr <= 7:
        return rng.randint(2, 12) * 20
    if cr <= 12:
        return rng.randint(3, 18) * 50
    if cr <= 17:
        return rng.randint(4, 24) * 200
    return rng.randint(4, 24) * 500


@dataclass
class LootResult:
    cr: int
    gold: int
    gems: list[tuple[str, int]]      # (name, gp_value)
    mundane: list[tuple[str, int]]   # (name, gp_value)
    magic: list[tuple[str, str]]     # (rarity, name)

    @property
    def total_value(self) -> int:
        return (self.gold
                + sum(v for _, v in self.gems)
                + sum(v for _, v in self.mundane))

    def items_for_db(self) -> list[str]:
        out = []
        for rarity, name in self.magic:
            out.append(f"[{rarity.replace('_', ' ').title()}] {name}")
        for name, val in self.gems:
            out.append(f"{name} ({val} gp)")
        for name, val in self.mundane:
            out.append(f"{name} ({val} gp)")
        return out


def generate(cr: int = 1, rng: random.Random | None = None) -> LootResult:
    rng = rng or random.SystemRandom()
    cr = max(0, cr)
    tier = _tier(cr)
    gold = _gold_roll(cr, rng)

    # Gems
    gems: list[tuple[str, int]] = []
    gem_pool = _GEMS[tier]
    n_gems = rng.choices([0, 1, 2, 3], weights=[35, 35, 20, 10])[0]
    for _ in range(n_gems):
        gems.append(rng.choice(gem_pool))

    # Mundane valuables
    mundane: list[tuple[str, int]] = []
    n_mundane = rng.choices([0, 1, 2], weights=[40, 45, 15])[0]
    for _ in range(n_mundane):
        mundane.append(rng.choice(_MUNDANE[tier]))

    # Magic items
    magic: list[tuple[str, str]] = []
    if cr == 0:
        pass  # no magic for trivial encounters
    elif cr <= 3:
        if rng.random() < 0.35:
            magic.append(("common", rng.choice(_MAGIC["common"])))
    elif cr <= 7:
        if rng.random() < 0.70:
            magic.append(("common", rng.choice(_MAGIC["common"])))
        if rng.random() < 0.35:
            magic.append(("uncommon", rng.choice(_MAGIC["uncommon"])))
    elif cr <= 12:
        magic.append(("uncommon", rng.choice(_MAGIC["uncommon"])))
        if rng.random() < 0.55:
            magic.append(("rare", rng.choice(_MAGIC["rare"])))
    elif cr <= 17:
        magic.append(("rare", rng.choice(_MAGIC["rare"])))
        if rng.random() < 0.45:
            magic.append(("very_rare", rng.choice(_MAGIC["very_rare"])))
    else:
        magic.append(("very_rare", rng.choice(_MAGIC["very_rare"])))
        if rng.random() < 0.50:
            magic.append(("legendary", rng.choice(_MAGIC["legendary"])))

    return LootResult(cr=cr, gold=gold, gems=gems, mundane=mundane, magic=magic)
