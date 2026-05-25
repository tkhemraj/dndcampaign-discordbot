"""Loot generator — /loot generate, share, list."""
from __future__ import annotations
import json
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import dm_only
from bot.generators import loot_gen

_RARITY_COLOURS = {
    "common":    0xAAAAAA,
    "uncommon":  0x1EFF00,
    "rare":      0x0070DD,
    "very_rare": 0xA335EE,
    "legendary": 0xFF8000,
}

_RARITY_ICONS = {
    "common":    "⬜",
    "uncommon":  "🟩",
    "rare":      "🟦",
    "very_rare": "🟪",
    "legendary": "🟧",
}


def _loot_embed(loot: loot_gen.LootResult, row_id: int | None = None,
                claimed: list[str] | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"💰 Loot — CR {loot.cr}",
        colour=0xD4A040,
    )

    # Gold
    embed.add_field(name="Gold", value=f"**{loot.gold:,} gp**", inline=True)
    embed.add_field(name="Est. Total Value",
                    value=f"~{loot.total_value:,} gp", inline=True)

    # Gems
    if loot.gems:
        gem_lines = "\n".join(f"• {name} *(+{val} gp)*" for name, val in loot.gems)
        embed.add_field(name="Gems & Valuables", value=gem_lines, inline=False)

    # Mundane items
    if loot.mundane:
        mundane_lines = "\n".join(f"• {name} *(+{val} gp)*" for name, val in loot.mundane)
        embed.add_field(name="Items of Interest", value=mundane_lines, inline=False)

    # Magic items
    if loot.magic:
        magic_lines = []
        for rarity, name in loot.magic:
            icon = _RARITY_ICONS.get(rarity, "•")
            label = rarity.replace("_", " ").title()
            magic_lines.append(f"{icon} **{label}:** {name}")
        embed.add_field(name="Magic Items", value="\n".join(magic_lines), inline=False)

    # Claimed
    if claimed:
        embed.add_field(
            name="Claimed",
            value="\n".join(f"✅ {c}" for c in claimed),
            inline=False,
        )

    if row_id:
        embed.set_footer(text=f"Loot ID {row_id} · /loot share {row_id} to post to players")
    return embed


def _shared_embed(loot: loot_gen.LootResult, claimed: list[str]) -> discord.Embed:
    """Public-facing embed posted to the player channel."""
    embed = discord.Embed(
        title="💰 Loot Found!",
        colour=0xD4A040,
    )
    embed.add_field(name="Gold", value=f"**{loot.gold:,} gp**", inline=True)

    if loot.gems:
        gem_lines = "\n".join(f"• {name} *(+{val} gp)*" for name, val in loot.gems)
        embed.add_field(name="Gems & Valuables", value=gem_lines, inline=False)

    if loot.mundane:
        mundane_lines = "\n".join(f"• {name}" for name, _ in loot.mundane)
        embed.add_field(name="Items of Interest", value=mundane_lines, inline=False)

    if loot.magic:
        magic_lines = []
        for rarity, name in loot.magic:
            icon = _RARITY_ICONS.get(rarity, "•")
            label = rarity.replace("_", " ").title()
            magic_lines.append(f"{icon} **{label}:** {name}")
        embed.add_field(name="✨ Magic Items", value="\n".join(magic_lines), inline=False)

    if claimed:
        embed.add_field(
            name="Claimed",
            value="\n".join(f"✅ {c}" for c in claimed),
            inline=False,
        )

    return embed


def _row_to_loot(row: dict) -> loot_gen.LootResult:
    items_raw = json.loads(row["items"])
    magic, gems, mundane = [], [], []
    for s in items_raw:
        if s.startswith("["):
            bracket_end = s.index("]")
            rarity_label = s[1:bracket_end].lower().replace(" ", "_")
            name = s[bracket_end + 2:]
            magic.append((rarity_label, name))
        elif " gp)" in s and "•" not in s:
            # gems or mundane — split on last " ("
            try:
                name, rest = s.rsplit(" (", 1)
                val = int(rest.rstrip(" gp)").replace(",", ""))
                # heuristic: short names are gems
                if len(name) < 30:
                    gems.append((name, val))
                else:
                    mundane.append((name, val))
            except Exception:
                mundane.append((s, 0))
    return loot_gen.LootResult(
        cr=row["cr"], gold=row["gold"],
        gems=gems, mundane=mundane, magic=magic,
    )


class LootCog(commands.Cog, name="Loot"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    loot_group = app_commands.Group(name="loot", description="Loot tools")

    @loot_group.command(name="generate", description="Generate loot for a defeated encounter")
    @app_commands.describe(cr="Challenge Rating of the defeated enemy/encounter")
    @dm_only()
    async def loot_generate(self, interaction: discord.Interaction, cr: int = 1) -> None:
        if not (0 <= cr <= 30):
            await interaction.response.send_message(
                "CR must be 0–30.", ephemeral=True)
            return

        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        result = loot_gen.generate(cr)

        row_id = db.execute(
            "INSERT INTO loot (campaign_id, cr, gold, items) VALUES (?,?,?,?)",
            (cid, cr, result.gold, json.dumps(result.items_for_db())),
        )

        embed = _loot_embed(result, row_id, claimed=[])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @loot_group.command(name="share", description="Post a loot card to the player channel")
    @app_commands.describe(loot_id="ID from /loot generate (shown in the footer)")
    @dm_only()
    async def loot_share(self, interaction: discord.Interaction, loot_id: int) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        row = db.fetchone(
            "SELECT * FROM loot WHERE id=? AND campaign_id=?", (loot_id, cid))
        if not row:
            await interaction.response.send_message(
                f"No loot with ID {loot_id} in this campaign.", ephemeral=True)
            return

        loot = _row_to_loot(row)
        claimed = json.loads(row["claimed"] or "[]")
        embed = _shared_embed(loot, claimed)

        pcid = config.get_key(interaction.guild.id, "player_channel_id")
        if pcid:
            ch = interaction.guild.get_channel(int(pcid))
            if ch:
                await ch.send(embed=embed)
                db.execute("UPDATE loot SET shared=1 WHERE id=?", (loot_id,))
                await interaction.response.send_message(
                    f"Loot posted to {ch.mention}.", ephemeral=True)
                return

        # Fallback: post here
        await interaction.response.send_message(embed=embed)
        db.execute("UPDATE loot SET shared=1 WHERE id=?", (loot_id,))

    @loot_group.command(name="list", description="List recent loot cards for this campaign")
    @dm_only()
    async def loot_list(self, interaction: discord.Interaction) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        rows = db.fetchall(
            "SELECT * FROM loot WHERE campaign_id=? ORDER BY created_at DESC LIMIT 10",
            (cid,),
        )
        if not rows:
            await interaction.response.send_message(
                "No loot generated yet.", ephemeral=True)
            return

        embed = discord.Embed(title="Recent Loot", colour=0xD4A040)
        for row in rows:
            items = json.loads(row["items"] or "[]")
            shared_tag = " · shared" if row["shared"] else ""
            magic_count = sum(1 for i in items if i.startswith("["))
            summary = f"**{row['gold']:,} gp**"
            if magic_count:
                summary += f" + {magic_count} magic item{'s' if magic_count > 1 else ''}"
            embed.add_field(
                name=f"ID {row['id']} — CR {row['cr']}{shared_tag}",
                value=summary,
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LootCog(bot))
