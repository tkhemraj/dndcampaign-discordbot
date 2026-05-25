"""Player character registration and party tracker."""
from __future__ import annotations
import json
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import dm_only, is_dm

_REST_CHOICES = [
    app_commands.Choice(name="Short Rest", value="short"),
    app_commands.Choice(name="Long Rest",  value="long"),
]


def _mod(score: int) -> str:
    m = (score - 10) // 2
    return f"+{m}" if m >= 0 else str(m)


def _hp_bar(hp: int, max_hp: int) -> str:
    filled = round((hp / max_hp) * 10 if max_hp else 0)
    return "█" * filled + "░" * (10 - filled)


def _slot_line(slots: dict) -> str:
    if not slots:
        return ""
    parts = []
    for lvl in sorted(slots.keys(), key=int):
        cur, mx = slots[lvl]
        parts.append(f"L{lvl}: {cur}/{mx}")
    return "  ·  ".join(parts)


def _pc_embed(pc: dict) -> discord.Embed:
    pct = pc["hp"] / pc["max_hp"] if pc["max_hp"] else 0
    colour = 0x44AA44 if pct > 0.5 else 0xD4A040 if pct > 0.25 else 0xCC2222
    embed = discord.Embed(
        title=pc["name"],
        description=f"{pc.get('race','?')} {pc.get('pc_class','?')} · Level {pc.get('level',1)}",
        colour=colour,
    )
    bar = _hp_bar(pc["hp"], pc["max_hp"])
    embed.add_field(name="HP",     value=f"**{pc['hp']}/{pc['max_hp']}** `{bar}`", inline=False)
    embed.add_field(name="AC",     value=str(pc.get("ac", 10)),    inline=True)
    embed.add_field(name="Level",  value=str(pc.get("level", 1)),  inline=True)
    embed.add_field(name="Status", value=pc.get("status","active").title(), inline=True)

    for s, label in [("str","STR"),("dex","DEX"),("con","CON"),
                     ("int","INT"),("wis","WIS"),("cha","CHA")]:
        score = pc.get(f"{s}_score", 10)
        embed.add_field(name=label, value=f"**{score}**\n({_mod(score)})", inline=True)

    slots = json.loads(pc.get("spell_slots") or "{}")
    slot_str = _slot_line(slots)
    if slot_str:
        embed.add_field(name="Spell Slots", value=slot_str, inline=False)

    if pc.get("inspiration"):
        embed.add_field(name="✨ Inspiration", value="Active", inline=True)

    if pc.get("notes"):
        embed.add_field(name="Notes", value=pc["notes"][:256], inline=False)

    return embed


class PCCog(commands.Cog, name="PlayerChars"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    pc_group = app_commands.Group(name="pc", description="Player character management")

    # ── Register ──────────────────────────────────────────────────────────────

    @pc_group.command(name="register", description="Register your character for the active campaign")
    @app_commands.describe(
        name="Character name",
        race="Race (e.g. Human, Elf, Dwarf)",
        pc_class="Class (e.g. Fighter, Wizard, Rogue)",
        level="Current level",
        max_hp="Maximum hit points",
        ac="Armour Class",
    )
    async def pc_register(
        self,
        interaction: discord.Interaction,
        name: str,
        race: str,
        pc_class: str,
        level: int = 1,
        max_hp: int = 10,
        ac: int = 10,
    ) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign. Start one with `/campaign new [name]`, then `/campaign select` to activate it.", ephemeral=True)
            return
        existing = db.fetchone(
            "SELECT id FROM player_characters WHERE campaign_id=? AND name=? COLLATE NOCASE",
            (cid, name),
        )
        if existing:
            await interaction.response.send_message(
                f"**{name}** is already registered in this campaign.", ephemeral=True
            )
            return
        pc_id = db.execute(
            """INSERT INTO player_characters
               (campaign_id, discord_user_id, name, race, pc_class, level, hp, max_hp, ac)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (cid, str(interaction.user.id), name, race, pc_class, level, max_hp, max_hp, ac),
        )
        embed = discord.Embed(
            title=f"✅  {name} joined the party!",
            description=f"{race} {pc_class} · Level {level}",
            colour=0x44AA44,
        )
        embed.add_field(name="HP",  value=f"{max_hp}/{max_hp} `{'█'*10}`", inline=True)
        embed.add_field(name="AC",  value=str(ac),    inline=True)
        embed.add_field(name="ID",  value=str(pc_id), inline=True)
        embed.set_footer(text="Use /pc update to change stats · /pc slots to track spell slots")
        await interaction.response.send_message(embed=embed)

    # ── View ──────────────────────────────────────────────────────────────────

    @pc_group.command(name="view", description="View a character sheet")
    @app_commands.describe(name="Character name (partial match)")
    async def pc_view(self, interaction: discord.Interaction, name: str = "") -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if name:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
                (cid, f"%{name}%"),
            ) if cid else None
        else:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
                (cid, str(interaction.user.id)),
            ) if cid else None
        if not pc:
            hint = " Use `/pc register` to create one." if not name else ""
            await interaction.response.send_message(
                f"No character found.{hint}", ephemeral=True
            )
            return
        await interaction.response.send_message(embed=_pc_embed(pc))

    # ── List (party overview) ─────────────────────────────────────────────────

    @pc_group.command(name="list", description="Show all party members with HP and status")
    async def pc_list(self, interaction: discord.Interaction) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign. Start one with `/campaign new [name]`, then `/campaign select` to activate it.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT * FROM player_characters WHERE campaign_id=? AND status='active' ORDER BY name",
            (cid,),
        )
        if not rows:
            await interaction.response.send_message(
                "No characters registered yet. Anyone can use `/pc register` to add theirs!",
                ephemeral=True,
            )
            return
        embed = discord.Embed(title="⚔️  Party", colour=0xD4A040)
        for pc in rows:
            bar = _hp_bar(pc["hp"], pc["max_hp"])
            pct = pc["hp"] / pc["max_hp"] if pc["max_hp"] else 0
            icon = "🟢" if pct > 0.5 else "🟡" if pct > 0.25 else "🔴"
            insp = " ✨" if pc.get("inspiration") else ""
            slots = json.loads(pc.get("spell_slots") or "{}")
            slot_str = f" · Slots: {_slot_line(slots)}" if slots else ""
            embed.add_field(
                name=f"{icon} {pc['name']}{insp}",
                value=f"{pc['race']} {pc['pc_class']} lv{pc['level']} · "
                      f"HP {pc['hp']}/{pc['max_hp']} `{bar}` · AC {pc['ac']}{slot_str}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    # ── HP ────────────────────────────────────────────────────────────────────

    @pc_group.command(name="hp", description="Update your character's HP (+heal / -damage)")
    @app_commands.describe(delta="Change in HP (e.g. +5 to heal, -8 for damage)",
                           name="Character name (if you have multiple characters)")
    async def pc_hp(self, interaction: discord.Interaction, delta: int, name: str = "") -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if name and is_dm(interaction):
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
                (cid, f"%{name}%"),
            ) if cid else None
        elif name:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
                (cid, str(interaction.user.id), f"%{name}%"),
            ) if cid else None
        else:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
                (cid, str(interaction.user.id)),
            ) if cid else None
        if not pc:
            await interaction.response.send_message(
                "No character found. Use `/pc register` first.", ephemeral=True
            )
            return
        new_hp = max(0, min(pc["hp"] + delta, pc["max_hp"]))
        db.execute("UPDATE player_characters SET hp=? WHERE id=?", (new_hp, pc["id"]))
        sign = f"+{delta}" if delta >= 0 else str(delta)
        bar = _hp_bar(new_hp, pc["max_hp"])
        pct = new_hp / pc["max_hp"] if pc["max_hp"] else 0
        colour = 0x44AA44 if pct > 0.5 else 0xD4A040 if pct > 0.25 else 0xCC2222
        embed = discord.Embed(colour=colour)
        embed.add_field(
            name=pc["name"],
            value=f"{pc['hp']} → **{new_hp}** ({sign})  `{bar}`",
        )
        await interaction.response.send_message(embed=embed)

    # ── Update stats ──────────────────────────────────────────────────────────

    @pc_group.command(name="update", description="Update your character's stats (DM can update any character)")
    @app_commands.describe(
        name="Character to update (DM: specify whose; players: leave blank for yours)",
        ac="New Armour Class",
        level="New level",
        max_hp="New max HP (also refills current HP to new max)",
        notes="Short notes visible on character sheet",
    )
    async def pc_update(
        self,
        interaction: discord.Interaction,
        name: str = "",
        ac: int = 0,
        level: int = 0,
        max_hp: int = 0,
        notes: str = "",
    ) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if name and is_dm(interaction):
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
                (cid, f"%{name}%"),
            ) if cid else None
        else:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
                (cid, str(interaction.user.id)),
            ) if cid else None
        if not pc:
            await interaction.response.send_message("Character not found.", ephemeral=True)
            return
        updates, params = [], []
        if ac:    updates.append("ac=?");    params.append(ac)
        if level: updates.append("level=?"); params.append(level)
        if max_hp:
            updates.extend(["max_hp=?", "hp=?"])
            params.extend([max_hp, max_hp])
        if notes:
            updates.append("notes=?"); params.append(notes[:512])
        if not updates:
            await interaction.response.send_message(
                "Specify at least one field to update.", ephemeral=True
            )
            return
        params.append(pc["id"])
        db.execute(f"UPDATE player_characters SET {', '.join(updates)} WHERE id=?", tuple(params))
        changed = ", ".join(
            filter(None, [
                f"AC→{ac}" if ac else "",
                f"Lv→{level}" if level else "",
                f"MaxHP→{max_hp}" if max_hp else "",
                "notes" if notes else "",
            ])
        )
        await interaction.response.send_message(
            f"**{pc['name']}** updated ({changed}).", ephemeral=True
        )

    # ── Spell slots ───────────────────────────────────────────────────────────

    @pc_group.command(name="slots", description="Set your spell slot totals for levels 1–6")
    @app_commands.describe(
        l1="Level 1 slots", l2="Level 2 slots", l3="Level 3 slots",
        l4="Level 4 slots", l5="Level 5 slots", l6="Level 6 slots",
    )
    async def pc_slots(
        self,
        interaction: discord.Interaction,
        l1: int = 0, l2: int = 0, l3: int = 0,
        l4: int = 0, l5: int = 0, l6: int = 0,
    ) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        pc = db.fetchone(
            "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (cid, str(interaction.user.id)),
        ) if cid else None
        if not pc:
            await interaction.response.send_message(
                "No active character. Use `/pc register` first.", ephemeral=True
            )
            return
        slots = json.loads(pc.get("spell_slots") or "{}")
        for lvl, total in zip(range(1, 7), [l1, l2, l3, l4, l5, l6]):
            if total > 0:
                slots[str(lvl)] = [total, total]
        db.execute("UPDATE player_characters SET spell_slots=? WHERE id=?",
                   (json.dumps(slots), pc["id"]))
        slot_str = _slot_line(slots)
        await interaction.response.send_message(
            f"**{pc['name']}** spell slots set: {slot_str}", ephemeral=True
        )

    @pc_group.command(name="cast", description="Expend one spell slot")
    @app_commands.describe(level="Spell slot level to expend (1–9)")
    async def pc_cast(self, interaction: discord.Interaction, level: int) -> None:
        if not (1 <= level <= 9):
            await interaction.response.send_message("Level must be 1–9.", ephemeral=True)
            return
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        pc = db.fetchone(
            "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (cid, str(interaction.user.id)),
        ) if cid else None
        if not pc:
            await interaction.response.send_message("No active character found.", ephemeral=True)
            return
        slots = json.loads(pc.get("spell_slots") or "{}")
        key = str(level)
        if key not in slots or slots[key][0] <= 0:
            await interaction.response.send_message(
                f"No level {level} spell slots remaining.", ephemeral=True
            )
            return
        slots[key][0] -= 1
        db.execute("UPDATE player_characters SET spell_slots=? WHERE id=?",
                   (json.dumps(slots), pc["id"]))
        cur, mx = slots[key]
        await interaction.response.send_message(
            f"**{pc['name']}** cast a level {level} spell. Slots remaining: {cur}/{mx}"
        )

    # ── Rest ──────────────────────────────────────────────────────────────────

    @pc_group.command(name="rest", description="Apply a rest to all party members")
    @app_commands.choices(rest_type=_REST_CHOICES)
    @dm_only()
    async def pc_rest(self, interaction: discord.Interaction, rest_type: str) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign. Start one with `/campaign new [name]`, then `/campaign select` to activate it.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT * FROM player_characters WHERE campaign_id=? AND status='active'",
            (cid,),
        )
        if not rows:
            await interaction.response.send_message("No active characters.", ephemeral=True)
            return
        if rest_type == "long":
            for pc in rows:
                slots = json.loads(pc.get("spell_slots") or "{}")
                for key in slots:
                    slots[key][0] = slots[key][1]
                db.execute(
                    "UPDATE player_characters SET hp=max_hp, spell_slots=? WHERE id=?",
                    (json.dumps(slots), pc["id"]),
                )
            desc = "HP fully restored · Spell slots fully recovered · Inspiration retained"
        else:
            desc = "Short rest taken. Players: use `/pc hp` to spend Hit Dice."

        pcid = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(pcid)) if pcid else interaction.channel
        title = "🌙  Long Rest" if rest_type == "long" else "⏰  Short Rest"
        embed = discord.Embed(title=title, description=desc, colour=0x5060A0)
        embed.set_footer(text=f"{len(rows)} character(s) updated")
        await target.send(embed=embed)
        await interaction.response.send_message("Rest applied.", ephemeral=True)

    # ── Inspiration ───────────────────────────────────────────────────────────

    @pc_group.command(name="inspire", description="Grant or remove Inspiration from a character")
    @app_commands.describe(name="Character name")
    @dm_only()
    async def pc_inspire(self, interaction: discord.Interaction, name: str) -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        pc = db.fetchone(
            "SELECT * FROM player_characters WHERE campaign_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
            (cid, f"%{name}%"),
        ) if cid else None
        if not pc:
            await interaction.response.send_message(
                f"No character matching '{name}'.", ephemeral=True
            )
            return
        new_val = 0 if pc.get("inspiration") else 1
        db.execute("UPDATE player_characters SET inspiration=? WHERE id=?", (new_val, pc["id"]))
        verb = "granted ✨ Inspiration" if new_val else "lost Inspiration"
        pcid = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(pcid)) if pcid else interaction.channel
        await target.send(f"**{pc['name']}** has been {verb}!")
        await interaction.response.send_message("Done.", ephemeral=True)

    # ── Retire ────────────────────────────────────────────────────────────────

    @pc_group.command(name="retire", description="Retire or remove your character from the active roster")
    @app_commands.describe(name="Character name (DM can retire any; players retire their own)")
    async def pc_retire(self, interaction: discord.Interaction, name: str = "") -> None:
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if name and is_dm(interaction):
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND name LIKE ? COLLATE NOCASE ORDER BY id DESC LIMIT 1",
                (cid, f"%{name}%"),
            ) if cid else None
        else:
            pc = db.fetchone(
                "SELECT * FROM player_characters WHERE campaign_id=? AND discord_user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
                (cid, str(interaction.user.id)),
            ) if cid else None
        if not pc:
            await interaction.response.send_message("Character not found.", ephemeral=True)
            return
        db.execute("UPDATE player_characters SET status='retired' WHERE id=?", (pc["id"],))
        await interaction.response.send_message(
            f"**{pc['name']}** retired from active duty.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PCCog(bot))
