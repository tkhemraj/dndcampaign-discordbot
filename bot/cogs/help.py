"""Help system and guided setup wizard for non-technical DMs."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from bot import config, db


# ── Help categories ───────────────────────────────────────────────────────────

_HELP = {
    "🚀 Getting Started": {
        "desc": "The five things to do after the bot joins your server.",
        "fields": [
            ("1. Set your DM role", "`/setup role @YourRole` — only this role can run DM commands"),
            ("2. Set the player channel", "`/setup player_channel #channel` — where the bot posts maps, quests, combat"),
            ("3. Create a campaign", "`/campaign new The Wildemount War` — names and activates your campaign"),
            ("4. Invite your players", "Players can register their characters with `/pc register`"),
            ("5. Guided setup", "Run `/quickstart` for a step-by-step wizard instead"),
        ],
        "colour": 0x44AA44,
    },
    "⚔️ Combat": {
        "desc": "Run live combat encounters. The tracker updates silently in the player channel.",
        "fields": [
            ("/encounter generate", "Build a balanced encounter for your party size and level"),
            ("/combat start [id]", "Start combat — posts the live tracker to the player channel"),
            ("/combat next", "Advance to the next turn"),
            ("/combat hp [name] [±amount]", "Heal or damage a combatant — e.g. `/combat hp Goblin -8`"),
            ("/combat condition [name] [condition]", "Apply a condition like Poisoned, Stunned, Prone"),
            ("/combat end", "End combat — tracker turns green with a battle summary"),
            ("Autopilot", "`/setup dm_mode auto` — bot handles monster turns; you just narrate"),
        ],
        "colour": 0xCC2222,
    },
    "🧙 NPCs & Quests": {
        "desc": "Generate characters and story hooks on the fly.",
        "fields": [
            ("/npc generate", "Create a fully-statted Wildemount NPC (only you see it)"),
            ("/npc library", "Browse 185 hand-crafted characters — filter by tier or region"),
            ("/npc summon [name]", "Add a library NPC to your campaign with fresh stats"),
            ("/npc speak [id] [question]", "Ask an NPC a question — AI reply posts to the player channel"),
            ("/npc list", "See all your NPCs — filter by alive / dead"),
            ("/quest generate", "Create a quest hook with faction flavour"),
            ("/quest board", "Post all active quests to the player channel"),
            ("/quest complete [id]", "Mark a quest done"),
        ],
        "colour": 0xD4A040,
    },
    "🗺️ Maps": {
        "desc": "Generate procedural maps and post them to your players.",
        "fields": [
            ("/map generate [type]", "Generate a map — dungeon, outdoor, interior, or wildemount location"),
            ("/map generate dungeon [subtype]", "Dungeon subtypes: generic · underdark · crypt · sewers · cerberus_lab · bazzoxan"),
            ("/map share [id]", "Post the map to the player channel"),
            ("/map list", "See recent maps with their IDs"),
        ],
        "colour": 0x336699,
    },
    "🧝 Player Characters": {
        "desc": "Players register their own characters. They auto-join combat with correct stats.",
        "fields": [
            ("/pc register [name]", "Register your character — set HP, AC, race, class, stats"),
            ("/pc view", "See your character sheet with HP bar and spell slots"),
            ("/pc hp [±amount]", "Update your HP — e.g. `/pc hp -12` after taking damage"),
            ("/pc cast [slot level]", "Expend a spell slot"),
            ("/pc rest", "Long rest — resets HP and refills all spell slots"),
            ("/pc list", "DM: see all registered characters in the active campaign"),
        ],
        "colour": 0x8844CC,
    },
    "🌍 World Events": {
        "desc": "Keep the world alive between fights. Fire events manually or run on a timer.",
        "fields": [
            ("/event fire [type]", "Trigger an event now — weather, rumour, faction, discovery, omen, encounter"),
            ("/event preview [type]", "See an event privately before deciding to share it"),
            ("/setup event_mode auto", "Bot fires ambient events every 20 minutes automatically"),
            ("/setup event_interval [minutes]", "Change how often auto events fire"),
            ("/setup event_dm_only", "Events go to DM channel first so you decide what to narrate"),
        ],
        "colour": 0x44AA88,
    },
    "🎲 Dice & Loot": {
        "desc": "Dice roller for the whole table. Loot generator for treasure rewards.",
        "fields": [
            ("/roll [expression]", "Roll dice — `1d20+5`, `2d6`, `4d6kh3` (keep highest 3)"),
            ("/roll [expression] secret:True", "Secret roll — only you see the result"),
            ("/roll 1d20 adv", "Roll with advantage (rolls twice, takes higher)"),
            ("/loot generate [cr]", "Generate CR-appropriate treasure with magic items"),
            ("/loot share [id]", "Post the loot card to the player channel"),
        ],
        "colour": 0xCCAA22,
    },
    "⚙️ Setup & Config": {
        "desc": "Configure channels, roles, and automation modes.",
        "fields": [
            ("/setup role @role", "Set the Dungeon Master role"),
            ("/setup player_channel #channel", "Where the bot posts public updates"),
            ("/setup dm_channel #channel", "Optional: restrict DM commands to one channel"),
            ("/setup voice_channel #vc", "Voice channel for combat turn announcements"),
            ("/setup status", "Show everything that's configured"),
            ("/setup dm_mode [auto|manual]", "Autopilot combat on/off"),
            ("/setup player_mode [open|managed]", "Player action buttons on/off"),
        ],
        "colour": 0x888888,
    },
}


def _help_embed(category: str) -> discord.Embed:
    data   = _HELP[category]
    embed  = discord.Embed(
        title=category,
        description=data["desc"],
        colour=data["colour"],
    )
    for name, value in data["fields"]:
        embed.add_field(name=name, value=value, inline=False)
    embed.set_footer(text="Use /quickstart for guided first-time setup · /help to browse commands")
    return embed


class HelpCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, description=_HELP[cat]["desc"][:100])
            for cat in _HELP
        ]
        super().__init__(placeholder="Choose a topic…", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        embed = _help_embed(self.values[0])
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(HelpCategorySelect())


# ── Quickstart wizard ─────────────────────────────────────────────────────────

def _wizard_embed(step: int, state: dict) -> discord.Embed:
    steps = ["DM Role", "Player Channel", "Campaign", "Done"]
    prog  = " → ".join(
        f"**{s}**" if i == step - 1 else s
        for i, s in enumerate(steps)
    )
    if step == 0:
        embed = discord.Embed(
            title="🎲 Welcome to CampaignBot!",
            description=(
                "Let's get your server set up in **4 quick steps**.\n\n"
                "You can skip any step and configure it later with `/setup status`."
            ),
            colour=0x44AA44,
        )
        embed.add_field(
            name="What you'll set up",
            value="• **DM Role** — who can run DM commands\n"
                  "• **Player Channel** — where the bot posts public updates\n"
                  "• **Campaign** — your first campaign",
            inline=False,
        )
    elif step == 1:
        embed = discord.Embed(
            title="Step 1 of 3 — DM Role",
            description=(
                "Which role should have **Dungeon Master access**?\n\n"
                "People with this role can use `/npc`, `/combat`, `/map`, and other DM commands. "
                "Players never see those commands."
            ),
            colour=0xD4A040,
        )
        embed.set_footer(text=prog)
    elif step == 2:
        role_set = "✅ DM Role set" if state.get("dm_role_id") else "⬜ DM Role skipped"
        embed = discord.Embed(
            title="Step 2 of 3 — Player Channel",
            description=(
                "Which channel should the bot use to **post updates players can see**?\n\n"
                "Combat trackers, maps, quest boards, and session recaps will all appear here."
            ),
            colour=0xD4A040,
        )
        embed.set_footer(text=f"{role_set} · {prog}")
    elif step == 3:
        role_set = "✅ DM Role set" if state.get("dm_role_id") else "⬜ DM Role skipped"
        ch_set   = "✅ Player channel set" if state.get("player_channel_id") else "⬜ Player channel skipped"
        embed = discord.Embed(
            title="Step 3 of 3 — Campaign Name",
            description=(
                "What's your **campaign called**?\n\n"
                "You can have multiple campaigns per server and switch between them. "
                "This creates your first one."
            ),
            colour=0xD4A040,
        )
        embed.set_footer(text=f"{role_set} · {ch_set} · {prog}")
    else:  # done
        lines = []
        if state.get("dm_role_id"):
            lines.append("✅ DM Role configured")
        else:
            lines.append("⬜ DM Role — use `/setup role @role` to set later")
        if state.get("player_channel_id"):
            lines.append("✅ Player channel configured")
        else:
            lines.append("⬜ Player channel — use `/setup player_channel #channel` to set later")
        if state.get("campaign_name"):
            lines.append(f"✅ Campaign **{state['campaign_name']}** created")
        else:
            lines.append("⬜ Campaign — use `/campaign new [name]` to create later")
        embed = discord.Embed(
            title="✅ Setup complete!",
            description="\n".join(lines),
            colour=0x44AA44,
        )
        embed.add_field(
            name="What to try next",
            value=(
                "`/npc generate` — create your first NPC\n"
                "`/encounter generate` — build a combat encounter\n"
                "`/event fire` — generate an ambient world event\n"
                "`/help` — browse all commands by category"
            ),
            inline=False,
        )
    return embed


class SetupWizardView(discord.ui.View):
    def __init__(self, guild_id: int, bot: commands.Bot, initial_step: int = 0):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.bot      = bot
        self.state: dict = {}
        self._build_step(initial_step)

    def _build_step(self, step: int) -> None:
        self.step = step
        self.clear_items()

        if step == 0:
            btn = discord.ui.Button(label="Start Setup →", style=discord.ButtonStyle.success)
            btn.callback = self._go_step1
            self.add_item(btn)

        elif step == 1:
            sel = discord.ui.RoleSelect(placeholder="Select DM role…", min_values=1, max_values=1)
            sel.callback = self._set_role
            self.add_item(sel)
            skip = discord.ui.Button(label="Skip →", style=discord.ButtonStyle.secondary)
            skip.callback = self._skip_to_2
            self.add_item(skip)

        elif step == 2:
            sel = discord.ui.ChannelSelect(
                placeholder="Select player channel…",
                min_values=1,
                max_values=1,
                channel_types=[discord.ChannelType.text],
            )
            sel.callback = self._set_channel
            self.add_item(sel)
            skip = discord.ui.Button(label="Skip →", style=discord.ButtonStyle.secondary)
            skip.callback = self._skip_to_3
            self.add_item(skip)

        elif step == 3:
            btn = discord.ui.Button(label="✏️ Name my campaign", style=discord.ButtonStyle.primary)
            btn.callback = self._open_campaign_modal
            self.add_item(btn)
            skip = discord.ui.Button(label="Skip", style=discord.ButtonStyle.secondary)
            skip.callback = self._skip_to_done
            self.add_item(skip)

    async def _go_step1(self, interaction: discord.Interaction) -> None:
        self._build_step(1)
        await interaction.response.edit_message(embed=_wizard_embed(1, self.state), view=self)

    async def _set_role(self, interaction: discord.Interaction) -> None:
        role = interaction.data["values"][0]
        config.set_key(self.guild_id, "dm_role_id", int(role))
        self.state["dm_role_id"] = int(role)
        self._build_step(2)
        await interaction.response.edit_message(embed=_wizard_embed(2, self.state), view=self)

    async def _skip_to_2(self, interaction: discord.Interaction) -> None:
        self._build_step(2)
        await interaction.response.edit_message(embed=_wizard_embed(2, self.state), view=self)

    async def _set_channel(self, interaction: discord.Interaction) -> None:
        ch_id = int(interaction.data["values"][0])
        config.set_key(self.guild_id, "player_channel_id", ch_id)
        self.state["player_channel_id"] = ch_id
        self._build_step(3)
        await interaction.response.edit_message(embed=_wizard_embed(3, self.state), view=self)

    async def _skip_to_3(self, interaction: discord.Interaction) -> None:
        self._build_step(3)
        await interaction.response.edit_message(embed=_wizard_embed(3, self.state), view=self)

    async def _open_campaign_modal(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_CampaignModal(self))

    async def _skip_to_done(self, interaction: discord.Interaction) -> None:
        self._build_step(4)
        await interaction.response.edit_message(embed=_wizard_embed(4, self.state), view=self)
        self.stop()

    async def finish(self, interaction: discord.Interaction, campaign_name: str) -> None:
        self.state["campaign_name"] = campaign_name
        self._build_step(4)
        await interaction.response.edit_message(embed=_wizard_embed(4, self.state), view=self)
        self.stop()


class _CampaignModal(discord.ui.Modal, title="Create Campaign"):
    name = discord.ui.TextInput(
        label="Campaign Name",
        placeholder="e.g. The Wildemount War",
        max_length=100,
    )
    setting = discord.ui.TextInput(
        label="Setting",
        placeholder="e.g. Wildemount",
        default="Wildemount",
        required=False,
        max_length=80,
    )

    def __init__(self, wizard: SetupWizardView):
        super().__init__()
        self.wizard = wizard

    async def on_submit(self, interaction: discord.Interaction) -> None:
        cid = db.execute(
            "INSERT INTO campaigns (name, setting, description) VALUES (?,?,?)",
            (self.name.value, self.setting.value or "Wildemount", ""),
        )
        config.set_key(self.wizard.guild_id, "active_campaign_id", cid)
        await self.wizard.finish(interaction, self.name.value)


# ── Cog ───────────────────────────────────────────────────────────────────────

class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Post a welcome message when the bot joins a new server."""
        embed = discord.Embed(
            title="👋 CampaignBot has arrived!",
            description=(
                "I'm a D&D campaign companion for Dungeon Masters.\n\n"
                "**To get started:** use `/quickstart` for a step-by-step setup wizard, "
                "or `/help` to browse all commands.\n\n"
                "The DM needs to run `/quickstart` — it takes about 2 minutes."
            ),
            colour=0x44AA44,
        )
        embed.add_field(
            name="Quick setup",
            value=(
                "`/quickstart` — guided wizard\n"
                "`/setup role @role` — set who is the DM\n"
                "`/setup player_channel #channel` — where the bot posts\n"
                "`/campaign new [name]` — create your first campaign"
            ),
            inline=False,
        )
        embed.set_footer(text="All DM commands are hidden from players. Use /help to explore.")

        # Try system channel first, then first writeable text channel
        target = guild.system_channel
        if target is None:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    target = ch
                    break

        if target:
            try:
                await target.send(embed=embed)
            except Exception:
                pass

    @app_commands.command(name="help", description="Browse all bot commands by category")
    async def help_cmd(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="CampaignBot — Command Reference",
            description="Select a category below to browse commands.",
            colour=0xD4A040,
        )
        embed.add_field(
            name="Quick links",
            value=(
                "🚀 **Getting Started** — first-time setup\n"
                "⚔️ **Combat** — tracker, autopilot, turns\n"
                "🧙 **NPCs & Quests** — generation + library\n"
                "🗺️ **Maps** — procedural map generation\n"
                "🧝 **Player Characters** — registration, HP, spells\n"
                "🌍 **World Events** — ambient events\n"
                "🎲 **Dice & Loot** — rolling and treasure\n"
                "⚙️ **Setup & Config** — channels, roles, modes"
            ),
            inline=False,
        )
        embed.set_footer(text="Use /quickstart for guided first-time setup")
        await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)

    @app_commands.command(name="quickstart", description="Guided setup wizard — takes 2 minutes")
    async def quickstart(self, interaction: discord.Interaction) -> None:
        embed = _wizard_embed(0, {})
        view  = SetupWizardView(interaction.guild.id, self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
