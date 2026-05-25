"""Dice expression parser and roller."""
from __future__ import annotations
import random
import re
from dataclasses import dataclass


@dataclass
class RollResult:
    expression: str
    rolls: list[int]    # all dice rolled (before keep/drop)
    kept: list[int]     # dice that count toward total
    modifier: int
    total: int
    die_sides: int
    label: str          # e.g. "4d6 keep highest 3"

    @property
    def is_crit(self) -> bool:
        return self.die_sides == 20 and len(self.kept) == 1 and self.kept[0] == 20

    @property
    def is_fumble(self) -> bool:
        return self.die_sides == 20 and len(self.kept) == 1 and self.kept[0] == 1


def roll(expression: str, rng: random.Random | None = None) -> RollResult:
    rng = rng or random.SystemRandom()
    raw = expression.strip().lower()

    adv = bool(re.search(r'\b(adv(antage)?)\s*$', raw))
    dis = bool(re.search(r'\b(dis(advantage)?)\s*$', raw))
    if adv or dis:
        raw = re.sub(r'\s*(adv(antage)?|dis(advantage)?)\s*$', '', raw)

    m = re.match(r'^(\d+)d(\d+)(?:(kh|kl)(\d+))?([+-]\d+)?$', raw.replace(' ', ''))
    if not m:
        raise ValueError(f"Can't parse \"{expression}\". Try: 1d20+5 · 4d6kh3 · 2d6 · 1d20 adv")

    count     = int(m.group(1))
    sides     = int(m.group(2))
    keep_mode = m.group(3)
    keep_n    = int(m.group(4)) if m.group(4) else None
    modifier  = int(m.group(5)) if m.group(5) else 0

    if adv:
        count, keep_mode, keep_n = 2, "kh", 1
    elif dis:
        count, keep_mode, keep_n = 2, "kl", 1

    if not (1 <= count <= 100):
        raise ValueError("Dice count must be 1–100.")
    if not (2 <= sides <= 1000):
        raise ValueError("Die sides must be 2–1000.")
    if keep_n and not (1 <= keep_n <= count):
        raise ValueError(f"Keep count must be between 1 and {count}.")

    rolls = [rng.randint(1, sides) for _ in range(count)]

    if keep_mode == "kh" and keep_n:
        kept = sorted(rolls, reverse=True)[:keep_n]
    elif keep_mode == "kl" and keep_n:
        kept = sorted(rolls)[:keep_n]
    else:
        kept = rolls[:]

    total = sum(kept) + modifier

    base = f"{count}d{sides}"
    if adv:
        label = "2d20 advantage"
    elif dis:
        label = "2d20 disadvantage"
    elif keep_mode and keep_n:
        word = "highest" if keep_mode == "kh" else "lowest"
        label = f"{base} keep {word} {keep_n}"
    else:
        label = base
    if modifier:
        label += f" {'+' if modifier > 0 else ''}{modifier}"

    return RollResult(
        expression=expression,
        rolls=rolls,
        kept=kept,
        modifier=modifier,
        total=total,
        die_sides=sides,
        label=label,
    )
