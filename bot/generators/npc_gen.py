"""Procedural NPC generation with full Wildemount flavour."""
from __future__ import annotations
import random
from .data.wildemount import FACTIONS, REGIONS, RACES, NAMES, DEITIES

ALIGNMENTS = [
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil",
]

CLASSES = [
    "Fighter", "Rogue", "Wizard", "Cleric", "Ranger", "Paladin",
    "Bard", "Warlock", "Sorcerer", "Druid", "Monk", "Barbarian",
    "Artificer", "Echo Knight", "Chronurgist", "Graviturgist",
]

PERSONALITY_TRAITS = [
    "Never backs down from a challenge, even when they should.",
    "Deflects all serious conversation with dark humour.",
    "Fastidiously clean — cannot stand mess or disorder.",
    "Speaks in understatements even when the situation is dire.",
    "Mistrusts magic but relies on a magical item they won't explain.",
    "Names every weapon, horse, and piece of furniture they own.",
    "Quotes scripture or law at every opportunity.",
    "Has an unsettling habit of finishing other people's sentences correctly.",
    "Refuses to eat food they haven't prepared themselves.",
    "Deeply superstitious — throws salt over their shoulder, avoids specific numbers.",
    "Laughs too loudly and too often. Something is being suppressed.",
    "Speaks very quietly and expects everyone to lean in.",
]

IDEALS = [
    "Order: The rule of law is the only thing standing between civilisation and the abyss.",
    "Freedom: No one has the right to tell another how to live.",
    "Power: Those with strength should lead. Everyone else should follow.",
    "Knowledge: Every question has an answer. I intend to find all of them.",
    "Loyalty: The people I have chosen are my world. Everything else is negotiable.",
    "Survival: Ideals are for those who can afford them. I cannot.",
    "Redemption: I have done terrible things. I will spend my life trying to balance the scales.",
    "The Dynasty: The Luxon's light will eventually reach every corner of Wildemount.",
    "The Empire: Stability and order are worth any price. Even this one.",
    "Balance: Neither the Empire nor the Dynasty deserves to win. Someone has to make sure neither does.",
]

BONDS = [
    "A sibling conscripted into the Righteous Brand who hasn't written home in six months.",
    "Owes their life to a Kryn soldier who had every reason to let them die.",
    "Protecting a piece of information the Cerberus Assembly would kill to suppress.",
    "Searching for a mentor who vanished near the Ashkeeper Peaks.",
    "A child back in {location} who doesn't know this person is alive.",
    "Sworn a consecution oath to the Luxon and cannot explain why — they were raised in the Empire.",
    "Has a copy of an Assembly document that names them as an 'asset to be terminated'.",
    "The last survivor of a village destroyed in the war. Knows exactly who gave the order.",
]

FLAWS = [
    "Will not ask for help, even when dying.",
    "Harbours a secret sympathy for the enemy faction that would destroy their reputation.",
    "Addicted to a substance obtainable only in dangerous places.",
    "Cannot resist taking something valuable when they believe no one is watching.",
    "Deeply envious of anyone with magical talent they lack.",
    "Freezes completely when confronted by a specific type of creature.",
    "Lies reflexively, even when the truth would serve them better.",
    "Believes they are destined for greatness and makes reckless decisions to prove it.",
    "The massacre they participated in was following orders. They still follow orders.",
]

BACKSTORY_SEEDS = [
    "Survived the fall of {location} during an early Empire–Kryn skirmish. Everyone else died.",
    "Former Cerberus Assembly apprentice who witnessed something in a sealed tower and fled.",
    "A consecuted Kryn warrior in their third life — the other two lives belonged to an Imperial soldier.",
    "Grew up on the Menagerie Coast, fell into Myriad work out of desperation, never quite left.",
    "Cobalt Soul expositor who was 'retired' after their investigation got too close to an archmage.",
    "The only survivor of a Revelry raid on a merchant vessel. Swore revenge on the Plank King.",
    "A pallid elf who has never seen sunlight. Spent their life underground. The surface terrifies them.",
    "Raised in a Righteous Brand garrison on the front line. War is the only life they've ever known.",
    "Discovered a Luxon beacon fragment in a field and has been hearing echoes of someone else's memories ever since.",
    "Was the target of an Empire 'thinning' — a quiet purge of political dissidents. Faked their own death.",
]


def generate(campaign_id: int | None, region: str | None = None, faction: str | None = None, seed: int | None = None) -> dict:
    rng = random.Random(seed)

    race = rng.choice(RACES)
    npc_class = rng.choice(CLASSES)
    level = rng.choices(range(1, 21), weights=[10,8,7,6,5,5,4,4,3,3,2,2,2,2,1,1,1,1,1,1])[0]
    alignment = rng.choice(ALIGNMENTS)

    if region is None:
        region = rng.choice(list(REGIONS.keys()))
    region_data = REGIONS.get(region, REGIONS["Western Wynandir"])

    if faction is None:
        region_factions = {
            "Western Wynandir": ["Dwendalian Empire", "Cerberus Assembly", "Cobalt Soul", "The Myriad"],
            "Xhorhas":          ["Kryn Dynasty", "Cobalt Soul"],
            "Menagerie Coast":  ["The Clovis Concord", "The Revelry", "The Myriad"],
            "Greying Wildlands":["Cobalt Soul", "None"],
            "Eiselcross":       ["Cerberus Assembly", "None"],
        }
        faction = rng.choice(region_factions.get(region, ["None"]))

    culture = _region_to_culture(region, race)
    name_table = NAMES.get(culture, NAMES["Zemnian (Imperial)"])
    gender = rng.choice(["m", "f"])
    first = rng.choice(name_table["first_m"] if gender == "m" else name_table["first_f"])
    last = rng.choice(name_table["last"])
    name = f"{first} {last}"

    def roll_stat():
        rolls = [rng.randint(1, 6) for _ in range(4)]
        return sum(sorted(rolls)[1:])
    stats = {k: roll_stat() for k in ("str_score", "dex_score", "con_score", "int_score", "wis_score", "cha_score")}
    con_mod = (stats["con_score"] - 10) // 2
    hp = max(1, rng.randint(1, 10) + con_mod) * level
    ac = 10 + (stats["dex_score"] - 10) // 2 + rng.randint(0, 4)

    location = rng.choice(region_data["locations"])
    bond = rng.choice(BONDS).replace("{location}", location)

    return {
        "campaign_id":  campaign_id,
        "name":         name,
        "race":         race,
        "npc_class":    npc_class,
        "level":        level,
        "alignment":    alignment,
        "faction":      faction,
        "region":       region,
        "personality":  rng.choice(PERSONALITY_TRAITS),
        "ideal":        rng.choice(IDEALS),
        "bond":         bond,
        "flaw":         rng.choice(FLAWS),
        "backstory":    rng.choice(BACKSTORY_SEEDS).replace("{location}", location),
        "hp":           hp,
        "ac":           ac,
        **stats,
        "status":       "alive",
    }


def _region_to_culture(region: str, race: str) -> str:
    if "Drow" in race or "Kryn" in race:
        return "Xhorhasian (Kryn)"
    if region in ("Menagerie Coast",):
        return "Coastal (Menagerie)"
    if region in ("Xhorhas",):
        return "Xhorhasian (Kryn)"
    return "Zemnian (Imperial)"
