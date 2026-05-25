"""Combat resolution engine — dice math, attack resolution, PC stat helpers."""
from __future__ import annotations
import random
import re


def _parse_dice(expr: str) -> tuple[int, int, int]:
    """Parse 'NdM[+-K]' → (count, sides, modifier). Falls back to 1d4+0."""
    m = re.match(r"^(\d+)d(\d+)([+-]\d+)?$", expr.strip().replace(" ", ""))
    if not m:
        return (1, 4, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else 0)


def roll_dice(expr: str, rng: random.Random | None = None) -> tuple[list[int], int]:
    """Roll a dice expression. Returns (individual_rolls, total)."""
    r = rng or random
    if re.match(r"^\d+$", expr.strip()):
        v = int(expr.strip())
        return ([v], v)
    count, sides, mod = _parse_dice(expr)
    rolls = [r.randint(1, sides) for _ in range(max(1, count))]
    return (rolls, sum(rolls) + mod)


def roll_d20(
    modifier: int = 0,
    advantage: bool = False,
    disadvantage: bool = False,
    rng: random.Random | None = None,
) -> tuple[int, int, bool]:
    """Roll d20 with optional adv/dis. Returns (raw_roll, total, is_nat20)."""
    r = rng or random
    r1, r2 = r.randint(1, 20), r.randint(1, 20)
    raw = max(r1, r2) if advantage else (min(r1, r2) if disadvantage else r1)
    return (raw, raw + modifier, raw == 20)


def resolve_attack(atk_bonus: int, target_ac: int, damage_dice: str) -> dict:
    """Full attack resolution. Returns a result dict."""
    raw, total, is_crit = roll_d20(atk_bonus)
    hit = total >= target_ac or is_crit
    dmg_rolls: list[int] = []
    damage = 0
    if hit:
        rolls, base = roll_dice(damage_dice)
        if is_crit:
            rolls2, extra = roll_dice(damage_dice)
            rolls = rolls + rolls2
            base = base + extra
        dmg_rolls = rolls
        damage = max(1, base)
    return {
        "d20":         raw,
        "total":       total,
        "target_ac":   target_ac,
        "hit":         hit,
        "crit":        is_crit,
        "dmg_rolls":   dmg_rolls,
        "damage":      damage,
        "damage_dice": damage_dice,
        "atk_bonus":   atk_bonus,
    }


def calc_player_attack_bonus(pc: dict) -> int:
    """Derive attack bonus: proficiency + max(STR mod, DEX mod)."""
    level = pc.get("level", 1)
    prof  = 2 + (level - 1) // 4
    str_mod = (pc.get("str_score", 10) - 10) // 2
    dex_mod = (pc.get("dex_score", 10) - 10) // 2
    return prof + max(str_mod, dex_mod)


def calc_player_damage_dice(pc: dict) -> str:
    """Default weapon damage for a PC: 1d8 + max(STR mod, DEX mod)."""
    str_mod = (pc.get("str_score", 10) - 10) // 2
    dex_mod = (pc.get("dex_score", 10) - 10) // 2
    mod = max(str_mod, dex_mod)
    if mod > 0:
        return f"1d8+{mod}"
    if mod < 0:
        return f"1d8{mod}"
    return "1d8"


def roll_initiative(dex_score: int = 10) -> int:
    """Roll initiative: d20 + DEX modifier."""
    dex_mod = (dex_score - 10) // 2
    return random.randint(1, 20) + dex_mod
