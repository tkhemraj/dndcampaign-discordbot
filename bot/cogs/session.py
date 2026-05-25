"""Session log cog — post recaps to the player channel and browse history."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import dm_only


class SessionCog(commands.Cog, name="Session"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    session_group = app_commands.Group(name="session", description="Session recaps")

    @session_group.command(name="log", description="Post a session recap to the player channel")
    @dm_only()
    async def session_log(
        self,
        interaction: discord.Interaction,
        title: str,
        notes: str,
    ) -> None:
        gid = interaction.guild.id
        cid = config.get_key(gid, "active_campaign_id")
        if not cid:
            await interaction.response.send_message(
                "No active campaign. Start one with `/campaign new [name]`, then `/campaign select` to activate it.",
                ephemeral=True,
            )
            return

        lid = db.execute(
            "INSERT INTO lore (campaign_id, title, content, lore_type) VALUES (?,?,?,'session')",
            (cid, title, notes),
        )

        embed = discord.Embed(
            title=f"📖  Session Recap — {title}",
            description=notes,
            colour=0x8866CC,
        )
        embed.set_footer(text=f"Session log #{lid} · searchable with /search")

        player_channel_id = config.get_key(gid, "player_channel_id")
        target = (
            interaction.guild.get_channel(int(player_channel_id))
            if player_channel_id else interaction.channel
        )
        if target:
            await target.send(embed=embed)

        await interaction.response.send_message(
            f"Session recap posted to {target.mention if target else 'channel'}.",
            ephemeral=True,
        )

    @session_group.command(name="history", description="Show recent session recaps")
    async def session_history(
        self,
        interaction: discord.Interaction,
        limit: int = 5,
    ) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign.", ephemeral=True)
            return

        rows = db.fetchall(
            """SELECT id, title, content, created_at FROM lore
               WHERE campaign_id=? AND lore_type='session'
               ORDER BY id DESC LIMIT ?""",
            (cid, min(max(limit, 1), 10)),
        )
        if not rows:
            await interaction.response.send_message(
                "No session recaps yet. Use `/session log <title> <notes>` to create one.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="Session History", colour=0x8866CC)
        for r in rows:
            content = r["content"] or ""
            preview = content[:120] + ("…" if len(content) > 120 else "")
            embed.add_field(
                name=f"[{r['id']}] {r['title']} · {r['created_at'][:10]}",
                value=preview or "​",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SessionCog(bot))
