"""Maps cog — generate, preview, share to player channel."""
from __future__ import annotations
import json
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db, renderer
from bot.guard import dm_only
from bot.generators import map_gen

# Choices surfaced to Discord's autocomplete
_TYPE_CHOICES = [
    app_commands.Choice(name="Dungeon",    value="dungeon"),
    app_commands.Choice(name="Outdoor",    value="outdoor"),
    app_commands.Choice(name="Interior",   value="interior"),
    app_commands.Choice(name="Wildemount", value="wildemount"),
]

_SUBTYPE_CHOICES = [
    # dungeon
    app_commands.Choice(name="Generic",           value="generic"),
    app_commands.Choice(name="Cave",              value="cave"),
    app_commands.Choice(name="Temple",            value="temple"),
    app_commands.Choice(name="Ruins of Aeor",     value="ruins_aeor"),
    app_commands.Choice(name="Underdark",         value="underdark"),
    app_commands.Choice(name="Crypt",             value="crypt"),
    app_commands.Choice(name="Sewers",            value="sewers"),
    app_commands.Choice(name="Cerberus Lab",      value="cerberus_lab"),
    app_commands.Choice(name="Bazzoxan Caverns",  value="bazzoxan"),
    # outdoor
    app_commands.Choice(name="Forest",            value="forest"),
    app_commands.Choice(name="Plains",            value="plains"),
    app_commands.Choice(name="Tundra",            value="tundra"),
    app_commands.Choice(name="Badlands",          value="badlands"),
    app_commands.Choice(name="Coastal",           value="coastal"),
    app_commands.Choice(name="Jungle",            value="jungle"),
    app_commands.Choice(name="Mountain",          value="mountain"),
    app_commands.Choice(name="Wastes",            value="wastes"),
    app_commands.Choice(name="Savalirwood",       value="savalirwood"),
    # interior
    app_commands.Choice(name="Tavern",            value="tavern"),
    app_commands.Choice(name="Castle",            value="castle"),
    app_commands.Choice(name="Ship",              value="ship"),
    app_commands.Choice(name="Mansion",           value="mansion"),
    # wildemount
    app_commands.Choice(name="Xhorhas Wastes",    value="xhorhas_wastes"),
    app_commands.Choice(name="Aeor Ruins",        value="aeor_ruins"),
    app_commands.Choice(name="Rosohna",           value="rosohna"),
    app_commands.Choice(name="Dwendalian Keep",   value="dwendalian_keep"),
    app_commands.Choice(name="Menagerie Port",    value="menagerie_port"),
    app_commands.Choice(name="Eiselcross",        value="eiselcross"),
    app_commands.Choice(name="Kryn Temple",       value="kryn_temple"),
]


class MapsCog(commands.Cog, name="Maps"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_map: dict | None = None

    map_group = app_commands.Group(name="map", description="Map tools")

    @map_group.command(name="generate", description="Generate a map (DM preview only)")
    @app_commands.choices(map_type=_TYPE_CHOICES, subtype=_SUBTYPE_CHOICES)
    @dm_only()
    async def map_generate(
        self,
        interaction: discord.Interaction,
        map_type: str = "dungeon",
        subtype: str = "",
    ):
        await interaction.response.defer(ephemeral=True)
        result = map_gen.generate(map_type, subtype or None)
        map_data = result.to_dict()

        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        map_name = f"{map_type.title()} — {map_data.get('subtype','generic').title()}"
        mid = db.execute(
            "INSERT INTO maps (campaign_id,name,map_data) VALUES (?,?,?)",
            (cid, map_name, json.dumps(map_data)),
        )
        map_data["_db_id"] = mid
        self._last_map = map_data

        buf = renderer.scale_for_discord(map_data)
        file = discord.File(buf, filename="map_preview.png")
        embed = discord.Embed(title=f"Map Preview — {map_name}",
                              description=f"{map_data['width']}×{map_data['height']} tiles", colour=0x3A6080)
        embed.add_field(name="Map ID",   value=str(mid),                           inline=True)
        embed.add_field(name="Rooms",   value=str(len(map_data.get("rooms", []))), inline=True)
        embed.add_field(name="Size",    value=f"{map_data['width']}×{map_data['height']}", inline=True)
        features = map_data.get("features", [])
        if features:
            ftypes = ", ".join({f["type"] for f in features[:6]})
            embed.add_field(name="Features", value=ftypes, inline=False)
        legend = map_data.get("legend", {})
        if legend:
            embed.add_field(name="Legend", value=" · ".join(f"{v}" for v in legend.values()), inline=False)
        embed.set_image(url="attachment://map_preview.png")
        embed.set_footer(text="Use /map share to post this to the player channel")
        await interaction.followup.send(embed=embed, file=file, ephemeral=True)

    @map_group.command(name="share", description="Post a map to the player channel")
    @dm_only()
    async def map_share(self, interaction: discord.Interaction, map_id: int = 0):
        await interaction.response.defer(ephemeral=True)
        if map_id:
            row = db.fetchone("SELECT map_data, name FROM maps WHERE id=?", (map_id,))
            if not row:
                await interaction.followup.send(f"No map with ID {map_id}.", ephemeral=True)
                return
            map_data = json.loads(row["map_data"])
            map_name = row["name"]
        elif self._last_map:
            map_data = self._last_map
            map_name = f"{map_data['map_type'].title()} — {map_data.get('subtype','').title()}"
        else:
            await interaction.followup.send(
                "No map to share. Run `/map generate` first.", ephemeral=True
            )
            return

        player_channel_id = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(player_channel_id)) if player_channel_id else interaction.channel

        buf = renderer.scale_for_discord(map_data)
        file = discord.File(buf, filename="map.png")
        embed = discord.Embed(title=map_name, colour=0x3A6080)
        embed.set_image(url="attachment://map.png")
        await target.send(embed=embed, file=file)
        await interaction.followup.send(f"Map posted to {target.mention}.", ephemeral=True)

    @map_group.command(name="list", description="List saved maps")
    @dm_only()
    async def map_list(self, interaction: discord.Interaction):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        rows = db.fetchall(
            "SELECT id,name,created_at FROM maps WHERE campaign_id=? ORDER BY id DESC LIMIT 20",
            (cid,) if cid else (),
        )
        if not rows:
            await interaction.response.send_message("No saved maps.", ephemeral=True)
            return
        embed = discord.Embed(title="Saved Maps", colour=0x3A6080)
        for r in rows:
            embed.add_field(name=f"[{r['id']}] {r['name']}", value=r["created_at"][:16], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MapsCog(bot))
