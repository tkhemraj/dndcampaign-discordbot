# D&D Campaign Discord Bot

A fully standalone Discord bot companion for Dungeon Masters running campaigns in **Wildemount** (Critical Role setting). Live combat tracker with HP bars and conditions, procedural NPC/quest/map generation, voice channel turn announcements, and deploy notifications — all from Discord slash commands.

[![Add to Discord](https://img.shields.io/badge/Add%20to-Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/api/oauth2/authorize?client_id=1507476166494392420&permissions=117760&scope=bot%20applications.commands)
[![Live Demo](https://img.shields.io/badge/Live-Demo-7289da?logo=github)](https://tkhemraj.github.io/dndcampaign-discordbot/demo.html)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

---

## How it looks in Discord

### Live Combat Tracker
The DM controls combat privately. Players see a live embed that updates every turn — HP bars, conditions, and initiative order refresh silently without cluttering the channel.

![Combat Tracker](docs/img/combat_tracker.png)

### NPC Generator
Every NPC is fully statted with Wildemount lore — race, class, faction, ability scores, personality, ideals, flaws, and a backstory seeded to the setting. Replies are ephemeral (DM-only).

![NPC Generator](docs/img/npc_generator.png)

### Procedural Maps
BSP dungeon rooms, zone-based outdoor terrain, template interiors, and Wildemount-flavoured locations rendered as PNG — generated fresh every time, posted to the player channel with `/map share`.

![Procedural Map](docs/img/map_preview.png)

### Voice Channel Announcements
Configure a voice channel with `/setup voice_channel` and the bot joins automatically when combat starts — speaking each turn by name so nobody misses their go while the DM is narrating. Disconnects when combat ends.

![Voice Channel](docs/img/voice_channel.png)

> **[→ See the full interactive demo](https://tkhemraj.github.io/dndcampaign-discordbot/demo.html)**

---

## Features

| Feature | Commands | Who sees it |
|---|---|---|
| **Live combat tracker** | `/combat start/next/hp/end` | DM controls privately; players see live embed |
| **Voice turn announcements** | `/setup voice_channel` | Bot joins VC on combat start, announces each turn via TTS, disconnects on end |
| **Deploy announcements** | automatic | Posts a green embed to player channel on every restart — shows commit SHA and what changed |
| **NPC generation** | `/npc generate` | DM only (ephemeral) — fully statted, Wildemount lore |
| **Quest board** | `/quest generate`, `/quest board` | DM generates; board posts to player channel |
| **Procedural maps** | `/map generate`, `/map share` | DM previews privately; share posts PNG to channel |
| **Session recaps** | `/session log` | Posts rich embed to player channel |
| **Encounter builder** | `/encounter generate` | DM only (ephemeral) |
| **Multi-campaign** | `/campaign new/select` | Multiple campaigns per server |

**Map types:** `dungeon` · `outdoor` · `interior` · `wildemount`  
**Dungeon subtypes:** `generic` · `underdark` · `crypt` · `sewers` · `cerberus_lab` · `bazzoxan`

---

## Quick start

```bash
git clone https://github.com/tkhemraj/dndcampaign-discordbot
cd dndcampaign-discordbot
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your DISCORD_TOKEN
python run.py
```

Or deploy to Railway in one click — see [`Procfile`](Procfile) and [`nixpacks.toml`](nixpacks.toml).

---

## First-time server setup

Run these as the DM after adding the bot:

```
/setup role           @Dungeon Master       ← grants DM commands via role
/setup dm_channel     #dm-commands         ← OR restrict by channel
/setup player_channel #session-log         ← where the bot posts public updates
/setup voice_channel  #General             ← optional: VC for combat TTS announcements
/campaign new         "The Wildemount War" ← creates and activates a campaign
/setup status                              ← confirm everything is wired up
```

---

## DM access control

A user is treated as the DM if **either** is true:
1. They have the configured DM role (`/setup role`)
2. They are posting in the configured DM channel (`/setup dm_channel`)

Both gates can be active simultaneously — useful for having a `#dm-commands` channel AND a DM role on shared servers. All DM commands reply ephemerally so players never see them.

---

## Full command reference

<details>
<summary>Campaign</summary>

| Command | Description |
|---|---|
| `/campaign new <name>` | Create a new campaign |
| `/campaign select <id>` | Switch active campaign |
| `/campaign list` | List all campaigns |
| `/campaign info` | Show active campaign stats |

</details>

<details>
<summary>Generate</summary>

| Command | Description |
|---|---|
| `/npc generate [region] [faction]` | Generate + save a fully statted NPC (ephemeral) |
| `/npc list [status]` | List saved NPCs |
| `/quest generate [region] [faction]` | Generate + save a quest hook (ephemeral) |
| `/quest board` | Post all active quests → player channel |
| `/encounter generate [size] [level] [difficulty]` | Generate + save an encounter |

</details>

<details>
<summary>Maps</summary>

| Command | Description |
|---|---|
| `/map generate [type] [subtype]` | Generate a map — PNG preview (ephemeral) |
| `/map share [map_id]` | Post the map → player channel |
| `/map list` | List saved maps |

</details>

<details>
<summary>Combat</summary>

| Command | Description |
|---|---|
| `/combat start <encounter_id>` | Start combat — posts live embed to player channel |
| `/combat next` | Advance turn (embed updates live) |
| `/combat hp <name> <delta>` | Heal or damage (`+5`, `-12`) |
| `/combat add <name> <hp> [ac] [initiative]` | Add combatant mid-fight |
| `/combat condition <name> <condition>` | Apply/remove a condition |
| `/combat notes <name> <notes>` | Set combatant notes |
| `/combat remove <name>` | Remove a combatant |
| `/combat status` | View tracker privately |
| `/combat end` | End combat (embed turns green) |

</details>

<details>
<summary>Session</summary>

| Command | Description |
|---|---|
| `/session log <title> <notes>` | Post session recap → player channel |
| `/session history [limit]` | Show recent session recaps |

</details>

<details>
<summary>Setup</summary>

| Command | Description |
|---|---|
| `/setup role <role>` | Set the DM role |
| `/setup dm_channel <channel>` | Set the DM-only text channel |
| `/setup player_channel <channel>` | Set the player text channel |
| `/setup voice_channel <channel>` | Set the voice channel for combat TTS announcements |
| `/setup status` | Show current configuration |

</details>

---

## Database modes

| Mode | Env var | Description |
|---|---|---|
| **Standalone** (default) | `USE_SHARED_DB=0` | Bot uses its own `campaign.db` |
| **Shared** | `USE_SHARED_DB=1` | Reads `../dndcampaign/dndcampaign.db` — synced with the [companion web app](https://github.com/tkhemraj/dndcampaign) |
