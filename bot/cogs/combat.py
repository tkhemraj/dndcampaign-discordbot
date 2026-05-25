"""Combat tracker — live embed in player channel, DM controls."""
from __future__ import annotations
import asyncio
import json
import os
import tempfile
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db
from bot.guard import dm_only

_active: dict[int, "_Tracker"] = {}

_CONDITION_CHOICES = [
    app_commands.Choice(name=c, value=c) for c in [
        "Blinded", "Charmed", "Deafened", "Exhaustion", "Frightened",
        "Grappled", "Incapacitated", "Invisible", "Paralyzed", "Petrified",
        "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious",
    ]
]


def _tts_to_file(text: str) -> str:
    """Generate TTS MP3 via gTTS and return a temp file path. Runs in thread executor."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="en", slow=False)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(tmp.name)
    return tmp.name


async def _speak(vc: discord.VoiceClient, text: str) -> None:
    """Play a TTS announcement on an already-connected VoiceClient."""
    if vc is None or not vc.is_connected():
        return
    try:
        path = await asyncio.get_event_loop().run_in_executor(None, _tts_to_file, text)
    except Exception:
        return
    if vc.is_playing():
        vc.stop()
    def _after(_err):
        try:
            os.unlink(path)
        except OSError:
            pass
    vc.play(discord.FFmpegPCMAudio(path), after=_after)


class _Tracker:
    def __init__(self, encounter_id: int, guild_id: int, player_message: discord.Message):
        self.encounter_id = encounter_id
        self.guild_id = guild_id
        self.player_message = player_message
        self.vc: discord.VoiceClient | None = None

    def combatants(self) -> list[dict]:
        return db.fetchall(
            "SELECT * FROM combatants WHERE encounter_id=? AND is_active=1 ORDER BY initiative DESC",
            (self.encounter_id,),
        )

    def fallen(self) -> list[dict]:
        return db.fetchall(
            "SELECT * FROM combatants WHERE encounter_id=? AND is_active=0 ORDER BY initiative DESC",
            (self.encounter_id,),
        )

    def encounter(self) -> dict:
        return db.fetchone("SELECT * FROM encounters WHERE id=?", (self.encounter_id,))

    def current(self) -> dict | None:
        enc = self.encounter()
        combatants = self.combatants()
        if not enc or not combatants:
            return None
        return combatants[enc["current_turn"] % len(combatants)]

    def build_embed(self) -> discord.Embed:
        enc = self.encounter()
        combatants = self.combatants()
        cur = self.current()
        embed = discord.Embed(title=f"⚔️  {enc['name']}", colour=0xCC2222)
        embed.add_field(name="Round",  value=str(enc["round"]),        inline=True)
        embed.add_field(name="Status", value=enc["status"].title(),    inline=True)

        lines = []
        for c in combatants:
            conditions = json.loads(c.get("conditions") or "[]")
            cond_str   = f" *[{', '.join(conditions)}]*" if conditions else ""
            hp, max_hp = c["hp"], c["max_hp"]
            bar  = "█" * round((hp / max_hp) * 10 if max_hp else 0)
            bar += "░" * (10 - len(bar))
            arrow = "▶ " if cur and c["id"] == cur["id"] else "   "
            name  = f"**{c['name']}**" if cur and c["id"] == cur["id"] else c["name"]
            lines.append(f"{arrow}{name} — HP {hp}/{max_hp} `{bar}` AC {c['ac']}{cond_str}")
            if c.get("notes"):
                lines.append(f"      *{c['notes']}*")
        for c in self.fallen():
            lines.append(f"   ~~{c['name']}~~ 💀")

        embed.add_field(name="Initiative Order", value="\n".join(lines) or "_No combatants_", inline=False)
        if cur:
            embed.set_footer(text=f"Current: {cur['name']} · Initiative {cur['initiative']}")
        return embed


class CombatCog(commands.Cog, name="Combat"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    combat_group = app_commands.Group(name="combat", description="Combat tracker")

    async def _refresh(self, tracker: _Tracker):
        try:
            await tracker.player_message.edit(embed=tracker.build_embed())
        except discord.NotFound:
            _active.pop(tracker.guild_id, None)

    @combat_group.command(name="start", description="Start a combat encounter")
    @dm_only()
    async def combat_start(self, interaction: discord.Interaction, encounter_id: int):
        gid = interaction.guild.id
        if gid in _active:
            await interaction.response.send_message("Combat already running. Use /combat end first.", ephemeral=True)
            return
        enc = db.fetchone("SELECT * FROM encounters WHERE id=?", (encounter_id,))
        if not enc:
            await interaction.response.send_message(f"No encounter {encounter_id}.", ephemeral=True)
            return
        db.execute("UPDATE encounters SET status='active', round=1, current_turn=0 WHERE id=?", (encounter_id,))
        player_channel_id = config.get_key(gid, "player_channel_id")
        target = interaction.guild.get_channel(int(player_channel_id)) if player_channel_id else interaction.channel
        await interaction.response.defer(ephemeral=True)
        msg = await target.send(embed=discord.Embed(title="Preparing combat…", colour=0xCC2222))
        tracker = _Tracker(encounter_id, gid, msg)
        _active[gid] = tracker
        await self._refresh(tracker)

        vc_id = config.get_key(gid, "voice_channel_id")
        if vc_id:
            vc_channel = interaction.guild.get_channel(int(vc_id))
            if vc_channel:
                try:
                    existing = interaction.guild.voice_client
                    if existing:
                        await existing.move_to(vc_channel)
                        tracker.vc = existing
                    else:
                        tracker.vc = await vc_channel.connect()
                    cur = tracker.current()
                    name = cur["name"] if cur else "unknown"
                    enc_name = enc["name"]
                    await _speak(tracker.vc, f"Combat has begun. {enc_name}. {name} goes first.")
                except Exception:
                    pass

        await interaction.followup.send(f"Combat started in {target.mention}.", ephemeral=True)

    @combat_group.command(name="next", description="Advance to the next turn")
    @dm_only()
    async def combat_next(self, interaction: discord.Interaction):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        enc = tracker.encounter()
        combatants = tracker.combatants()
        next_turn = enc["current_turn"] + 1
        next_round = enc["round"]
        if next_turn >= len(combatants):
            next_turn = 0
            next_round += 1
        db.execute("UPDATE encounters SET current_turn=?, round=? WHERE id=?",
                   (next_turn, next_round, tracker.encounter_id))
        await self._refresh(tracker)
        cur = tracker.current()
        await interaction.response.send_message(f"→ **{cur['name'] if cur else '?'}**", ephemeral=True)
        if cur and tracker.vc:
            enc = tracker.encounter()
            await _speak(tracker.vc, f"{cur['name']}, round {enc['round']}.")

    @combat_group.command(name="hp", description="Adjust HP (+heal, -damage)")
    @dm_only()
    async def combat_hp(self, interaction: discord.Interaction, name: str, delta: int):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        row = db.fetchone(
            "SELECT id,hp,max_hp,name FROM combatants WHERE encounter_id=? AND name LIKE ? AND is_active=1",
            (tracker.encounter_id, f"%{name}%"),
        )
        if not row:
            await interaction.response.send_message(f"No combatant matching '{name}'.", ephemeral=True)
            return
        new_hp = max(0, min(row["hp"] + delta, row["max_hp"]))
        db.execute("UPDATE combatants SET hp=? WHERE id=?", (new_hp, row["id"]))
        await self._refresh(tracker)
        sign = f"+{delta}" if delta >= 0 else str(delta)
        await interaction.response.send_message(
            f"**{row['name']}** {row['hp']} → {new_hp} ({sign})", ephemeral=True
        )

    @combat_group.command(name="add", description="Add a combatant mid-fight")
    @dm_only()
    async def combat_add(
        self,
        interaction: discord.Interaction,
        name: str,
        hp: int,
        ac: int = 10,
        initiative: int = 0,
        combatant_type: str = "monster",
    ):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        db.execute(
            "INSERT INTO combatants (encounter_id,name,combatant_type,initiative,hp,max_hp,ac,conditions,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (tracker.encounter_id, name, combatant_type, initiative, hp, hp, ac, "[]", ""),
        )
        await self._refresh(tracker)
        await interaction.response.send_message(f"Added **{name}** (HP {hp}, AC {ac}).", ephemeral=True)

    @combat_group.command(name="condition", description="Apply or remove a condition")
    @app_commands.choices(condition=_CONDITION_CHOICES)
    @dm_only()
    async def combat_condition(
        self,
        interaction: discord.Interaction,
        name: str,
        condition: str,
        remove: bool = False,
    ):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        row = db.fetchone(
            "SELECT id,name,conditions FROM combatants WHERE encounter_id=? AND name LIKE ? AND is_active=1",
            (tracker.encounter_id, f"%{name}%"),
        )
        if not row:
            await interaction.response.send_message(f"No combatant matching '{name}'.", ephemeral=True)
            return
        conditions = json.loads(row.get("conditions") or "[]")
        if remove:
            conditions = [c for c in conditions if c.lower() != condition.lower()]
            verb = "Removed"
        else:
            if condition not in conditions:
                conditions.append(condition)
            verb = "Applied"
        db.execute("UPDATE combatants SET conditions=? WHERE id=?", (json.dumps(conditions), row["id"]))
        await self._refresh(tracker)
        await interaction.response.send_message(f"{verb} **{condition}** on {row['name']}.", ephemeral=True)

    @combat_group.command(name="notes", description="Set notes for a combatant")
    @dm_only()
    async def combat_notes(self, interaction: discord.Interaction, name: str, notes: str):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        row = db.fetchone(
            "SELECT id,name FROM combatants WHERE encounter_id=? AND name LIKE ? AND is_active=1",
            (tracker.encounter_id, f"%{name}%"),
        )
        if not row:
            await interaction.response.send_message(f"No combatant matching '{name}'.", ephemeral=True)
            return
        db.execute("UPDATE combatants SET notes=? WHERE id=?", (notes, row["id"]))
        await self._refresh(tracker)
        await interaction.response.send_message(f"Notes updated for **{row['name']}**.", ephemeral=True)

    @combat_group.command(name="remove", description="Remove a combatant (defeated)")
    @dm_only()
    async def combat_remove(self, interaction: discord.Interaction, name: str):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        row = db.fetchone(
            "SELECT id,name FROM combatants WHERE encounter_id=? AND name LIKE ? AND is_active=1",
            (tracker.encounter_id, f"%{name}%"),
        )
        if not row:
            await interaction.response.send_message(f"No combatant matching '{name}'.", ephemeral=True)
            return
        db.execute("UPDATE combatants SET is_active=0, hp=0 WHERE id=?", (row["id"],))
        await self._refresh(tracker)
        await interaction.response.send_message(f"**{row['name']}** removed.", ephemeral=True)

    @combat_group.command(name="status", description="Show current tracker (DM only)")
    @dm_only()
    async def combat_status(self, interaction: discord.Interaction):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        await interaction.response.send_message(embed=tracker.build_embed(), ephemeral=True)

    @combat_group.command(name="end", description="End the current combat")
    @dm_only()
    async def combat_end(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        tracker = _active.get(gid)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        enc = tracker.encounter()
        fallen = tracker.fallen()
        db.execute("UPDATE encounters SET status='completed' WHERE id=?", (tracker.encounter_id,))
        final = tracker.build_embed()
        final.title = f"✅  {enc['name']} — Completed"
        final.colour = 0x44AA44
        summary_parts = [f"**{enc['round']}** round{'s' if enc['round'] != 1 else ''}"]
        if fallen:
            names = ", ".join(c["name"] for c in fallen)
            summary_parts.append(f"Fallen: {names}")
        final.add_field(name="Battle Summary", value=" · ".join(summary_parts), inline=False)
        await tracker.player_message.edit(embed=final)
        if tracker.vc:
            await _speak(tracker.vc, "Combat over.")
            await asyncio.sleep(3)
            try:
                await tracker.vc.disconnect()
            except Exception:
                pass
        _active.pop(gid, None)
        await interaction.response.send_message("Combat ended.", ephemeral=True)

    @combat_group.command(name="initiative", description="Override a combatant's initiative score")
    @dm_only()
    async def combat_initiative(self, interaction: discord.Interaction, name: str, value: int):
        tracker = _active.get(interaction.guild.id)
        if not tracker:
            await interaction.response.send_message("No active combat.", ephemeral=True)
            return
        row = db.fetchone(
            "SELECT id,name FROM combatants WHERE encounter_id=? AND name LIKE ? AND is_active=1",
            (tracker.encounter_id, f"%{name}%"),
        )
        if not row:
            await interaction.response.send_message(f"No combatant matching '{name}'.", ephemeral=True)
            return
        db.execute("UPDATE combatants SET initiative=? WHERE id=?", (value, row["id"]))
        await self._refresh(tracker)
        await interaction.response.send_message(
            f"**{row['name']}** initiative set to {value}.", ephemeral=True
        )

    # ── Session recaps ────────────────────────────────────────────────────────

    session_group = app_commands.Group(name="session", description="Session notes")

    @session_group.command(name="log", description="Log a session recap and post to the player channel")
    @dm_only()
    async def session_log(self, interaction: discord.Interaction, title: str, notes: str):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        lore_id = db.execute(
            "INSERT INTO lore (campaign_id,title,content,lore_type) VALUES (?,?,?,?)",
            (cid, title, notes, "session"),
        )
        player_channel_id = config.get_key(interaction.guild.id, "player_channel_id")
        target = interaction.guild.get_channel(int(player_channel_id)) if player_channel_id else interaction.channel
        embed = discord.Embed(title=f"Session Recap — {title}", description=notes[:4096], colour=0x7060A0)
        embed.set_footer(text=f"Session log ID {lore_id}")
        await target.send(embed=embed)
        await interaction.response.send_message(f"Recap posted to {target.mention}.", ephemeral=True)

    @session_group.command(name="history", description="Show recent session recaps")
    async def session_history(self, interaction: discord.Interaction, limit: int = 5):
        cid = config.get_key(interaction.guild.id, "active_campaign_id")
        if not cid:
            await interaction.response.send_message("No active campaign.", ephemeral=True)
            return
        rows = db.fetchall(
            "SELECT id,title,content,created_at FROM lore WHERE campaign_id=? AND lore_type='session' ORDER BY id DESC LIMIT ?",
            (cid, min(limit, 10)),
        )
        if not rows:
            await interaction.response.send_message("No session logs yet.", ephemeral=True)
            return
        embed = discord.Embed(title="Session History", colour=0x7060A0)
        for r in rows:
            preview = (r["content"] or "")[:200]
            if len(r["content"] or "") > 200:
                preview += "…"
            embed.add_field(
                name=f"[{r['id']}] {r['title']} · {r['created_at'][:10]}",
                value=preview or "_no notes_",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CombatCog(bot))
