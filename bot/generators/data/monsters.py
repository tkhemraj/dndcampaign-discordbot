"""Monster stat blocks for encounter generation. CR, HP, AC, attack bonus, damage."""

MONSTERS = [
    # CR 0
    {"name": "Rat",            "cr": 0,    "hp": 1,   "ac": 10, "atk": 0,  "dmg": "1",     "type": "beast"},
    {"name": "Bat",            "cr": 0,    "hp": 1,   "ac": 12, "atk": 0,  "dmg": "1",     "type": "beast"},
    # CR 1/8
    {"name": "Bandit",         "cr": 0.125,"hp": 11,  "ac": 12, "atk": 3,  "dmg": "1d6+1", "type": "humanoid"},
    {"name": "Cultist",        "cr": 0.125,"hp": 9,   "ac": 12, "atk": 3,  "dmg": "1d6+1", "type": "humanoid"},
    {"name": "Guard",          "cr": 0.125,"hp": 11,  "ac": 16, "atk": 3,  "dmg": "1d6+1", "type": "humanoid"},
    {"name": "Kobold",         "cr": 0.125,"hp": 5,   "ac": 12, "atk": 4,  "dmg": "1d4+2", "type": "humanoid"},
    # CR 1/4
    {"name": "Goblin",         "cr": 0.25, "hp": 7,   "ac": 15, "atk": 4,  "dmg": "1d6+2", "type": "humanoid"},
    {"name": "Skeleton",       "cr": 0.25, "hp": 13,  "ac": 13, "atk": 4,  "dmg": "1d6+2", "type": "undead"},
    {"name": "Zombie",         "cr": 0.25, "hp": 22,  "ac": 8,  "atk": 3,  "dmg": "1d6+1", "type": "undead"},
    {"name": "Kryn Warrior",   "cr": 0.25, "hp": 11,  "ac": 16, "atk": 3,  "dmg": "1d8+1", "type": "humanoid", "wildemount": True},
    # CR 1/2
    {"name": "Orc",            "cr": 0.5,  "hp": 15,  "ac": 13, "atk": 5,  "dmg": "1d12+3","type": "humanoid"},
    {"name": "Scout",          "cr": 0.5,  "hp": 16,  "ac": 13, "atk": 4,  "dmg": "1d8+2", "type": "humanoid"},
    {"name": "Righteous Brand Soldier", "cr": 0.5, "hp": 16, "ac": 14, "atk": 4, "dmg": "1d8+2", "type": "humanoid", "wildemount": True},
    # CR 1
    {"name": "Drow",           "cr": 1,    "hp": 13,  "ac": 15, "atk": 4,  "dmg": "1d6+2", "type": "humanoid"},
    {"name": "Ghoul",          "cr": 1,    "hp": 22,  "ac": 12, "atk": 4,  "dmg": "2d6+2", "type": "undead"},
    {"name": "Specter",        "cr": 1,    "hp": 22,  "ac": 12, "atk": 4,  "dmg": "3d6",   "type": "undead"},
    {"name": "Spy",            "cr": 1,    "hp": 27,  "ac": 12, "atk": 4,  "dmg": "1d6+2", "type": "humanoid"},
    {"name": "Cerberus Assembly Mage","cr":1,"hp":22, "ac": 13, "atk": 5,  "dmg": "3d6",   "type": "humanoid", "wildemount": True},
    # CR 2
    {"name": "Bandit Captain", "cr": 2,    "hp": 65,  "ac": 15, "atk": 5,  "dmg": "1d8+3", "type": "humanoid"},
    {"name": "Ghast",          "cr": 2,    "hp": 36,  "ac": 13, "atk": 5,  "dmg": "2d8+3", "type": "undead"},
    {"name": "Gargoyle",       "cr": 2,    "hp": 52,  "ac": 15, "atk": 5,  "dmg": "2d6+2", "type": "elemental"},
    {"name": "Nott / Goblin Boss","cr": 2, "hp": 27,  "ac": 17, "atk": 5,  "dmg": "2d6+3", "type": "humanoid"},
    # CR 3
    {"name": "Manticore",      "cr": 3,    "hp": 68,  "ac": 14, "atk": 5,  "dmg": "2d6+3", "type": "monstrosity"},
    {"name": "Minotaur",       "cr": 3,    "hp": 114, "ac": 14, "atk": 6,  "dmg": "2d12+4","type": "monstrosity"},
    {"name": "Myriad Assassin","cr": 3,    "hp": 58,  "ac": 15, "atk": 6,  "dmg": "1d6+4", "type": "humanoid", "wildemount": True},
    {"name": "Wight",          "cr": 3,    "hp": 45,  "ac": 14, "atk": 5,  "dmg": "2d6+2", "type": "undead"},
    # CR 4
    {"name": "Banshee",        "cr": 4,    "hp": 58,  "ac": 12, "atk": 4,  "dmg": "3d6+3", "type": "undead"},
    {"name": "Ettin",          "cr": 4,    "hp": 85,  "ac": 12, "atk": 7,  "dmg": "2d8+5", "type": "giant"},
    {"name": "Shadow Demon",   "cr": 4,    "hp": 66,  "ac": 13, "atk": 5,  "dmg": "2d6+3", "type": "fiend"},
    # CR 5
    {"name": "Gladiator",      "cr": 5,    "hp": 112, "ac": 16, "atk": 7,  "dmg": "2d8+5", "type": "humanoid"},
    {"name": "Troll",          "cr": 5,    "hp": 84,  "ac": 15, "atk": 7,  "dmg": "2d6+4", "type": "giant"},
    {"name": "Xorn",           "cr": 5,    "hp": 73,  "ac": 19, "atk": 8,  "dmg": "3d6+5", "type": "elemental"},
    {"name": "Kryn Gloomstalker","cr": 5,  "hp": 91,  "ac": 15, "atk": 7,  "dmg": "2d8+4", "type": "monstrosity", "wildemount": True},
    # CR 6
    {"name": "Mage",           "cr": 6,    "hp": 40,  "ac": 12, "atk": 6,  "dmg": "4d8",   "type": "humanoid"},
    {"name": "Vrock",          "cr": 6,    "hp": 104, "ac": 15, "atk": 8,  "dmg": "2d10+5","type": "fiend"},
    # CR 7
    {"name": "Stone Giant",    "cr": 7,    "hp": 126, "ac": 17, "atk": 9,  "dmg": "3d10+6","type": "giant"},
    {"name": "Oni",            "cr": 7,    "hp": 110, "ac": 16, "atk": 7,  "dmg": "2d10+4","type": "giant"},
    # CR 8
    {"name": "Assassin",       "cr": 8,    "hp": 78,  "ac": 15, "atk": 7,  "dmg": "2d6+4", "type": "humanoid"},
    {"name": "Chain Devil",    "cr": 8,    "hp": 85,  "ac": 16, "atk": 8,  "dmg": "2d6+4", "type": "fiend"},
    # CR 9
    {"name": "Fire Giant",     "cr": 9,    "hp": 162, "ac": 18, "atk": 11, "dmg": "6d6+7", "type": "giant"},
    {"name": "Aezpun Abyssal Architect","cr":9,"hp":136,"ac":17,"atk":9, "dmg":"3d10+5","type":"fiend","wildemount":True},
    # CR 10
    {"name": "Aboleth",        "cr": 10,   "hp": 135, "ac": 17, "atk": 9,  "dmg": "3d6+5", "type": "aberration"},
    {"name": "Guardian Naga",  "cr": 10,   "hp": 120, "ac": 18, "atk": 8,  "dmg": "4d6+4", "type": "monstrosity"},
    # CR 11-15
    {"name": "Horned Devil",   "cr": 11,   "hp": 148, "ac": 18, "atk": 10, "dmg": "3d8+6", "type": "fiend"},
    {"name": "Archmage",       "cr": 12,   "hp": 99,  "ac": 12, "atk": 8,  "dmg": "6d6",   "type": "humanoid"},
    {"name": "Ludinus Da'leth (approx)","cr":15,"hp":180,"ac":14,"atk":9,"dmg":"8d6","type":"humanoid","wildemount":True},
    # CR 16+
    {"name": "Adult Red Dragon","cr":17,   "hp": 256, "ac": 19, "atk": 13, "dmg": "2d10+7","type": "dragon"},
    {"name": "Ancient White Dragon","cr":20,"hp":333,"ac": 20, "atk": 14, "dmg": "2d10+8","type": "dragon"},
    {"name": "Balor",          "cr": 19,   "hp": 262, "ac": 19, "atk": 14, "dmg": "3d10+9","type": "fiend"},
    {"name": "Lich",           "cr": 21,   "hp": 135, "ac": 17, "atk": 7,  "dmg": "4d8",   "type": "undead"},
]

CR_TO_XP = {
    0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
    1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
    6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
    11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
    16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
    21: 33000,
}

DIFFICULTY_THRESHOLDS = {
    # per-player XP thresholds by level [easy, medium, hard, deadly]
    1:  [25,   50,   75,   100],
    2:  [50,   100,  150,  200],
    3:  [75,   150,  225,  400],
    4:  [125,  250,  375,  500],
    5:  [250,  500,  750,  1100],
    6:  [300,  600,  900,  1400],
    7:  [350,  750,  1100, 1700],
    8:  [450,  900,  1400, 2100],
    9:  [550,  1100, 1600, 2400],
    10: [600,  1200, 1900, 2800],
    11: [800,  1600, 2400, 3600],
    12: [1000, 2000, 3000, 4500],
    15: [1100, 2200, 3400, 5100],
    20: [2800, 5700, 8500, 12700],
}
