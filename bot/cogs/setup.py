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

        embed = discord.Embed(title="Bot Configuration", colour=0xD4A040)
        embed.add_field(name="DM Role",        value=_role(cfg["dm_role_id"]),         inline=True)
        embed.add_field(name="DM Channel",     value=_chan(cfg["dm_channel_id"]),       inline=True)
        embed.add_field(name="Player Channel", value=_chan(cfg["player_channel_id"]),   inline=True)

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
