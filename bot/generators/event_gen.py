"""World event generator — atmospheric, faction, social, and discovery events.

Events are purely narrative prompts the bot posts to give the world a sense
of motion between combat encounters. They require no player input and can be
narrated around, ignored, or expanded by the DM.
"""
from __future__ import annotations
import random
from .data.wildemount import FACTIONS, REGIONS

# ── Event type catalogue ─────────────────────────────────────────────────────

_WEATHER = [
    {
        "title": "Storm Rolling In",
        "desc": "Storm clouds mass on the horizon — dark, fast-moving, and lit from within by occasional lightning. You have perhaps an hour before it breaks.",
        "detail": "Visibility reduced · Difficult terrain (mud/wet) · Duration: 2–6 hours",
        "colour": 0x445566,
    },
    {
        "title": "Unseasonable Fog",
        "desc": "A dense grey fog rolls in without warning, muffling sound and reducing visibility to thirty feet. Shapes at the edge suggest movement that isn't there.",
        "detail": "Visibility 30 ft · Stealth checks at advantage · Duration: until midday",
        "colour": 0x778899,
    },
    {
        "title": "Bitter Cold Snap",
        "desc": "The temperature drops sharply — breath fogs, fingers go numb, and the mud freezes underfoot. A cold front from the Greying Wildlands.",
        "detail": "Extreme cold rules (PHB p.110) · Campfires require twice the fuel · Duration: overnight",
        "colour": 0x99AACC,
    },
    {
        "title": "Ash Fall",
        "desc": "Fine grey ash drifts down from a clear sky, coating everything in a thin layer of grey. The smell is faintly sulphurous. The source is somewhere distant — and difficult.",
        "detail": "Xhorhas/volcanic region flavour · Unsettling but not dangerous · Duration: 1–2 hours",
        "colour": 0x555555,
    },
    {
        "title": "Violent Thunderstorm",
        "desc": "A true storm, not merely rain. Thunder shakes the ground, lightning walks the nearby hills, and wind strong enough to knock a person sideways tears through the area.",
        "detail": "All outdoor travel halted · Ranged attacks impossible · Duration: 3–4 hours",
        "colour": 0x222244,
    },
    {
        "title": "Sudden Clearing",
        "desc": "After days of overcast sky, the clouds part completely. The sun is lower than expected — late afternoon, almost evening. The light makes everything look freshly made.",
        "detail": "Morale boost opportunity · Good time to make camp · Duration: rest of day",
        "colour": 0xDDAA44,
    },
    {
        "title": "Blood Moon Rising",
        "desc": "The moon rises rust-red tonight — a trick of dust in the upper atmosphere, or so they say. The local inn is quieter than usual. Nobody wants to be out.",
        "detail": "Undead activity may be elevated · Good hook for rumour · Duration: one night",
        "colour": 0x882222,
    },
    {
        "title": "Aurora Borealis",
        "desc": "The northern sky blazes with curtains of green and violet light. Locals call it the Luxon's breath — the Dynasty would agree. The Empire considers it a bad omen.",
        "detail": "Wildemount atmospheric event · Faction flavour opportunity · Duration: several hours",
        "colour": 0x44AA88,
    },
]

_RUMOURS = [
    {
        "title": "Overheard at the Inn",
        "source": "A merchant's half-drunk travelling companion",
        "reliability": "Questionable",
        "desc": "\"Three Crown marshals rode through Trostenwald last week — heading east, no livery, no announcement. Someone important doesn't want anyone to know they're in Xhorhas.\"",
        "colour": 0xA07030,
    },
    {
        "title": "A Traveller's Warning",
        "source": "A Cobalt Soul monk heading the opposite direction",
        "reliability": "Credible",
        "desc": "\"Stay off the King's Road past the junction for the next few days. Crown soldiers are searching every cart for something. They're not saying what.\"",
        "colour": 0x336699,
    },
    {
        "title": "Dockside Gossip",
        "source": "A longshoreman between ships",
        "reliability": "Unreliable",
        "desc": "\"The Assembly's got a new tower going up outside Port Damali — built in a week, no local labour hired. Nobody goes in or out. The fishermen won't cast nets near it.\"",
        "colour": 0x664422,
    },
    {
        "title": "The Barkeeper Leans In",
        "source": "Innkeeper, quietly",
        "reliability": "Local knowledge",
        "desc": "\"You didn't hear this from me — but the old Lochward family's been selling off everything they own. Fields, house, the mill. Gone before harvest. I've seen that kind of hurry before.\"",
        "colour": 0x885533,
    },
    {
        "title": "Roadside Rumour",
        "source": "A family of refugees moving west",
        "reliability": "First-hand",
        "desc": "\"There were lights in the ruins east of Brokenveil last night — not campfires, something else. Blue, they said. The whole family left before dawn.\"",
        "colour": 0x334455,
    },
    {
        "title": "A Soldier's Loose Lips",
        "source": "An off-duty Righteous Brand soldier",
        "reliability": "Likely true",
        "desc": "\"Third battalion got recalled early. No explanation, just 'report to Rexxentrum immediately.' Half of us think the Cerberus Assembly found something in Eiselcross and doesn't want anyone talking about it.\"",
        "colour": 0x663333,
    },
    {
        "title": "Kryn Graffiti",
        "source": "Written in Elvish on a bridge pillar",
        "reliability": "Unknown origin",
        "desc": "\"The light remembers what the light destroys.\" Below it, someone has scratched a response in Common: *So do the dead.*",
        "colour": 0x443366,
    },
    {
        "title": "Children's Game",
        "source": "Local children playing near the road",
        "reliability": "Folklore",
        "desc": "The children are playing a game where one hides and the others search — but the one who hides keeps vanishing entirely, not just behind cover. They seem unbothered. The adults nearby look uncomfortable.",
        "colour": 0x667755,
    },
    {
        "title": "A Myriad Message",
        "source": "Slipped under the door at first light",
        "reliability": "Intentional",
        "desc": "A scrap of parchment: three numbers, a location name you've heard, and a symbol you don't recognise. No signature. It could be for someone else — or it could be for you.",
        "colour": 0x444444,
    },
    {
        "title": "Merchant's Warning",
        "source": "A spice trader heading to Zadash",
        "reliability": "First-hand account",
        "desc": "\"Something is off in Shadycreek. Prices have dropped — all the caravans are paying bribes to move through faster. Like people are trying to empty the place out before something happens.\"",
        "colour": 0x886633,
    },
]

_DISCOVERIES = [
    {
        "title": "Abandoned Campsite",
        "desc": "A campsite, clearly used recently — cold fire pit, a torn bedroll, a dented tin cup. Whoever was here left in a hurry. The ground is soft enough to show tracks: two sets heading east, one set that stops abruptly.",
        "significance": "Medium",
        "colour": 0x665544,
    },
    {
        "title": "Ancient Marker Stone",
        "desc": "A standing stone at a crossroads, older than any map you carry. The inscription is in Old Zemnian, partially eroded. What you can make out describes a boundary — and what it was keeping out.",
        "significance": "Lore",
        "colour": 0x556644,
    },
    {
        "title": "Dead Courier",
        "desc": "A rider and horse, both dead, off the road in a thicket. The rider's satchel is intact — the seals unbroken. Whatever killed them didn't care about the mail.",
        "significance": "High — sealed correspondence",
        "colour": 0x443333,
    },
    {
        "title": "Kryn Scouting Cache",
        "desc": "Hidden beneath a false stone near the road: dried provisions for four, a folded map with marks you don't fully understand, and a Luxon prayer bead worn smooth with use.",
        "significance": "Faction intelligence",
        "colour": 0x334455,
    },
    {
        "title": "Collapsed Structure",
        "desc": "The ruins of something — a waystation, perhaps, or a small shrine — collapsed inward as if the ground simply gave way. The stone is scorched from beneath, not from above.",
        "significance": "Possibly a dunamantic incident",
        "colour": 0x554433,
    },
    {
        "title": "Mass Animal Migration",
        "desc": "A large herd of deer, boar, and smaller animals moving together in the same direction — something predators and prey alike are fleeing from, to the east.",
        "significance": "Something large is coming from that direction",
        "colour": 0x557744,
    },
    {
        "title": "Fresh Graves",
        "desc": "Three unmarked graves dug at the roadside, still fresh. No names, no markers, but someone took the time to do it properly. The shovels are still here.",
        "significance": "Someone local knows what happened",
        "colour": 0x444444,
    },
    {
        "title": "A Locked Box",
        "desc": "Half-buried at the base of a distinctive tree — an iron strongbox, good quality, locked with a mechanism you don't recognise. It's heavier than it should be for its size.",
        "significance": "Unknown contents",
        "colour": 0x665522,
    },
    {
        "title": "Strange Tracks",
        "desc": "Tracks that start in the middle of the road and end twenty feet later, as if whatever made them appeared and then vanished. The impressions are deep — it was heavy. The prints are unlike anything you know.",
        "significance": "Mysterious creature or teleportation",
        "colour": 0x445566,
    },
    {
        "title": "A Burned Village",
        "desc": "A hamlet, small — a dozen buildings at most — burned to foundations. Not recently. The weeds are knee-high through the ash. But the well is still intact, and someone has left a fresh flower at its edge.",
        "significance": "Local history, survivor nearby",
        "colour": 0x553322,
    },
]

_FACTION_EVENTS = [
    {
        "title": "Crown Marshal on the Road",
        "faction": "Dwendalian Empire",
        "desc": "A Crown Marshal with two soldiers is making inquiries at the nearest settlement — showing a sketch, asking if anyone has been through recently. The sketch is hard to see clearly from a distance.",
        "mood": "Official, focused",
        "colour": 0x884422,
    },
    {
        "title": "Cerberus Assembly Mages",
        "faction": "Cerberus Assembly",
        "desc": "Two mages in Assembly livery are examining a site nearby — taking measurements, making notes, occasionally casting something that leaves a brief shimmer in the air. They acknowledge you with the minimum courtesy.",
        "mood": "Professional, guarded",
        "colour": 0x442266,
    },
    {
        "title": "Kryn Dynasty Scouts",
        "faction": "Kryn Dynasty",
        "desc": "A pair of Kryn warriors — recognisable by their dark armour and the Luxon symbols at their throats — watch from a ridge for a moment, then melt back into shadow. They didn't attack. They were cataloguing.",
        "mood": "Observing, not hostile",
        "colour": 0x223366,
    },
    {
        "title": "Cobalt Soul Expositor",
        "faction": "Cobalt Soul",
        "desc": "A monk in Cobalt Soul robes sits by the road eating lunch and making notes in a leather-bound journal. They look up, assess you in seconds, and offer a brief but genuine greeting. They're heading somewhere with purpose.",
        "mood": "Friendly, purposeful",
        "colour": 0x224488,
    },
    {
        "title": "Myriad Drop Point",
        "faction": "The Myriad",
        "desc": "A hollow tree at the roadside has been used as a message drop — there's a fresh note inside, sealed. Taking it is theft from the Myriad. Leaving it means whatever it contains reaches its destination.",
        "mood": "Criminal opportunity / risk",
        "colour": 0x333333,
    },
    {
        "title": "Revelry Corsairs Inland",
        "faction": "The Revelry",
        "desc": "Three Revelry pirates — distinctive tattoos, salt-weathered coats — are far from the coast and trying not to be obvious about it. Whatever they're doing inland, it isn't legal.",
        "mood": "Nervous, opportunistic",
        "colour": 0x663300,
    },
    {
        "title": "Righteous Brand Checkpoint",
        "faction": "Dwendalian Empire",
        "desc": "An impromptu military checkpoint on the road: six Righteous Brand soldiers checking papers and searching carts. They're polite but thorough. Nobody is getting through without explaining themselves.",
        "mood": "Professional, tense",
        "colour": 0x882222,
    },
    {
        "title": "Xhorhasian Refugees",
        "faction": "Kryn Dynasty",
        "desc": "A family of Xhorhasian refugees — mixed races, carrying everything they own — asks if the road ahead is clear. They're fleeing something specific, though they're cautious about saying what.",
        "mood": "Frightened, grateful",
        "colour": 0x334455,
    },
]

_OMENS = [
    {
        "title": "Crow Parliament",
        "desc": "A hundred crows sit motionless in the trees along the road, watching in complete silence. As you pass, not one moves. Behind you, they all take flight at once — but you never hear them land again.",
        "colour": 0x222222,
    },
    {
        "title": "Reversed Compass",
        "desc": "For the span of about ten minutes, magnetic compasses point steadily south-west instead of north. Then they correct. No one can explain it. The locals have a name for it: they call it a Possibility Echo.",
        "colour": 0x334455,
    },
    {
        "title": "An Unlocked Door",
        "desc": "A door — freestanding, no walls, no frame around it — stands in the middle of a field. Solid oak, iron hinges, the latch worn smooth. When you open it, there's nothing but the field behind it. When you walk through, you're somewhere exactly three feet to the left of where you should be.",
        "colour": 0x6644AA,
    },
    {
        "title": "Dunamantic Ripple",
        "desc": "A visible shimmer passes through the air, distorting everything for a second — like heat haze, but cold. Loose objects nearby are displaced slightly. A canteen ends up on the wrong side of a closed bag. Somewhere nearby, something significant just happened to time or space.",
        "colour": 0x9944CC,
    },
    {
        "title": "The Dead Speak Once",
        "desc": "A name — just a name, spoken clearly in a voice that belongs to someone who isn't there. Each person who hears it says it was a different name. Each name belongs to someone they know.",
        "colour": 0x331133,
    },
    {
        "title": "Perfect Stillness",
        "desc": "No wind. No birdsong. No insects. The silence is so complete it feels like pressure. It lasts exactly long enough to become deeply unsettling, then ends as abruptly as it started. Nothing explains it.",
        "colour": 0x333333,
    },
    {
        "title": "A Familiar Stranger",
        "desc": "Someone in the crowd looks exactly like a person each of you knows — but a different person for each of you. When you move to follow or address them, they're gone. They didn't walk away. They're simply no longer present.",
        "colour": 0x443355,
    },
    {
        "title": "Luxon Light",
        "desc": "A pulse of soft golden light rises from the ground a few hundred yards away, climbs to about thirty feet, then fades. Nothing marks the spot afterward. The Dynasty would call it a consecuted soul finding its next life. The Empire has no official position on what it is.",
        "colour": 0xCCBB44,
    },
]

_ENCOUNTERS = [
    {
        "title": "Travelling Performer",
        "desc": "A lone bard with a cart of props and a tired mule is setting up for a performance at the roadside, apparently for no audience. They seem genuinely pleased to have some. Their act is stranger than expected and the closing song carries a verse that seems personally relevant.",
        "tone": "Social / information",
        "colour": 0x887722,
    },
    {
        "title": "Lost Pilgrim",
        "desc": "An elderly pilgrim has been walking for three days in what they believe is the right direction. They have a hand-drawn map that is confidently, catastrophically wrong. They are determined, cheerful, and utterly lost.",
        "tone": "Social / navigation",
        "colour": 0x558844,
    },
    {
        "title": "Wounded Animal",
        "desc": "A wolf — large, old, clearly suffering from an arrow wound — lies off the road. It's watching you without aggression. The arrow is Imperial military issue. It has a brass tag through one ear: it was someone's companion.",
        "tone": "Compassion / mystery",
        "colour": 0x665544,
    },
    {
        "title": "Children with a Find",
        "desc": "Two local children approach with obvious excitement: they've found something in a field. It turns out to be a sealed silver tube — the kind used for important correspondence. They want to know if it's treasure. It might be.",
        "tone": "Discovery / hook",
        "colour": 0xAA9944,
    },
    {
        "title": "A Healer in Need",
        "desc": "A field medic — Cobalt Soul trained by the look of the kit — is treating three people in a collapsed barn off the road. She's been awake for two days. She doesn't ask for help; she just looks at you like she's calculating what she can say without begging.",
        "tone": "Aid / moral weight",
        "colour": 0x335566,
    },
    {
        "title": "Merchant with Too Much",
        "desc": "A merchant's cart has thrown a wheel in a muddy stretch of road. The merchant is frantic — the cargo is tarpaulined, the cart too heavy to move alone, and he's been here for two hours. He'll pay. He very much wants to keep the tarpaulin in place.",
        "tone": "Physical challenge / curiosity",
        "colour": 0x886633,
    },
    {
        "title": "Old Soldier",
        "desc": "An old veteran of the Wynandir war sits at a milestone, resting. He doesn't ask for money. He asks if you've been to Bladegarden lately. He left something there before the battle — not an object, exactly. He's been meaning to go back for twenty years.",
        "tone": "Story / pathos",
        "colour": 0x554433,
    },
    {
        "title": "An Abandoned Cart",
        "desc": "A merchant's cart, horse and all, standing on the road — fully loaded, apparently undamaged, completely empty of people. The horse is calm. The cargo is intact. There's a meal half-eaten on the driver's seat, still slightly warm.",
        "tone": "Mystery",
        "colour": 0x444444,
    },
]

# ── Event type registry ───────────────────────────────────────────────────────

EVENT_TYPES = {
    "weather":    (_WEATHER,    "🌦️"),
    "rumour":     (_RUMOURS,    "📣"),
    "discovery":  (_DISCOVERIES,"🔍"),
    "faction":    (_FACTION_EVENTS, "⚔️"),
    "omen":       (_OMENS,      "🔮"),
    "encounter":  (_ENCOUNTERS, "👥"),
}

EVENT_TYPE_CHOICES = list(EVENT_TYPES.keys())


def generate(
    campaign_id: int | None = None,
    event_type: str | None = None,
    region: str | None = None,
    seed: int | None = None,
) -> dict:
    """Generate a single world event. Returns a dict with type, icon, embed data."""
    rng = random.Random(seed)

    if event_type and event_type in EVENT_TYPES:
        pool, icon = EVENT_TYPES[event_type]
        chosen_type = event_type
    else:
        # Weight: encounters & rumours more common; omens rarer
        weights = [2, 3, 2, 2, 1, 3]
        chosen_type = rng.choices(EVENT_TYPE_CHOICES, weights=weights, k=1)[0]
        pool, icon  = EVENT_TYPES[chosen_type]

    event = dict(rng.choice(pool))
    event["type"]   = chosen_type
    event["icon"]   = icon
    event["region"] = region or (
        rng.choice(list(REGIONS.keys())) if REGIONS else "Wildemount"
    )

    # For faction events, optionally pull a hook from the faction data
    if chosen_type == "faction" and FACTIONS:
        faction_name = event.get("faction", "")
        fdata = next((f for f in FACTIONS if f["name"] == faction_name), None)
        if fdata and fdata.get("hooks"):
            event["hook"] = rng.choice(fdata["hooks"])

    return event


def build_embed(event: dict) -> "discord.Embed":
    import discord
    title  = f"{event['icon']} {event['title']}"
    colour = event.get("colour", 0x8B7355)
    embed  = discord.Embed(title=title, description=event["desc"], colour=colour)

    if event.get("detail"):
        embed.add_field(name="Details", value=event["detail"], inline=False)
    if event.get("significance"):
        embed.add_field(name="Significance", value=event["significance"], inline=True)
    if event.get("mood"):
        embed.add_field(name="Mood", value=event["mood"], inline=True)
    if event.get("source"):
        embed.add_field(name="Source", value=event["source"], inline=True)
    if event.get("reliability"):
        embed.add_field(name="Reliability", value=event["reliability"], inline=True)
    if event.get("faction"):
        embed.add_field(name="Faction", value=event["faction"], inline=True)
    if event.get("tone"):
        embed.add_field(name="Tone", value=event["tone"], inline=True)
    if event.get("hook"):
        embed.add_field(name="Potential Hook", value=event["hook"], inline=False)

    embed.set_footer(text=f"World Event · {event.get('region','Wildemount')} · {event['type'].title()}")
    return embed
