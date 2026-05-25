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


def _speak_template(npc: dict, question: str) -> str:
    """Zero-dependency fallback — constructs a reply from the NPC's own character data."""
    import random
    q = question.lower()
    faction   = npc.get("faction") or "no one"
    region    = npc.get("region") or "these lands"
    ideal     = npc.get("ideal", "")
    flaw      = npc.get("flaw", "")
    backstory = npc.get("backstory", "")

    # Use the first sentence of backstory as a hook
    back = backstory.split(".")[0].strip() if backstory else ""
    # Strip the ideal label ("Knowledge: X" → "X")
    ideal_body = ideal.split(":", 1)[1].strip() if ":" in ideal else ideal
    # Clean faction name for use in sentences
    faction_clean = faction.replace("Former ", "").replace("The ", "the ")

    faction_words = {"faction", "empire", "kryn", "dynasty", "assembly", "cobalt", "myriad", "revelry", "concord", "allegiance", "side", "serve", "loyal"}
    personal_words = {"who are you", "your name", "yourself", "past", "where are you from", "history", "background"}
    danger_words   = {"danger", "threat", "enemy", "fight", "war", "attack", "afraid", "risk"}
    trust_words    = {"trust", "secret", "tell me", "honest", "truth", "hiding", "know about", "information"}

    if any(w in q for w in personal_words):
        options = [
            f"{back}. That's enough for a stranger to know.",
            f"I've been in {region} long enough to stop explaining myself. My choices now are what matter.",
            f"{back}." if back else f"My past is mine. What I've chosen since is what matters.",
            f"What I was then and what I am now are different things. Ask about now.",
        ]
    elif any(w in q for w in faction_words):
        options = [
            f"I work with {faction_clean}. What you make of that is your business.",
            f"{faction_clean.capitalize()} is what I chose. I didn't choose it lightly.",
            f"Every argument against {faction_clean} — I've heard the good ones. I'm still here.",
            f"If you're asking because you want to judge me, that conversation costs more than a quick question.",
        ]
    elif any(w in q for w in danger_words):
        options = [
            f"I've survived {region}. I've survived things before that. Ask your real question.",
            f"I don't frighten easily. What specifically are you warning me about?",
            f"If you're threatening me, you're making a mistake. If you're warning me, I already know.",
            f"Danger is a condition, not an event. I'm used to the condition.",
        ]
    elif any(w in q for w in trust_words):
        options = [
            f"Trust is earned slowly and lost fast. We've just met. Do the math.",
            f"What I know isn't offered freely. What are you actually asking me for?",
            f"I'll tell you this much: {back.lower()}." if back else "There are things I keep to myself.",
            f"Honest? I'm as honest as the situation allows. Today it allows some.",
        ]
    else:
        options = [
            f"{ideal_body}" if ideal_body else f"I've been doing this long enough to have opinions. Ask a more specific question.",
            f"{back}." if back else f"I've been in {region} long enough to know how these conversations go.",
            f"I don't have a short answer to that. The long answer starts with: {back.lower()}." if back else f"That depends on what you're actually trying to find out.",
            f"I have my reasons for being here. They're mine.",
        ]

    options = [o for o in options if o.strip() and len(o) > 15]
    rng = random.Random(hash(question + npc.get("name", "")) & 0xFFFFFFFF)
    reply = rng.choice(options) if options else "I don't answer that. Not today."

    # Add flaw colouring on trust/personal questions, 40% of the time
    if flaw and any(w in q for w in trust_words | personal_words):
        flaw_first = flaw.split(".")[0].rstrip()
        if rng.random() < 0.4:
            reply = reply.rstrip(".") + f" — though {flaw_first.lower()}."

    return reply


def speak(npc: dict, question: str) -> str:
    """Return an in-character reply.

    Priority: ANTHROPIC_API_KEY → OPENAI_API_KEY → OLLAMA_MODEL → template fallback.
    Template fallback requires no API key and works on all 185 library NPCs.
    """
    system = _system_prompt(npc)

    if os.getenv("ANTHROPIC_API_KEY"):
        return _speak_anthropic(system, question)

    if os.getenv("OPENAI_API_KEY"):
        return _speak_openai_compat(system, question)

    if os.getenv("OLLAMA_MODEL") or os.getenv("OLLAMA_URL"):
        return _speak_ollama(system, question)

    return _speak_template(npc, question)
