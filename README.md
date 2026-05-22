# D&D Campaign Discord Bot

A fully standalone Discord bot companion for the [D&D Campaign Generator](https://github.com/tkhemraj/dndcampaign).

Players and the DM see different things — the DM gets ephemeral (private) responses while session recaps, quest boards, combat trackers, and maps are posted live to a designated player channel.

---

## Add to your Discord server

> **Replace `YOUR_CLIENT_ID` with your bot's Application ID from the [Discord Developer Portal](https://discord.com/developers/applications).**

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=84992&scope=bot%20applications.commands
```

**Or paste this badge into your own README after filling in the ID:**

```markdown
[![Add to Discord](https://img.shields.io/badge/Add%20to-Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=84992&scope=bot%20applications.commands)
```

The permission integer `84992` grants: **View Channels + Send Messages + Embed Links + Attach Files + Read Message History** — the minimum needed for the bot to function.

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

---

## First-time server setup (DM runs these)

```
/setup role      @Dungeon Master       ← grants DM commands via role
/setup dm_channel #dm-commands         ← OR restrict by channel (either works)
/setup player_channel #session-log     ← where the bot posts public updates
/campaign new    "The Wildemount War"  ← creates and activates a campaign
/setup status                          ← confirm everything looks right
```

---

## Command reference

### Campaign
| Command | Who | Description |
|---|---|---|
| `/campaign new <name>` | DM | Create a campaign |
| `/campaign select <id>` | DM | Switch active campaign |
| `/campaign list` | DM | List all campaigns |
| `/campaign info` | Anyone | Show active campaign stats |

### Generate
| Command | Who | Description |
|---|---|---|
| `/npc generate [region] [faction]` | DM | Generate + save an NPC (ephemeral) |
| `/npc list [status]` | Anyone | List NPCs |
| `/quest generate [region] [faction]` | DM | Generate + save a quest (ephemeral) |
| `/quest board` | DM | Post all active quests → player channel |
| `/encounter generate [size] [level] [difficulty]` | DM | Generate + save an encounter |

### Maps
| Command | Who | Description |
|---|---|---|
| `/map generate [type] [subtype]` | DM | Generate a map — PNG preview (ephemeral) |
| `/map share [map_id]` | DM | Post the map → player channel |
| `/map list` | DM | List saved maps |

**Map types:** `dungeon`, `outdoor`, `interior`, `wildemount`

### Combat
| Command | Who | Description |
|---|---|---|
| `/combat start <encounter_id>` | DM | Start combat — posts live embed to player channel |
| `/combat next` | DM | Advance turn (embed updates live) |
| `/combat hp <name> <delta>` | DM | Heal or damage (`+5`, `-12`) |
| `/combat add <name> <hp> [ac] [initiative]` | DM | Add combatant mid-fight |
| `/combat condition <name> <condition> [remove]` | DM | Apply/remove a condition |
| `/combat notes <name> <notes>` | DM | Set combatant notes |
| `/combat remove <name>` | DM | Remove defeated combatant |
| `/combat status` | DM | See tracker privately |
| `/combat end` | DM | End combat (embed turns green) |

### Session
| Command | Who | Description |
|---|---|---|
| `/session log <title> <notes>` | DM | Post session recap → player channel |
| `/session history [limit]` | Anyone | Show recent session recaps |

---

## DM access

A user is treated as the DM if **either** is true:
1. They have the configured DM role (`/setup role`)
2. They are posting in the configured DM channel (`/setup dm_channel`)

Both can be active at once — useful for having a dedicated `#dm-commands` channel AND a role for DMs on shared servers.

---

## Database modes

| Mode | Setting | Description |
|---|---|---|
| **Standalone** (default) | `USE_SHARED_DB=0` | Bot keeps its own `campaign.db` — runs independently |
| **Shared** | `USE_SHARED_DB=1` | Reads `../dndcampaign/dndcampaign.db` — synced with the web app |

---

## What players see vs what the DM sees

| Event | Player channel | DM (ephemeral) |
|---|---|---|
| `/quest board` | All active quests posted | Confirmation |
| `/map share` | Map PNG image | Confirmation |
| `/combat start` | Live tracker embed | Confirmation |
| `/combat next/hp/etc.` | Tracker embed updates silently | Confirmation |
| `/combat end` | Tracker turns green | Confirmation |
| `/session log` | Full session recap embed | Confirmation |
| `/npc generate` | — | Full NPC card |
| `/quest generate` | — | Full quest card |
