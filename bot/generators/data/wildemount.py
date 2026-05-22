"""
Wildemount lore tables — factions, locations, names, deities, plot seeds.
Source: Explorer's Guide to Wildemount (Matthew Mercer / Wizards of the Coast, 2020)
"""

FACTIONS = [
    {
        "name": "Dwendalian Empire",
        "region": "Western Wynandir",
        "alignment": "Lawful Neutral",
        "description": "A militaristic monarchy ruling Western Wynandir. Suppresses worship of most deities in favour of state control. At war with the Kryn Dynasty.",
        "hooks": [
            "Crown marshals are hunting a deserter who knows too much about Cerberus Assembly experiments.",
            "A local lord is collecting 'war taxes' far beyond the imperial mandate — and pocketing the difference.",
            "The empire needs couriers to deliver sealed orders across Xhorhas. The contents are not your concern.",
            "A Righteous Brand commander requests deniable operatives to raid a Kryn supply line.",
        ],
    },
    {
        "name": "Cerberus Assembly",
        "region": "Western Wynandir",
        "alignment": "Lawful Evil",
        "description": "Eight archmages who serve as advisors and enforcers for the Dwendalian Empire. More powerful than many suspect — and more ruthless.",
        "hooks": [
            "Archmage Ludinus Da'leth wants a relic recovered from Eiselcross before a rival mage reaches it.",
            "A Cobalt Soul monk suspects the Assembly is conducting soul-binding experiments in a locked tower.",
            "Someone has stolen a tome of Dunamancy from Assembly vaults. They want it back quietly.",
            "An Assembly member is willing to pay handsomely for evidence that a rival is dealing with the Kryn.",
        ],
    },
    {
        "name": "Kryn Dynasty",
        "region": "Xhorhas",
        "alignment": "Lawful Neutral",
        "description": "A civilisation of Drow and others in Eastern Wynandir, devoted to the Luxon. Practice consecution — the belief that the faithful are reborn after death to carry memories forward.",
        "hooks": [
            "The Bright Queen seeks emissaries willing to enter the Empire to negotiate a prisoner exchange.",
            "A consecuted warrior has been reborn but remembers nothing — and enemies want them dead before the memories return.",
            "A Luxon beacon has gone dark near Bazzoxan. Something in the wastes is consuming its light.",
            "The Aurora Watch needs scouts to map a new passage through the Ashkeeper Peaks.",
        ],
    },
    {
        "name": "Cobalt Soul",
        "region": "All of Wildemount",
        "alignment": "Lawful Good",
        "description": "An order of monks and scholars devoted to Ioun, goddess of knowledge. They expose corruption and preserve truth — sometimes dangerously.",
        "hooks": [
            "An Expositor has gone missing inside Rexxentrum. Their last report mentioned a name that should not be spoken.",
            "The Soul's archive in Zadash was broken into; only one record was taken — the party's.",
            "A dying monk presses a sealed letter into your hands: 'Reach the High Curator. Tell no one.'",
        ],
    },
    {
        "name": "The Revelry",
        "region": "Menagerie Coast",
        "alignment": "Chaotic Neutral",
        "description": "Pirates of the Lucidian Ocean led by the Plank King, based out of Darktow Isle. They raid coastal trade but follow a strict code among themselves.",
        "hooks": [
            "The Revelry seized a ship carrying something that was never meant to reach port. They want to sell it — to the right buyer.",
            "A merchant prince in Port Damali wants the Plank King's head. Quietly.",
            "A Revelry ship was sunk in calm waters with no survivors. The Plank King wants answers.",
        ],
    },
    {
        "name": "The Myriad",
        "region": "All of Wildemount",
        "alignment": "Neutral Evil",
        "description": "A vast criminal syndicate embedded in every city, dealing in contraband, blackmail, and assassination. Recently driven from the Empire's largest cities — or so the Empire believes.",
        "hooks": [
            "A Myriad contact offers triple pay for a simple job: escort a crate, no questions.",
            "Someone is systematically killing Myriad operatives in Zadash. The syndicate wants it stopped before panic spreads.",
            "You owe the Myriad a favour. They're calling it in.",
        ],
    },
    {
        "name": "The Clovis Concord",
        "region": "Menagerie Coast",
        "alignment": "Lawful Neutral",
        "description": "The governing council of the seven City-States of the Menagerie Coast. Trade-focused and nominally independent from both major powers.",
        "hooks": [
            "A Concord inspector found smuggled Dunamancy artefacts in a Port Damali warehouse and promptly disappeared.",
            "Tensions between two city-states are about to boil over into open conflict. A neutral party is needed to mediate.",
        ],
    },
]

REGIONS = {
    "Western Wynandir": {
        "description": "Heart of the Dwendalian Empire. Fertile farmland, imperial roads, and soldiers everywhere.",
        "locations": [
            "Rexxentrum", "Zadash", "Trostenwald", "Deastok", "Felderwin",
            "Hupperdook", "Nogvurot", "Pride's Call", "Grimgolir",
            "Zemni Fields", "Marrow Valley", "Cyrios Mountains",
        ],
        "terrain": ["plains", "farmland", "hills", "dungeon"],
        "encounter_flavour": [
            "Imperial patrol demanding to see travel papers",
            "Cerberus Assembly mages escorting a chained prisoner",
            "Refugees fleeing the eastern front",
            "Cultists of a Betrayer God, disguised as pilgrims",
            "A wanted poster — one of the party's faces is on it",
        ],
    },
    "Xhorhas": {
        "description": "Blasted badlands and volcanic wastes ruled by the Kryn Dynasty. Strange beauty and ancient danger.",
        "locations": [
            "Rosohna", "Bazzoxan", "Urzin", "Asarius", "Iothia Moorlands",
            "Ashkeeper Peaks", "Barbed Fields", "Sorrowseep Waters",
            "Den Thelyss", "Den Mirimm", "Underbelly of Rosohna",
        ],
        "terrain": ["badlands", "dungeon", "caverns", "ruins"],
        "encounter_flavour": [
            "Kryn Aurora Watch patrol, suspicious of outsiders",
            "A consecuted soldier who has forgotten their past life, wandering alone",
            "Demons spilling from a rift near Bazzoxan",
            "An abandoned Luxon beacon, still faintly glowing",
            "A massive Umbramantle above — the Dynasty's magical shield over Rosohna",
        ],
    },
    "Menagerie Coast": {
        "description": "Tropical city-states and merchant ports along the Lucidian Ocean. Wealth, pirates, and political intrigue.",
        "locations": [
            "Nicodranas", "Port Damali", "Tussoa", "Oremid", "Feolinn",
            "Palma Flora", "Darktow Isle", "Lucidian Ocean",
            "Open Quay", "Ruby Sunrise Inn",
        ],
        "terrain": ["coastal", "jungle", "interior", "tavern"],
        "encounter_flavour": [
            "Revelry pirates boarding a merchant vessel",
            "A Myriad smuggler looking for help moving cargo",
            "A Concord inspector who knows more than they should",
            "Sea serpent spotted off the coast — the navy is offering a bounty",
        ],
    },
    "Greying Wildlands": {
        "description": "A vast, dangerous northern wilderness. Home to Uthodurn — a rare city of dwarves and elves — and the Savalirwood, haunted by the betrayal of Obann.",
        "locations": [
            "Uthodurn", "Boroftkrah", "Savalirwood", "Cinderrest Sanctum",
            "Icehaven", "Greying Wildlands Tundra", "Crystalsands Tundra",
        ],
        "terrain": ["forest", "tundra", "dungeon", "caverns"],
        "encounter_flavour": [
            "Pallid elves scouting near their hidden borders",
            "A blighted treant, corrupted by the Savalirwood's dark history",
            "Wildfire spreading unnaturally fast — someone is burning the forest deliberately",
            "An orc clan from Boroftkrah, hostile to outsiders",
        ],
    },
    "Eiselcross": {
        "description": "A frozen archipelago in the far north, littered with ruins from before the Calamity. Research stations cling to the edge of survival.",
        "locations": [
            "Allowak's Sanctuary", "Balenpost", "Syrinlya",
            "Ruins of Aeor", "A2 — Research Outpost", "Foren Island",
            "Vurmas Outpost", "Tomb of the Trefoil",
        ],
        "terrain": ["tundra", "ruins", "dungeon", "ice caves"],
        "encounter_flavour": [
            "A Cerberus Assembly expedition, secretive about their findings",
            "A temporal anomaly — a moment from the Calamity replaying on loop",
            "Creatures frozen in ice for 800 years, now thawing",
            "A rival research team found something they weren't supposed to",
        ],
    },
}

RACES = [
    "Human (Zemnian)",
    "Human (Xhorhasian)",
    "Human (Clovis)",
    "Elf (High)",
    "Elf (Wood)",
    "Pallid Elf",           # Wildemount-unique: sun-starved, sensitive to light
    "Drow",
    "Dwarf (Mountain)",
    "Dwarf (Hill)",
    "Halfling (Lightfoot)",
    "Lotusden Halfling",    # Wildemount-unique: nature-attuned forest halflings
    "Gnome (Forest)",
    "Gnome (Rock)",
    "Half-Elf",
    "Half-Orc",
    "Tiefling",
    "Draconblood Dragonborn",   # Wildemount-unique: draconic nobles of Draconia
    "Ravenite Dragonborn",      # Wildemount-unique: former slaves, rebellious
    "Goblin",
    "Orc",
    "Aasimar",
    "Genasi",
    "Tabaxi",
    "Tortle",
]

# Name tables by cultural background
NAMES = {
    "Zemnian (Imperial)": {
        "first_m": ["Aldric", "Bren", "Caleb", "Edith", "Fjord", "Gunter", "Hamund", "Ikithon", "Jester", "Klaus",
                    "Luc", "Molly", "Nott", "Oskar", "Pumat", "Rinaldo", "Sepp", "Trent", "Ulric", "Veth",
                    "Wilhelm", "Yasha", "Zoran", "Brenathos", "Caduceus", "Dairon"],
        "first_f": ["Alura", "Bela", "Clara", "Dara", "Erika", "Frieda", "Greta", "Hilda", "Ilse", "Jana",
                    "Katya", "Liesel", "Marta", "Nele", "Petra", "Rosa", "Sabine", "Trude", "Ursa", "Vola"],
        "last":    ["Widogast", "Bronzegrip", "Ashguard", "Brenatto", "Clay", "Dwendal", "Ermendrud",
                    "Frostmantle", "Greymoore", "Hofstader", "Iosefka", "Jagentoth", "Khuul", "Lavorre",
                    "Mardoon", "Nydas", "Ophren", "Pumali", "Ruthendaal", "Soltriss"],
    },
    "Xhorhasian (Kryn)": {
        "first_m": ["Essek", "Verin", "Deirta", "Leylas", "Mirimm", "Thollo", "Adeen", "Oban", "Quana", "Riak",
                    "Skysunder", "Tyak", "Udrath", "Veilas", "Wyrick", "Xhorhas", "Yalann", "Zethris"],
        "first_f": ["Leylas", "Deanna", "Fen", "Jarende", "Khulan", "Lunia", "Myra", "Nydeth", "Olara", "Phaedra",
                    "Qorel", "Rienne", "Syl", "Telva", "Ulara", "Vera", "Wyrlan", "Xiema"],
        "last":    ["Thelyss", "Mirimm", "Xhorhas", "Kryn", "Byne", "Casadir", "Den'saava", "Erkath",
                    "Fadric", "Garoth", "Hethroth", "Iosiel", "Jennin", "Kazuru"],
    },
    "Coastal (Menagerie)": {
        "first_m": ["Beau", "Caduceus", "Devan", "Emon", "Farran", "Gil", "Harlan", "Ivan", "Joren", "Kir",
                    "Loren", "Merrick", "Navan", "Orlan", "Pierce", "Quentis", "Reani", "Solan", "Taryon", "Ulan"],
        "first_f": ["Avantika", "Brielle", "Calianna", "Dani", "Elaina", "Fren", "Grima", "Hira", "Isadora",
                    "Jaina", "Kylre", "Lita", "Mari", "Nila", "Orlan", "Pola", "Riya", "Saoirse", "Tara"],
        "last":    ["Dayana", "Ermendrud", "Frostborn", "Gravernd", "Harrowdale", "Isaryn", "Janitar",
                    "Kamordah", "Lassgrad", "Mardoon", "Norroa", "Oremid", "Palma", "Questis"],
    },
}

DEITIES = [
    # Prime Deities
    {"name": "The Wildmother (Melora)", "domain": "Nature, Sea", "alignment": "Neutral Good",
     "description": "Goddess of wilderness and the ocean. Beloved on the Menagerie Coast and in the Greying Wildlands."},
    {"name": "The Lawbearer (Erathis)", "domain": "Knowledge, Order", "alignment": "Lawful Neutral",
     "description": "Goddess of civilisation and law. Favoured by the Dwendalian Empire — though the emperor controls her worship tightly."},
    {"name": "The Knowing Mistress (Ioun)", "domain": "Knowledge", "alignment": "Neutral Good",
     "description": "Goddess of knowledge and prophecy. Patron of the Cobalt Soul."},
    {"name": "The Storm Lord (Kord)", "domain": "Tempest, War", "alignment": "Chaotic Neutral",
     "description": "God of storms and martial prowess. Popular among soldiers and sailors."},
    {"name": "The Platinum Dragon (Bahamut/Moradin)", "domain": "Life, War", "alignment": "Lawful Good",
     "description": "God of justice and dwarven craftsmanship."},
    {"name": "The Everlight (Avandra)", "domain": "Trickery, Travel", "alignment": "Chaotic Good",
     "description": "Goddess of freedom and luck. Beloved by halflings and travellers."},
    {"name": "The Raven Queen", "domain": "Death, Life", "alignment": "Lawful Neutral",
     "description": "Goddess of death and fate. She records all souls and guards against undeath."},
    # The Luxon — unique to Wildemount/Kryn
    {"name": "The Luxon", "domain": "Light, Rebirth", "alignment": "Unaligned",
     "description": "Not a god but an ancient entity of pure light predating the gods. The Kryn Dynasty worships it. Believers undergo consecution — death and rebirth, carrying memories forward."},
    # Betrayer Gods
    {"name": "The Chained Oblivion (Tharizdun)", "domain": "Death, Trickery", "alignment": "Chaotic Evil",
     "description": "The Betrayer God of entropy and madness. Imprisoned since the Calamity but still reaching out through cults."},
    {"name": "The Spider Queen (Lolth)", "domain": "Trickery", "alignment": "Chaotic Evil",
     "description": "Goddess of deception and spiders. Many Drow fled her influence to join the Kryn Dynasty."},
    {"name": "The Lord of the Hells (Asmodeus)", "domain": "Trickery", "alignment": "Lawful Evil",
     "description": "God of tyranny and hellfire. His influence is felt in the darkest corners of the Empire."},
    {"name": "The Ruiner (Gruumsh)", "domain": "War", "alignment": "Chaotic Evil",
     "description": "God of destruction and orcs. His priests preach endless war."},
]

SUBCLASSES = [
    {"name": "Echo Knight", "class": "Fighter", "source": "Wildemount",
     "description": "A fighter who harnesses Dunamancy to create echoes of themselves from alternate timelines."},
    {"name": "Chronurgy Magic", "class": "Wizard", "source": "Wildemount",
     "description": "A wizard who manipulates time itself — altering initiative, slowing enemies, glimpsing the future."},
    {"name": "Graviturgy Magic", "class": "Wizard", "source": "Wildemount",
     "description": "A wizard who bends gravity — crushing foes, launching allies, altering weight."},
]

PLOT_SEEDS = [
    # War arc
    "The party is caught behind enemy lines as the Empire launches a major offensive into Xhorhas.",
    "A Kryn dignitary wants to defect to the Empire but needs the party to get them out of Rosohna alive.",
    "Both sides believe an ancient artefact in the Ashkeeper Peaks could end the war — in their favour.",
    "A village on the front line has been sheltering soldiers from both armies. The commanding officers on each side are about to find out.",
    # Cerberus Assembly intrigue
    "Archmage Trent Ikithon is experimenting on civilian orphans to produce powerful mage-soldiers. Proof exists — if you survive getting it.",
    "A Cerberus Assembly member wants a rival's research destroyed. The rival's research could save thousands of lives.",
    "Something escaped from an Assembly vault in Rexxentrum. The Assembly wants it retrieved quietly. Very quietly.",
    # Kryn / Luxon mysteries
    "A Luxon beacon has been corrupted by a Betrayer God cult. The memories stored inside are leaking out as violent hauntings.",
    "A recently reborn Kryn warrior remembers being an imperial soldier in a past life — and remembers where the Empire buried its darkest secret.",
    "The Bright Queen believes the Luxon is trying to communicate something. She needs someone who isn't Kryn to receive the message without bias.",
    # Eiselcross / Calamity ruins
    "A research team at the Ruins of Aeor activated something they don't understand. They stopped sending reports three weeks ago.",
    "A pre-Calamity weapon has been found, perfectly preserved. Every major faction on Wildemount is sending agents to claim it.",
    "A temporal anomaly near Eiselcross is pulling people backward in time. Some of them are bringing things back with them.",
    # Menagerie Coast
    "The Plank King has gone silent. The Revelry is fracturing and the Concord is about to exploit the vacuum.",
    "A Myriad boss in Port Damali is collecting leverage on every Concord official. Someone wants the blackmail list — or the boss dead.",
    # Greying Wildlands
    "Uthodurn's Glassblades are hunting something in the Savalirwood that is hunting them back.",
    "A Pallid Elf village has begun hearing whispers from the forest that they recognise as the voices of dead ancestors.",
]
