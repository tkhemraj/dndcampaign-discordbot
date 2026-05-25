"""Generation cog — NPCs, quests, encounters."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import dm_only
from bot.generators import npc_gen, quest_gen, encounter_gen, npc_dialogue
from bot.generators.data.npc_library import ALL_NPCS, by_tier, by_region, find_by_name

_TIER_CHOICES = [
    app_commands.Choice(name="Legendary (5)",  value="legendary"),
    app_commands.Choice(name="Mega (10)",      value="mega"),
    app_commands.Choice(name="Notable (20)",   value="notable"),
    app_commands.Choice(name="Standard (150)", value="standard"),
]

_REGION_CHOICES = [
    app_commands.Choice(name="Western Wynandir",  value="Western Wynandir"),
    app_commands.Choice(name="Xhorhas",           value="Xhorhas"),
    app_commands.Choice(name="Menagerie Coast",   value="Menagerie Coast"),
    app_commands.Choice(name="Greying Wildlands", value="Greying Wildlands"),
    app_commands.Choice(name="Eiselcross",        value="Eiselcross"),
]

_FACTION_CHOICES = [
    app_commands.Choice(name="Dwendalian Empire", value="Dwendalian Empire"),
    app_commands.Choice(name="Cerberus Assembly", value="Cerberus Assembly"),
    app_commands.Choice(name="Kryn Dynasty",      value="Kryn Dynasty"),
    app_commands.Choice(name="Cobalt Soul",        value="Cobalt Soul"),
    app_commands.Choice(name="The Revelry",        value="The Revelry"),
    app_commands.Choice(name="The Myriad",         value="The Myriad"),
    app_commands.Choice(name="The Clovis Concord", value="The Clovis Concord"),
]

_DIFFICULTY_CHOICES = [
    app_commands.Choice(name="Easy",   value="easy"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="Hard",   value="hard"),
    app_commands.Choice(name="Deadly", value="deadly"),
]

_STATUS_CHOICES = [
    app_commands.Choice(name="Alive",   value="alive"),
    app_commands.Choice(name="Dead",    value="dead"),
    app_commands.Choice(name="Unknown", value="unknown"),
]


def _mod(score: int) -> str:
    m = (score - 10) // 2
    return f"+{m}" if m >= 0 else str(m)


def _npc_embed(npc: dict) -> discord.Embed:
    embed = discord.Embed(
        title=npc["name"],
        description=f"{npc.get('race','?')} {npc.get('npc_class','?')} · Level {npc.get('level',1)}",
        colour=0xD4A040,
    )
    embed.add_field(name="Alignment", value=npc.get("alignment","?"),        inline=True)
    embed.add_field(name="Faction",   value=npc.get("faction") or "None",    inline=True)
    embed.add_field(name="Region",    value=npc.get("region") or "?",        inline=True)
    embed.add_field(name="HP",        value=str(npc.get("hp","?")),           inline=True)
    embed.add_field(name="AC",        value=str(npc.get("ac","?")),           inline=True)
    embed.add_field(name="Status",    value=npc.get("status","alive").title(),inline=True)
    for s, label in [("str","STR"),("dex","DEX"),("con","CON"),("int","INT"),("wis","WIS"),("cha","CHA")]:
        score = npc.get(f"{s}_score", 10)
        embed.add_field(name=label, value=f"**{score}**\n({_mod(score)})", inline=True)
    if npc.get("personality"):
        embed.add_field(name="Personality", value=npc["personality"], inline=False)
    if npc.get("ideal"):
        embed.add_field(name="Ideal", value=npc["ideal"], inline=True)
    if npc.get("bond"):
        embed.add_field(name="Bond",  value=npc["bond"],  inline=True)
    if npc.get("flaw"):
        embed.add_field(name="Flaw",  value=npc["flaw"],  inline=True)
    if npc.get("backstory"):
        embed.add_field(name="Backstory", value=npc["backstory"][:1024], inline=False)
    return embed


def _quest_embed(quest: dict) -> discord.Embed:
    colours = {"easy": 0x44AA44, "medium": 0xD4A040, "hard": 0xDD6622, "deadly": 0xCC2222}
    embed = discord.Embed(
        title=quest["title"],
        description=quest.get("description",""),
        colour=colours.get(quest.get("difficulty","medium"), 0xD4A040),
    )
    embed.add_field(name="Difficulty", value=quest.get("difficulty","medium").title(), inline=True)
    embed.add_field(name="Region",     value=quest.get("region") or "?",              inline=True)
    embed.add_field(name="Faction",    value=quest.get("faction") or "None",          inline=True)
    if quest.get("reward"):
        embed.add_field(name="Reward", value=quest["reward"], inline=False)
    return embed


class GenerateCog(commands.Cog, name="Generate"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── NPC ──────────────────────────────────────────────────────────────────

    npc_group = app_commands.Group(name="npc", description="NPC tools")

    @npc_group.command(name="generate", description="Generate and save an NPC")
    @app_commands.choices(region=_REGION_CHOICES, faction=_FACTION_CHOICES)
    @dm_only()
    async def npc_generate(self, interaction: discord.Interaction, region: str = "", faction: str = ""):
        await interaction.response.defer(ephemeral=True)
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        npc = npc_gen.generate(cid, region or None, faction or None)
        row_id = db.execute(
            """INSERT INTO npcs
               (campaign_id,name,race,npc_class,level,faction,region,alignment,
                personality,ideal,bond,flaw,backstory,hp,ac,
                str_score,dex_score,con_score,int_score,wis_score,cha_score)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, npc["name"], npc["race"], npc["npc_class"], npc["level"],
             npc.get("faction"), npc.get("region"), npc["alignment"],
             npc["personality"], npc["ideal"], npc["bond"], npc["flaw"],
             npc["backstory"], npc["hp"], npc["ac"],
             npc["str_score"], npc["dex_score"], npc["con_score"],
             npc["int_score"], npc["wis_score"], npc["cha_score"]),
        )
        npc["id"] = row_id
        embed = _npc_embed(npc)
        embed.set_footer(text=f"Saved as NPC ID {row_id}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @npc_group.command(name="view", description="View a saved NPC's full stat card")
    @dm_only()
    async def npc_view(self, interaction: discord.Interaction, npc_id: int):
        row = db.fetchone("SELECT * FROM npcs WHERE id=?", (npc_id,))
        if not row:
            await interaction.response.send_message(f"No NPC with ID {npc_id}.", ephemeral=True)
            return
        embed = _npc_embed(row)
        embed.set_footer(text=f"NPC ID {npc_id} · Status: {row.get('status','alive').title()}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @npc_group.command(name="speak", description="Ask an NPC something — reply posts to the player channel")
    @dm_only()
    async def npc_speak(self, interaction: discord.Interaction, npc_id: int, question: str):
        await interaction.response.defer(ephemeral=True)
        npc = db.fetchone("SELECT * FROM npcs WHERE id=?", (npc_id,))
        if not npc:
            await interaction.followup.send(f"No NPC with ID {npc_id}.", ephemeral=True)
            return
        try:
            reply = await interaction.client.loop.run_in_executor(
                None, npc_dialogue.speak, npc, question
            )
        except RuntimeError as e:
            await interaction.followup.send(f"AI dialogue unavailable: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            description=f'*"{reply}"*',
            colour=0xD4A040,
        )
        embed.set_author(name=npc["name"])
        embed.add_field(
            name="",
            value=f"> {question}",
            inline=False,
        )
        embed.set_footer(
            text=f"{npc['race']} {npc['npc_class']} · {npc.get('faction') or 'No faction'} · {npc.get('region') or 'Wildemount'}"
        )

        player_channel_id = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(player_channel_id)) if player_channel_id else interaction.channel
        await target.send(embed=embed)
        await interaction.followup.send(f"Posted to {target.mention}.", ephemeral=True)

    @npc_group.command(name="list", description="List NPCs in the active campaign")
    @app_commands.choices(status=_STATUS_CHOICES)
    async def npc_list(self, interaction: discord.Interaction, status: str = "alive"):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT id,name,race,npc_class,level,faction FROM npcs WHERE campaign_id=? AND status=? ORDER BY name",
            (cid, status),
        )
        if not rows:
            await interaction.response.send_message(f"No {status} NPCs.", ephemeral=True)
            return
        embed = discord.Embed(title=f"NPCs — {status.title()}", colour=0xD4A040)
        for r in rows[:20]:
            embed.add_field(
                name=f"[{r['id']}] {r['name']}",
                value=f"{r['race']} {r['npc_class']} lv{r['level']} · {r.get('faction') or 'No faction'}",
                inline=False,
            )
        if len(rows) > 20:
            embed.set_footer(text=f"Showing 20 of {len(rows)}")
        await interaction.response.send_message(embed=embed)

    @npc_group.command(name="library", description="Browse the 185 hand-crafted NPC library")
    @app_commands.choices(tier=_TIER_CHOICES, region=_REGION_CHOICES)
    @dm_only()
    async def npc_library(self, interaction: discord.Interaction, tier: str = "", region: str = ""):
        pool = ALL_NPCS
        if tier:
            pool = [n for n in pool if n["tier"] == tier]
        if region:
            pool = [n for n in pool if region.lower() in n["region"].lower()]
        if not pool:
            await interaction.response.send_message("No NPCs match those filters.", ephemeral=True)
            return
        tier_icons = {"legendary": "🔥", "mega": "⚡", "notable": "✨", "standard": "·"}
        embed = discord.Embed(
            title=f"NPC Library — {len(pool)} characters",
            description="Use `/npc summon <name>` to add one to your campaign.",
            colour=0xD4A040,
        )
        for n in pool[:20]:
            icon = tier_icons.get(n["tier"], "·")
            embed.add_field(
                name=f"{icon} {n['name']}",
                value=f"{n['race']} {n['suggested_class']} · {n.get('faction') or 'None'} · {n['region']}",
                inline=False,
            )
        if len(pool) > 20:
            embed.set_footer(text=f"Showing 20 of {len(pool)} — add tier or region filter to narrow")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @npc_group.command(name="summon", description="Add a library NPC to your campaign (rolls their stats)")
    @dm_only()
    async def npc_summon(self, interaction: discord.Interaction, name: str):
        template = find_by_name(name)
        if not template:
            close = [n["name"] for n in ALL_NPCS if name.lower() in n["name"].lower()][:5]
            hint = f"\nDid you mean: {', '.join(close)}?" if close else ""
            await interaction.response.send_message(f"No library NPC named '{name}'.{hint}", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        npc = npc_gen.generate(cid, template["region"], template.get("faction"))
        # Override procedural fields with library data
        npc.update({
            "name":        template["name"],
            "race":        template["race"],
            "npc_class":   template["suggested_class"],
            "level":       template["suggested_level"],
            "faction":     template.get("faction"),
            "region":      template["region"],
            "alignment":   template["alignment"],
            "personality": template["personality"],
            "ideal":       template["ideal"],
            "bond":        template["bond"],
            "flaw":        template["flaw"],
            "backstory":   template["backstory"],
        })
        row_id = db.execute(
            """INSERT INTO npcs
               (campaign_id,name,race,npc_class,level,faction,region,alignment,
                personality,ideal,bond,flaw,backstory,hp,ac,
                str_score,dex_score,con_score,int_score,wis_score,cha_score)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, npc["name"], npc["race"], npc["npc_class"], npc["level"],
             npc.get("faction"), npc.get("region"), npc["alignment"],
             npc["personality"], npc["ideal"], npc["bond"], npc["flaw"],
             npc["backstory"], npc["hp"], npc["ac"],
             npc["str_score"], npc["dex_score"], npc["con_score"],
             npc["int_score"], npc["wis_score"], npc["cha_score"]),
        )
        npc["id"] = row_id
        tier_label = template["tier"].title()
        embed = _npc_embed(npc)
        embed.set_footer(text=f"Library NPC ({tier_label}) · Saved as ID {row_id} · Use /npc speak {row_id}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @npc_group.command(name="kill", description="Mark an NPC as dead")
    @dm_only()
    async def npc_kill(self, interaction: discord.Interaction, npc_id: int):
        row = db.fetchone("SELECT id,name,status FROM npcs WHERE id=?", (npc_id,))
        if not row:
            await interaction.response.send_message(f"No NPC with ID {npc_id}.", ephemeral=True)
            return
        if row["status"] == "dead":
            await interaction.response.send_message(f"**{row['name']}** is already dead.", ephemeral=True)
            return
        db.execute("UPDATE npcs SET status='dead' WHERE id=?", (npc_id,))
        await interaction.response.send_message(f"**{row['name']}** marked as dead.", ephemeral=True)

    # ── Quest ─────────────────────────────────────────────────────────────────

    quest_group = app_commands.Group(name="quest", description="Quest tools")

    @quest_group.command(name="generate", description="Generate and save a quest hook")
    @app_commands.choices(region=_REGION_CHOICES, faction=_FACTION_CHOICES)
    @dm_only()
    async def quest_generate(self, interaction: discord.Interaction, region: str = "", faction: str = ""):
        await interaction.response.defer(ephemeral=True)
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        quest = quest_gen.generate(cid, region or None, faction or None)
        row_id = db.execute(
            "INSERT INTO quests (campaign_id,title,description,faction,region,difficulty,reward) VALUES (?,?,?,?,?,?,?)",
            (cid, quest["title"], quest.get("description"), quest.get("faction"),
             quest.get("region"), quest.get("difficulty","medium"), quest.get("reward")),
        )
        quest["id"] = row_id
        embed = _quest_embed(quest)
        embed.set_footer(text=f"Saved as Quest ID {row_id}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @quest_group.command(name="board", description="Post the active quest board to the player channel")
    @dm_only()
    async def quest_board(self, interaction: discord.Interaction):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT * FROM quests WHERE campaign_id=? AND status='active' ORDER BY created_at DESC",
            (cid,),
        )
        if not rows:
            await interaction.response.send_message("No active quests.", ephemeral=True)
            return
        player_channel_id = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(player_channel_id)) if player_channel_id else interaction.channel
        await interaction.response.defer(ephemeral=True)
        colours = {"easy": 0x44AA44, "medium": 0xD4A040, "hard": 0xDD6622, "deadly": 0xCC2222}
        board = discord.Embed(
            title="📋 Quest Board",
            description=f"**{len(rows)}** active quest{'s' if len(rows)!=1 else ''}",
            colour=0xD4A040,
        )
        for quest in rows[:10]:
            diff  = quest.get("difficulty","medium")
            region = quest.get("region") or ""
            reward = quest.get("reward") or ""
            meta = " · ".join(filter(None, [diff.title(), region, f"Reward: {reward}" if reward else ""]))
            board.add_field(
                name=quest["title"],
                value=f"{quest.get('description','')[:200]}\n*{meta}*" if meta else quest.get("description","")[:200],
                inline=False,
            )
        if len(rows) > 10:
            board.set_footer(text=f"Showing 10 of {len(rows)} quests")
        await target.send(embed=board)
        await interaction.followup.send(f"Quest board posted to {target.mention}.", ephemeral=True)

    @quest_group.command(name="complete", description="Mark a quest as completed")
    @dm_only()
    async def quest_complete(self, interaction: discord.Interaction, quest_id: int):
        row = db.fetchone("SELECT id,title,status FROM quests WHERE id=?", (quest_id,))
        if not row:
            await interaction.response.send_message(f"No quest with ID {quest_id}.", ephemeral=True)
            return
        if row["status"] == "completed":
            await interaction.response.send_message(f"Quest **{row['title']}** is already completed.", ephemeral=True)
            return
        db.execute("UPDATE quests SET status='completed' WHERE id=?", (quest_id,))
        await interaction.response.send_message(f"Quest **{row['title']}** marked as completed.", ephemeral=True)

    # ── Encounter ─────────────────────────────────────────────────────────────

    encounter_group = app_commands.Group(name="encounter", description="Encounter generation")

    @encounter_group.command(name="generate", description="Generate and save an encounter")
    @app_commands.choices(difficulty=_DIFFICULTY_CHOICES)
    @dm_only()
    async def encounter_generate(
        self,
        interaction: discord.Interaction,
        party_size: int = 4,
        level: int = 5,
        difficulty: str = "medium",
    ):
        await interaction.response.defer(ephemeral=True)
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        enc = encounter_gen.generate(cid, party_size, level, difficulty)
        eid = db.execute(
            "INSERT INTO encounters (campaign_id,name,status) VALUES (?,?,?)",
            (cid, enc.get("name","Generated Encounter"), "planning"),
        )
        for c in enc.get("combatants", []):
            db.execute(
                """INSERT INTO combatants
                   (encounter_id,name,combatant_type,initiative,hp,max_hp,ac,atk_bonus,damage_dice,conditions,notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (eid, c["name"], c.get("combatant_type","monster"), 0,
                 c["hp"], c["max_hp"], c["ac"],
                 c.get("atk_bonus", 2), c.get("damage_dice", "1d6"),
                 c.get("conditions","[]"), c.get("notes","")),
            )
        embed = discord.Embed(
            title=enc.get("name","Encounter"),
            description=f"**{difficulty.title()}** · {party_size}×lv{level}",
            colour=0xCC2222,
        )
        embed.add_field(name="Total XP",    value=str(enc.get("total_xp",0)),              inline=True)
        embed.add_field(name="Combatants",  value=str(len(enc.get("combatants",[]))),       inline=True)
        roster = "\n".join(
            f"• {c['name']} — HP {c['hp']}, AC {c['ac']}"
            for c in enc.get("combatants",[])[:15]
        )
        if roster:
            embed.add_field(name="Roster", value=roster, inline=False)
        embed.set_footer(text=f"Encounter ID {eid} · Use /combat start {eid} to begin")
        await interaction.followup.send(embed=embed, ephemeral=True)


    @encounter_group.command(name="list", description="List saved encounters for this campaign")
    @dm_only()
    async def encounter_list(self, interaction: discord.Interaction):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT id,name,status,created_at FROM encounters WHERE campaign_id=? ORDER BY id DESC LIMIT 15",
            (cid,),
        )
        if not rows:
            await interaction.response.send_message("No encounters yet.", ephemeral=True)
            return
        embed = discord.Embed(title="Encounters", colour=0xCC2222)
        for r in rows:
            embed.add_field(
                name=f"[{r['id']}] {r['name']}",
                value=f"{r['status'].title()} · {r['created_at'][:10]}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GenerateCog(bot))
