"""DM-only permission guard — role OR channel, either is sufficient."""
from __future__ import annotations
import discord
from discord import app_commands
from . import config


def is_dm(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False

    gid = interaction.guild.id
    dm_role_id    = config.get_key(gid, "dm_role_id")
    dm_channel_id = config.get_key(gid, "dm_channel_id")

    # Nothing configured yet → fall back to server administrator so first-time
    # setup isn't a chicken-and-egg problem.
    if not dm_role_id and not dm_channel_id:
        if isinstance(interaction.user, discord.Member):
            p = interaction.user.guild_permissions
            return p.administrator or p.manage_guild
        return False

    if dm_role_id and isinstance(interaction.user, discord.Member):
        if any(r.id == int(dm_role_id) for r in interaction.user.roles):
            return True

    if dm_channel_id and interaction.channel_id == int(dm_channel_id):
        return True

    return False


def dm_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_dm(interaction):
            from bot import config as _cfg
            gid = interaction.guild.id if interaction.guild else None
            dm_role_id    = _cfg.get_key(gid, "dm_role_id") if gid else None
            dm_channel_id = _cfg.get_key(gid, "dm_channel_id") if gid else None
            if dm_role_id or dm_channel_id:
                hint = "Ask your server admin to give you the DM role, or run commands in the DM channel."
            else:
                hint = "Server admins can run `/quickstart` to configure the bot and grant DM access."
            await interaction.response.send_message(
                f"This command is for the Dungeon Master only. {hint}", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)
