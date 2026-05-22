"""Generate Wildemount-flavoured quests and plot hooks."""
from __future__ import annotations
import random
from .data.wildemount import FACTIONS, REGIONS, PLOT_SEEDS

DIFFICULTIES = ["easy", "medium", "hard", "deadly"]
REWARDS = [
    "500 gp and a letter of passage through Empire checkpoints",
    "A Luxon beacon shard — faintly warm, whispers in an unknown language",
    "Access to a Cerberus Assembly restricted archive (one question answered)",
    "A title deed to a ruined keep on the edge of Xhorhas",
    "The Bright Queen's personal commendation — opens doors in Rosohna",
    "A masterwork dunamantic focus, attuned to time magic",
    "Three favours from a Myriad contact — no questions asked",
    "A ship and crew, docked in Nicodranas, no questions about the cargo",
    "The name of whoever placed a bounty on the party",
    "Freedom: the Assembly declares them 'assets terminated' and stops hunting them",
    "800 gp, two potions of healing, and a spell scroll of Detect Thoughts",
    "A safe house in Zadash, stocked, warded, and unknown to anyone official",
]

_TITLES = [
    "Shadows Over", "The Silence of", "Blood and Salt in", "The Last Beacon of",
    "What Remains in", "The Price of Order at", "A Debt Owed in", "The Weight of",
    "Dark Water Below", "Echoes From", "No Witnesses in", "The Reckoning of",
    "Before the Storm Breaks Over", "The Things Left Behind in", "Dust and Ash at",
]


def generate(campaign_id: int | None, region: str | None = None, faction: str | None = None, seed: int | None = None) -> dict:
    rng = random.Random(seed)

    if region is None:
        region = rng.choice(list(REGIONS.keys()))
    region_data = REGIONS[region]

    if faction is None:
        faction_data = rng.choice(FACTIONS)
        faction = faction_data["name"]
        hook = rng.choice(faction_data["hooks"])
    else:
        matched = next((f for f in FACTIONS if f["name"] == faction), None)
        hook = rng.choice(matched["hooks"]) if matched else rng.choice(PLOT_SEEDS)

    location = rng.choice(region_data["locations"])
    difficulty = rng.choice(DIFFICULTIES)

    return {
        "campaign_id": campaign_id,
        "title":       f"{rng.choice(_TITLES)} — {location}",
        "description": hook,
        "faction":     faction,
        "region":      region,
        "difficulty":  difficulty,
        "status":      "active",
        "reward":      rng.choice(REWARDS),
        "notes":       "",
    }
