"""AI-powered NPC dialogue via the Anthropic API."""
from __future__ import annotations
import os


def _client():
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=key)


def _system_prompt(npc: dict) -> str:
    name      = npc.get("name", "Unknown")
    race      = npc.get("race", "Human")
    cls       = npc.get("npc_class", "Commoner")
    level     = npc.get("level", 1)
    faction   = npc.get("faction") or "None"
    region    = npc.get("region") or "Wildemount"
    alignment = npc.get("alignment", "True Neutral")
    persona   = npc.get("personality", "")
    ideal     = npc.get("ideal", "")
    bond      = npc.get("bond", "")
    flaw      = npc.get("flaw", "")
    backstory = npc.get("backstory", "")

    return f"""You are roleplaying as {name}, a level {level} {race} {cls} in the world of Wildemount (Critical Role setting).

IDENTITY
- Faction: {faction}
- Region: {region}
- Alignment: {alignment}

CHARACTER
- Personality: {persona}
- Ideal: {ideal}
- Bond: {bond}
- Flaw: {flaw}

BACKSTORY
{backstory}

RULES
- Speak in first person, always in character. Never break the fourth wall.
- Keep responses to 2–4 sentences. You are not giving a speech; you are speaking to someone.
- Let your personality, ideal, bond, and flaw colour every response — especially under pressure.
- Refer to real Wildemount locations, factions, and figures when relevant.
- If the question touches your flaw or bond, let it show — hesitation, deflection, or emotion as appropriate.
- Never volunteer information you would not trust a stranger with."""


def speak(npc: dict, question: str) -> str:
    """Return an in-character reply from the NPC. Raises RuntimeError if API key is missing."""
    client = _client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_system_prompt(npc),
        messages=[{"role": "user", "content": question}],
    )
    return message.content[0].text.strip()
