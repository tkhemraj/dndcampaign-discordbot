"""World events cog — atmospheric, faction, and social events.

In manual mode the DM fires events on demand.
In auto mode the bot generates and posts an event every N minutes,
giving the world a sense of motion while the DM focuses on narration.
"""
from __future__ import annotations
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from bot import config
from bot.guard import dm_only
from bot.generators import event_gen


_TYPE_CHOICES = [
    app_commands.Choice(name=t, value=t) for t in event_gen.EVENT_TYPE_CHOICES
]

_REGION_CHOICES = [
    app_commands.Choice(name=r, value=r) for r in [
        "Western Wynandir", "Eastern Wynandir", "Menagerie Coast",
        "Xhorhas", "Eiselcross", "Greying Wildlands",
    ]
]

# Per-guild background tasks
_event_tasks: dict[int, asyncio.Task] = {}


async def _event_loop(guild_id: int, bot: commands.Bot) -> None:
    """Background loop — fires world events on the configured interval."""
    try:
        while True:
            interval = config.get_key(guild_id, "event_interval") or 20
            await asyncio.sleep(interval * 60)

            if config.get_key(guild_id, "event_mode") != "auto":
                break

            guild = bot.get_guild(guild_id)
            if not guild:
                break

            dm_only_mode  = config.get_key(guild_id, "event_dm_only")
            if dm_only_mode:
                channel_id = config.get_key(guild_id, "dm_channel_id")
            else:
                channel_id = config.get_key(guild_id, "player_channel_id")

            if not channel_id:
                continue

            ch = guild.get_channel(int(channel_id))
            if not ch:
                continue

            cid   = config.get_key(guild_id, "active_campaign_id")
            event = event_gen.generate(cid)
            embed = event_gen.build_embed(event)
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

    except asyncio.CancelledError:
        pass


def _start_task(guild_id: int, bot: commands.Bot) -> None:
    _stop_task(guild_id)
    _event_tasks[guild_id] = asyncio.create_task(_event_loop(guild_id, bot))


def _stop_task(guild_id: int) -> None:
    task = _event_tasks.pop(guild_id, None)
    if task and not task.done():
        task.cancel()


class EventsCog(commands.Cog, name="Events"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Restart auto-event loops for any guild already in auto mode."""
        for guild in self.bot.guilds:
            if config.get_key(guild.id, "event_mode") == "auto":
                _start_task(guild.id, self.bot)

    event_group = app_commands.Group(name="event", description="World events and ambient occurrences")

    @event_group.command(name="fire", description="Trigger a world event now and post to the channel")
    @app_commands.describe(
        type="Event type (random if omitted)",
        region="Region flavour (random if omitted)",
    )
    @app_commands.choices(type=_TYPE_CHOICES, region=_REGION_CHOICES)
    @dm_only()
    async def event_fire(
        self,
        interaction: discord.Interaction,
        type: str = "",
        region: str = "",
    ):
        gid = interaction.guild.id

        dm_only_mode = config.get_key(gid, "event_dm_only")
        if dm_only_mode:
            channel_id = config.get_key(gid, "dm_channel_id")
        else:
            channel_id = config.get_key(gid, "player_channel_id")

        target = (
            interaction.guild.get_channel(int(channel_id))
            if channel_id else interaction.channel
        )

        cid   = config.get_key(gid, "active_campaign_id")
        event = event_gen.generate(cid, type or None, region or None)
        embed = event_gen.build_embed(event)
        await target.send(embed=embed)
        await interaction.response.send_message(
            f"Event posted to {target.mention}.", ephemeral=True
        )

    @event_group.command(name="preview", description="Preview a world event — DM eyes only")
    @app_commands.describe(
        type="Event type (random if omitted)",
        region="Region flavour (random if omitted)",
    )
    @app_commands.choices(type=_TYPE_CHOICES, region=_REGION_CHOICES)
    @dm_only()
    async def event_preview(
        self,
        interaction: discord.Interaction,
        type: str = "",
        region: str = "",
    ):
        cid   = config.get_key(interaction.guild.id, "active_campaign_id")
        event = event_gen.generate(cid, type or None, region or None)
        embed = event_gen.build_embed(event)
        embed.set_footer(text=f"PREVIEW (not posted) · {embed.footer.text}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @event_group.command(name="status", description="Show current world event settings")
    @dm_only()
    async def event_status(self, interaction: discord.Interaction):
        gid         = interaction.guild.id
        mode        = config.get_key(gid, "event_mode") or "manual"
        interval    = config.get_key(gid, "event_interval") or 20
        dm_only_flg = config.get_key(gid, "event_dm_only") or False
        running     = gid in _event_tasks and not _event_tasks[gid].done()

        embed = discord.Embed(title="World Event Settings", colour=0xD4A040)
        embed.add_field(name="Mode",     value=mode,                                  inline=True)
        embed.add_field(name="Interval", value=f"{interval} min",                     inline=True)
        embed.add_field(name="Target",   value="DM channel" if dm_only_flg else "Player channel", inline=True)
        embed.add_field(name="Loop",     value="✅ running" if running else "⬜ stopped", inline=True)
        embed.set_footer(text="Use /setup event_mode, /setup event_interval, /setup event_dm_only to configure")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
