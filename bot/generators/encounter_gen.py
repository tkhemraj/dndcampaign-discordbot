"""Build balanced encounters from the monster roster."""
from __future__ import annotations
import random
from .data.monsters import MONSTERS, CR_TO_XP, DIFFICULTY_THRESHOLDS


def generate(
    campaign_id: int | None,
    party_size: int = 4,
    party_level: int = 5,
    difficulty: str = "medium",
    wildemount_only: bool = False,
    seed: int | None = None,
) -> dict:
    rng = random.Random(seed)

    threshold_level = min(party_level, max(DIFFICULTY_THRESHOLDS.keys(), key=lambda k: k if k <= party_level else -1))
    thresholds = DIFFICULTY_THRESHOLDS.get(threshold_level, DIFFICULTY_THRESHOLDS[5])
    diff_idx = {"easy": 0, "medium": 1, "hard": 2, "deadly": 3}.get(difficulty, 1)
    xp_budget = thresholds[diff_idx] * party_size

    pool = [m for m in MONSTERS if m["cr"] <= party_level + 2]
    if wildemount_only:
        pool = [m for m in pool if m.get("wildemount")]
    if not pool:
        pool = MONSTERS

    combatants = []
    spent = 0
    MULTI = [0, 1.0, 1.5, 2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 3.0, 3.0, 4.0]

    for _ in range(rng.randint(1, 8)):
        remaining = xp_budget - spent
        viable = [m for m in pool if CR_TO_XP.get(m["cr"], 0) <= remaining / max(1, MULTI[min(len(combatants), 11)])]
        if not viable:
            break
        monster = rng.choice(viable)
        hp_roll = max(1, monster["hp"] + rng.randint(-monster["hp"] // 4, monster["hp"] // 4))
        combatants.append({
            "name":           monster["name"],
            "combatant_type": "monster",
            "initiative":     0,
            "hp":             hp_roll,
            "max_hp":         hp_roll,
            "ac":             monster["ac"],
            "conditions":     "[]",
            "notes":          f"CR {monster['cr']} · ATK +{monster['atk']} · DMG {monster['dmg']}",
        })
        spent += CR_TO_XP.get(monster["cr"], 0)

    total_xp = sum(CR_TO_XP.get(
        next((m["cr"] for m in MONSTERS if m["name"] == c["name"]), 0), 0
    ) for c in combatants)

    type_counts: dict[str, int] = {}
    for c in combatants:
        m = next((x for x in MONSTERS if x["name"] == c["name"]), None)
        if m:
            type_counts[m["type"]] = type_counts.get(m["type"], 0) + 1
    dominant_type = max(type_counts, key=lambda t: type_counts[t]) if type_counts else "humanoid"

    return {
        "campaign_id":   campaign_id,
        "name":          f"{difficulty.title()} Encounter",
        "difficulty":    difficulty,
        "status":        "planned",
        "notes":         f"Est. {total_xp} XP for {party_size} level-{party_level} characters",
        "combatants":    combatants,
        "dominant_type": dominant_type,
        "party_level":   party_level,
        "party_size":    party_size,
        "total_xp":      total_xp,
    }
