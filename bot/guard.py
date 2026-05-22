"""DM-only permission guard — role OR channel, either is sufficient."""
from __future__ import annotations
import discord
from discord import app_commands
from . import config


def is_dm(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False

    gid = interaction.guild.id
    dm_role_id = config.get_key(gid, "dm_role_id")
    dm_channel_id = config.get_key(gid, "dm_channel_id")

    if dm_role_id:
        if isinstance(interaction.user, discord.Member):
            if any(r.id == int(dm_role_id) for r in interaction.user.roles):
                return True

    if dm_channel_id:
        if interaction.channel_id == int(dm_channel_id):
            return True

    return False


def dm_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_dm(interaction):
            await interaction.response.send_message(
                "This command is restricted to the Dungeon Master.", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)
