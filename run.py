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


DnDBot().run(TOKEN)
