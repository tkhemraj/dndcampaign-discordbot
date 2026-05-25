"""
Narrator — generates spoken flavour text for combat events and world events.

Template mode (default): rich, varied phrases — no API key required.
AI mode (auto-detected): uses Anthropic → OpenAI-compat → Ollama when keys
are present and NARRATOR_AI=1 is set.  Capped at 50 tokens for fast replies.
"""
from __future__ import annotations
import os
import random


# ── Template banks ─────────────────────────────────────────────────────────────

_ATTACK_HIT = [
    "{attacker} drives forward and lands a solid blow on {target}.",
    "The strike connects. {attacker} carves into {target}.",
    "{attacker} finds the opening and hammers {target}.",
    "Hit! {attacker}'s weapon tears through {target}'s guard.",
    "{attacker} slams into {target} — damage dealt.",
    "Steel bites steel. {attacker} connects hard with {target}.",
    "{attacker} presses the attack and strikes {target} true.",
    "The blow lands. {attacker} makes {target} feel it.",
]

_ATTACK_MISS = [
    "{target} sidesteps. {attacker}'s swing flies wide.",
    "Miss. {attacker} overextends and {target} slips away.",
    "{attacker}'s attack falls short — {target} holds ground.",
    "{target} pulls back just in time. {attacker} misses.",
    "The blow glances off. {attacker} fails to connect with {target}.",
    "{attacker} strikes air. {target} was never there.",
]

_ATTACK_CRIT = [
    "Critical hit! {attacker} finds a gap in {target}'s defenses — devastating!",
    "A natural twenty! {attacker} carves through {target} with terrifying force!",
    "Critical strike! {attacker} drives through {target}'s guard with brutal precision!",
    "The perfect hit! {attacker} delivers a crushing critical blow to {target}!",
    "Critical! {attacker} finds the weakness and tears {target} apart!",
]

_KO = [
    "{name} goes down!",
    "{name} drops to the ground!",
    "{name} falls!",
    "It's over for {name}.",
    "{name} is down and out of the fight.",
]

_TURN_MONSTER = [
    "{name} moves to attack.",
    "{name} bares its teeth and advances.",
    "Watch out — {name} is on the move.",
    "{name} presses the assault.",
    "{name}'s turn.",
    "{name} surges forward.",
]

_TURN_PLAYER = [
    "{name} — your turn. Round {round}.",
    "It's your move, {name}. Round {round}.",
    "{name}, what do you do? Round {round}.",
    "All eyes on {name}. Round {round}.",
    "{name}, round {round}.",
    "Move it, {name}. Round {round}.",
]

_COMBAT_START = [
    "Weapons ready. {encounter} begins — {first} strikes first.",
    "Steel drawn. {first} leads the charge in {encounter}.",
    "{encounter}. Combat begins — {first} goes first!",
    "Initiative set. {encounter} is under way — {first} moves first.",
]

_COMBAT_END = [
    "The battle is over. {rounds} rounds of combat.",
    "Combat ends. Victory after {rounds} hard-fought rounds.",
    "The dust settles after {rounds} rounds. The fight is done.",
    "It's over. {rounds} rounds of carnage.",
]

_COMBAT_END_WITH_FALLEN = [
    "The battle ends after {rounds} rounds. {fallen} won't be getting up.",
    "Combat over in {rounds} rounds. {fallen} fell in the fight.",
    "After {rounds} rounds, silence. {fallen} lies defeated.",
]


def _pick(bank: list[str], seed: str = "") -> str:
    rng = random.Random(hash(seed))
    return rng.choice(bank)


# ── AI narration ────────────────────────────────────────────────────────────────

_AI_SYSTEM = (
    "You are a dramatic narrator for a D&D 5e tabletop game. "
    "Reply with exactly one short, vivid sentence of spoken narration (under 20 words). "
    "No markdown, no quotes, no stage directions — just the narration itself."
)

_AI_ENABLED = os.getenv("NARRATOR_AI", "0") == "1"


def _ai_narrate(prompt: str) -> str | None:
    """Try AI narration. Returns None on any failure or if no key is configured."""
    if not _AI_ENABLED:
        return None
    import json
    import urllib.request

    def _post(url: str, payload: dict, headers: dict) -> dict:
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", **headers},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read())

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=60,
                system=_AI_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception:
            pass

    # OpenAI-compatible
    if os.getenv("OPENAI_API_KEY"):
        try:
            base  = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            result = _post(
                f"{base}/chat/completions",
                {"model": model, "max_tokens": 60,
                 "messages": [{"role": "system", "content": _AI_SYSTEM},
                               {"role": "user",   "content": prompt}]},
                {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            )
            return result["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # Ollama
    if os.getenv("OLLAMA_MODEL"):
        try:
            base  = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
            model = os.getenv("OLLAMA_MODEL", "llama3")
            result = _post(
                f"{base}/api/chat",
                {"model": model, "stream": False,
                 "messages": [{"role": "system", "content": _AI_SYSTEM},
                               {"role": "user",   "content": prompt}]},
                {},
            )
            return result["message"]["content"].strip()
        except Exception:
            pass

    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def narrate_attack(attacker: str, target: str, result: dict) -> str:
    """Return narration for one attack (hit/miss/crit)."""
    crit = result.get("crit", False)
    hit  = result.get("hit", False)
    dmg  = result.get("damage", 0)

    ai_prompt = (
        f"Event: {attacker} attacks {target}. "
        f"Result: {'CRITICAL HIT' if crit else 'hit' if hit else 'miss'}."
        + (f" Damage: {dmg}." if hit else "")
    )
    ai = _ai_narrate(ai_prompt)
    if ai:
        return ai

    if crit:
        return _pick(_ATTACK_CRIT, attacker + target).format(attacker=attacker, target=target)
    if hit:
        return _pick(_ATTACK_HIT, attacker + target).format(attacker=attacker, target=target)
    return _pick(_ATTACK_MISS, attacker + target).format(attacker=attacker, target=target)


def narrate_ko(name: str) -> str:
    """Announce a combatant going to 0 HP."""
    ai = _ai_narrate(f"Event: {name} drops to zero hit points and is knocked out.")
    if ai:
        return ai
    return _pick(_KO, name).format(name=name)


def narrate_turn(name: str, round_num: int, combatant_type: str = "monster") -> str:
    """Short turn announcement."""
    bank = _TURN_MONSTER if combatant_type == "monster" else _TURN_PLAYER
    ai_prompt = (
        f"Event: It is {name}'s turn to act. "
        f"They are a {'monster' if combatant_type == 'monster' else 'player character'}. "
        f"Round {round_num}."
    )
    ai = _ai_narrate(ai_prompt)
    if ai:
        return ai
    return _pick(bank, name + str(round_num)).format(name=name, round=round_num)


def narrate_combat_start(encounter_name: str, first_name: str) -> str:
    """Opening line when combat starts."""
    ai = _ai_narrate(
        f"Event: Combat begins. Encounter: {encounter_name}. {first_name} acts first."
    )
    if ai:
        return ai
    return _pick(_COMBAT_START, encounter_name).format(
        encounter=encounter_name, first=first_name
    )


def narrate_combat_end(rounds: int, fallen: list[str]) -> str:
    """Closing line when combat ends."""
    ai = _ai_narrate(
        f"Event: Combat ends after {rounds} rounds."
        + (f" Fallen: {', '.join(fallen)}." if fallen else "")
    )
    if ai:
        return ai
    if fallen:
        names = _and_join(fallen)
        return _pick(_COMBAT_END_WITH_FALLEN, str(rounds)).format(
            rounds=rounds, fallen=names
        )
    return _pick(_COMBAT_END, str(rounds)).format(rounds=rounds)


def narrate_event(event: dict) -> str:
    """Return a short spoken version of a world event."""
    desc = event.get("description", "") or event.get("desc", "")
    if not desc:
        return event.get("title", "A world event unfolds.") + "."
    # Take just the first sentence for speech
    first = desc.split(".")[0].strip()
    if not first:
        return desc[:100].strip() + "."
    return first + "."


def _and_join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]
