"""AI-powered NPC dialogue — supports Anthropic, OpenAI-compatible, and Ollama."""
from __future__ import annotations
import json
import os
import urllib.request


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
- Keep responses to 2–4 sentences. You are speaking to someone, not giving a speech.
- Let your personality, ideal, bond, and flaw colour every response — especially under pressure.
- Refer to real Wildemount locations, factions, and figures when relevant.
- If the question touches your flaw or bond, let it show — hesitation, deflection, or emotion.
- Never volunteer information you would not trust a stranger with."""


def _speak_anthropic(system: str, question: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return msg.content[0].text.strip()


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _speak_openai_compat(system: str, question: str) -> str:
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    key = os.environ["OPENAI_API_KEY"]
    payload = {
        "model": model,
        "max_tokens": 300,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
    }
    result = _post_json(f"{base}/chat/completions", payload, {"Authorization": f"Bearer {key}"})
    return result["choices"][0]["message"]["content"].strip()


def _speak_ollama(system: str, question: str) -> str:
    base = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": question},
        ],
    }
    result = _post_json(f"{base}/api/chat", payload, {})
    return result["message"]["content"].strip()


def speak(npc: dict, question: str) -> str:
    """Return an in-character reply. Auto-selects backend from env vars.

    Priority: ANTHROPIC_API_KEY → OPENAI_API_KEY → OLLAMA_MODEL/OLLAMA_URL
    """
    system = _system_prompt(npc)

    if os.getenv("ANTHROPIC_API_KEY"):
        return _speak_anthropic(system, question)

    if os.getenv("OPENAI_API_KEY"):
        return _speak_openai_compat(system, question)

    if os.getenv("OLLAMA_MODEL") or os.getenv("OLLAMA_URL"):
        return _speak_ollama(system, question)

    raise RuntimeError(
        "No AI backend configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or OLLAMA_MODEL in your .env."
    )
