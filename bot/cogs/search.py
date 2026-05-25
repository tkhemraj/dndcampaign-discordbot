"""Campaign search — full-text search across NPCs, quests, sessions, and characters."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import is_dm

_MAX     = 15   # total results cap
_SNIP    = 90   # snippet length


def _snippet(text: str | None, query: str) -> str:
    if not text:
        return ""
    text  = text.strip()
    q_low = query.lower()
    idx   = text.lower().find(q_low)
    if idx >= 0:
        start = max(0, idx - 20)
        end   = min(len(text), idx + len(query) + 60)
        snip  = text[start:end]
        if start > 0:   snip = "…" + snip
        if end < len(text): snip = snip + "…"
        return snip[:_SNIP]
    return text[:_SNIP]


def _search(cid: int | None, q: str, show_ids: bool) -> list[dict]:
    like = f"%{q}%"
    ql   = q.lower()
    out: list[dict] = []

    if not cid:
        return out

    # ── NPCs ────────────────────────────────────────────────────────────────
    for r in db.fetchall(
        """SELECT id, name, faction, region, personality, backstory, notes, status
           FROM npcs WHERE campaign_id=?
             AND (name LIKE ? OR faction LIKE ? OR region LIKE ?
                  OR personality LIKE ? OR backstory LIKE ? OR notes LIKE ?)
           ORDER BY id DESC LIMIT 6""",
        (cid, like, like, like, like, like, like),
    ):
        score = (2 if ql in (r["name"] or "").lower() else 0) + 1
        snip  = _snippet(
            r.get("personality") or r.get("backstory") or r.get("notes")
            or f"{r.get('faction','')} · {r.get('region','')}".strip(" ·"),
            q,
        )
        out.append(dict(score=score, emoji="🧙", type="NPC",
                        name=r["name"], id=r["id"],
                        meta=(r.get("status") or "alive").title(),
                        snippet=snip, show_id=show_ids))

    # ── Quests ──────────────────────────────────────────────────────────────
    for r in db.fetchall(
        """SELECT id, title, description, faction, reward, status
           FROM quests WHERE campaign_id=?
             AND (title LIKE ? OR description LIKE ? OR faction LIKE ? OR reward LIKE ?)
           ORDER BY id DESC LIMIT 5""",
        (cid, like, like, like, like),
    ):
        score = (2 if ql in (r["title"] or "").lower() else 0) + 1
        snip  = _snippet(r.get("description") or r.get("reward") or "", q)
        out.append(dict(score=score, emoji="📜", type="Quest",
                        name=r["title"], id=r["id"],
                        meta=(r.get("status") or "active").title(),
                        snippet=snip, show_id=show_ids))

    # ── Session logs ─────────────────────────────────────────────────────────
    for r in db.fetchall(
        """SELECT id, title, content FROM lore
           WHERE campaign_id=? AND lore_type='session'
             AND (title LIKE ? OR content LIKE ?)
           ORDER BY id DESC LIMIT 4""",
        (cid, like, like),
    ):
        score = (2 if ql in (r["title"] or "").lower() else 0) + 1
        snip  = _snippet(r.get("content") or "", q)
        out.append(dict(score=score, emoji="📖", type="Session",
                        name=r["title"], id=r["id"],
                        meta="Session Log",
                        snippet=snip, show_id=show_ids))

    # ── Player Characters ────────────────────────────────────────────────────
    for r in db.fetchall(
        """SELECT id, name, race, pc_class, level, notes
           FROM player_characters WHERE campaign_id=? AND status='active'
             AND (name LIKE ? OR race LIKE ? OR pc_class LIKE ? OR notes LIKE ?)
           ORDER BY id DESC LIMIT 4""",
        (cid, like, like, like, like),
    ):
        score = (2 if ql in (r["name"] or "").lower() else 0) + 1
        snip  = _snippet(
            r.get("notes")
            or f"Level {r.get('level',1)} {r.get('race','')} {r.get('pc_class','')}".strip(),
            q,
        )
        race  = r.get("race") or ""
        cls   = r.get("pc_class") or ""
        meta  = f"Lv{r.get('level',1)}" + (f" {cls}" if cls else "") + (f" · {race}" if race else "")
        out.append(dict(score=score, emoji="🧝", type="Character",
                        name=r["name"], id=r["id"],
                        meta=meta.strip(),
                        snippet=snip, show_id=False))

    out.sort(key=lambda x: -x["score"])
    return out[:_MAX]


class SearchCog(commands.Cog, name="Search"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="search",
        description="Search the campaign — NPCs, quests, session logs, characters",
    )
    async def search_cmd(self, interaction: discord.Interaction, query: str) -> None:
        if len(query.strip()) < 2:
            await interaction.response.send_message(
                "Query must be at least 2 characters.", ephemeral=True
            )
            return

        cid     = config.get_key(interaction.guild.id, "active_campaign_id")
        dm      = is_dm(interaction)
        results = _search(int(cid) if cid else None, query.strip(), dm)

        if not results:
            embed = discord.Embed(
                title=f"No results for \"{query}\"",
                description=(
                    "Nothing matched across NPCs, quests, session logs, or characters.\n"
                    "Try a shorter keyword, a character name, or a faction."
                ),
                colour=0x888888,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        types_found = list(dict.fromkeys(r["type"] for r in results))
        embed = discord.Embed(
            title=f"Search: {query}",
            colour=0xD4A040,
        )
        embed.set_footer(
            text=f"{len(results)} result{'s' if len(results) != 1 else ''} "
                 f"across {', '.join(types_found)}"
        )

        for r in results:
            label = f"{r['emoji']}  {r['name']}"
            if r["show_id"]:
                label += f"  ·  #{r['id']}"
            meta    = r["meta"] or ""
            snippet = r["snippet"] or ""
            value   = (f"*{meta}*" if meta else "") + ("\n" if meta and snippet else "") + snippet
            embed.add_field(name=label, value=value or "​", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SearchCog(bot))
