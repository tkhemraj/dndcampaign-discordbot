"""Setup cog — DM role, channels, status."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot import config
from bot.guard import dm_only, is_dm


class SetupCog(commands.Cog, name="Setup"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    setup_group = app_commands.Group(name="setup", description="Configure the bot for this server")

    @setup_group.command(name="role", description="Set the DM role")
    @dm_only()
    async def setup_role(self, interaction: discord.Interaction, role: discord.Role):
        config.set_key(interaction.guild.id, "dm_role_id", role.id)
        await interaction.response.send_message(
            f"DM role set to **{role.name}**.", ephemeral=True
        )

    @setup_group.command(name="dm_channel", description="Set the channel where DM commands are allowed")
    @dm_only()
    async def setup_dm_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config.set_key(interaction.guild.id, "dm_channel_id", channel.id)
        await interaction.response.send_message(
            f"DM channel set to {channel.mention}.", ephemeral=True
        )

    @setup_group.command(name="player_channel", description="Set the channel where the bot posts player updates")
    @dm_only()
    async def setup_player_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config.set_key(interaction.guild.id, "player_channel_id", channel.id)
        await interaction.response.send_message(
            f"Player channel set to {channel.mention}.", ephemeral=True
        )

    @setup_group.command(name="voice_channel", description="Set the voice channel for combat turn announcements (TTS)")
    @dm_only()
    async def setup_voice_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        config.set_key(interaction.guild.id, "voice_channel_id", channel.id)
        await interaction.response.send_message(
            f"Voice channel set to **{channel.name}**. The bot will join it during combat and announce turns.", ephemeral=True
        )

    @setup_group.command(name="dm_mode", description="Set DM mode: auto (bot runs combat) or manual (DM controls)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="auto   — bot resolves monster turns, prompts players", value="auto"),
        app_commands.Choice(name="manual — DM controls all actions (default)",           value="manual"),
    ])
    @dm_only()
    async def setup_dm_mode(self, interaction: discord.Interaction, mode: str):
        config.set_key(interaction.guild.id, "dm_mode", mode)
        desc = (
            "Bot will auto-resolve monster attacks and prompt players for their turns."
            if mode == "auto" else
            "DM manually calls /combat next for every turn (default behaviour)."
        )
        await interaction.response.send_message(
            f"DM mode → **{mode}**. {desc}", ephemeral=True
        )

    @setup_group.command(name="player_mode", description="Set player mode: open (players interact) or managed (DM controls)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="open    — players use buttons and /combat done on their turn", value="open"),
        app_commands.Choice(name="managed — DM controls all actions including players (default)", value="managed"),
    ])
    @dm_only()
    async def setup_player_mode(self, interaction: discord.Interaction, mode: str):
        config.set_key(interaction.guild.id, "player_mode", mode)
        desc = (
            "Players will see action buttons (Attack / Cast Spell / Dodge / Pass) on their turn."
            if mode == "open" else
            "Players are observers; DM manages all character actions."
        )
        await interaction.response.send_message(
            f"Player mode → **{mode}**. {desc}", ephemeral=True
        )

    @setup_group.command(name="auto_timeout", description="Minutes before auto-advancing a stalled player turn (0 = disabled)")
    @dm_only()
    async def setup_auto_timeout(self, interaction: discord.Interaction, minutes: int):
        if minutes < 0:
            await interaction.response.send_message("Minutes must be ≥ 0.", ephemeral=True)
            return
        config.set_key(interaction.guild.id, "auto_turn_timeout", minutes)
        if minutes == 0:
            await interaction.response.send_message("Auto-timeout disabled — player turns wait indefinitely.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"Auto-timeout set to **{minutes} minute{'s' if minutes != 1 else ''}**.", ephemeral=True
            )

    @setup_group.command(name="status", description="Show current bot configuration")
    async def setup_status(self, interaction: discord.Interaction):
        cfg = config.get(interaction.guild.id)
        guild = interaction.guild

        def _role(rid):
            if not rid:
                return "_not set_"
            r = guild.get_role(int(rid))
            return r.mention if r else f"_unknown ({rid})_"

        def _chan(cid):
            if not cid:
                return "_not set_"
            c = guild.get_channel(int(cid))
            return c.mention if c else f"_unknown ({cid})_"

        def _vc(cid):
            if not cid:
                return "_not set_"
            c = guild.get_channel(int(cid))
            return f"🔊 {c.name}" if c else f"_unknown ({cid})_"

        embed = discord.Embed(title="Bot Configuration", colour=0xD4A040)
        embed.add_field(name="DM Role",        value=_role(cfg["dm_role_id"]),         inline=True)
        embed.add_field(name="DM Channel",     value=_chan(cfg["dm_channel_id"]),       inline=True)
        embed.add_field(name="Player Channel", value=_chan(cfg["player_channel_id"]),   inline=True)
        embed.add_field(name="Voice Channel",  value=_vc(cfg.get("voice_channel_id")), inline=True)

        dm_mode     = cfg.get("dm_mode", "manual")
        player_mode = cfg.get("player_mode", "managed")
        timeout_min = cfg.get("auto_turn_timeout", 5)
        timeout_str = f"{timeout_min}m" if timeout_min else "off"
        embed.add_field(name="DM Mode",     value=dm_mode,                          inline=True)
        embed.add_field(name="Player Mode", value=player_mode,                      inline=True)
        embed.add_field(name="Turn Timeout",value=timeout_str,                      inline=True)

        cid = cfg["active_campaign_id"]
        if cid:
            from bot import db
            row = db.fetchone("SELECT name FROM campaigns WHERE id=?", (cid,))
            cname = row["name"] if row else f"ID {cid} (not found)"
        else:
            cname = "_none selected_"
        embed.add_field(name="Active Campaign", value=cname, inline=False)
        embed.set_footer(text=f"You are: {'DM' if is_dm(interaction) else 'Player'}")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
