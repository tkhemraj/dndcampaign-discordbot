"""Entry point — python run.py"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your .env file. See .env.example.")

from bot import db as _db
_db.init()

COGS = [
    "bot.cogs.setup",
    "bot.cogs.campaign",
    "bot.cogs.generate",
    "bot.cogs.maps",
    "bot.cogs.combat",
    "bot.cogs.dice",
    "bot.cogs.loot",
    "bot.cogs.pc",
    "bot.cogs.events",
    "bot.cogs.help",
]

intents = discord.Intents.default()

class DnDBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        for cog in COGS:
            await self.load_extension(cog)
        await self.tree.sync()
        print(f"Synced slash commands ({len(COGS)} cogs)")

    async def on_ready(self):
        db_mode = "shared (dndcampaign.db)" if os.getenv("USE_SHARED_DB") == "1" else "standalone"
        print(f"Logged in as {self.user}  |  {len(self.guilds)} guild(s)  |  DB: {db_mode}")
        await self.change_presence(activity=discord.Game(name="D&D · /campaign info"))
        await self._announce_startup(db_mode)

    async def _announce_startup(self, db_mode: str):
        from bot import config as _cfg
        sha     = os.getenv("RAILWAY_GIT_COMMIT_SHA", "")
        msg     = os.getenv("RAILWAY_GIT_COMMIT_MESSAGE", "")
        branch  = os.getenv("RAILWAY_GIT_BRANCH", "master")
        short   = sha[:7] if sha else "local"

        embed = discord.Embed(
            title="✅  CampaignBot is online",
            colour=0x44AA44,
        )
        embed.add_field(name="Version", value=f"`{short}` on `{branch}`", inline=True)
        embed.add_field(name="DB",      value=db_mode.split()[0].title(),  inline=True)
        if msg:
            first_line = msg.strip().splitlines()[0][:100]
            embed.add_field(name="Deployed", value=first_line, inline=False)
        embed.set_footer(text=f"{len(self.guilds)} guild(s) · slash commands synced")

        for guild in self.guilds:
            pcid = _cfg.get_key(guild.id, "player_channel_id")
            if not pcid:
                continue
            ch = guild.get_channel(int(pcid))
            if ch:
                try:
                    await ch.send(embed=embed)
                except Exception:
                    pass


DnDBot().run(TOKEN)
