"""SQLite persistence — standalone DB or shared dndcampaign.db."""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_USE_SHARED = os.getenv("USE_SHARED_DB", "0") == "1"

if _USE_SHARED:
    # Expects dndcampaign to be running at the sibling directory
    _DB_PATH = str(Path(__file__).parent.parent.parent / "dndcampaign" / "dndcampaign.db")
else:
    _DB_PATH = os.getenv("BOT_DB_PATH", str(Path(__file__).parent.parent / "campaign.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    setting     TEXT DEFAULT 'Wildemount',
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS npcs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    race         TEXT,
    npc_class    TEXT,
    level        INTEGER DEFAULT 1,
    faction      TEXT,
    region       TEXT,
    alignment    TEXT,
    personality  TEXT,
    ideal        TEXT,
    bond         TEXT,
    flaw         TEXT,
    backstory    TEXT,
    hp           INTEGER,
    ac           INTEGER,
    str_score INTEGER, dex_score INTEGER, con_score INTEGER,
    int_score INTEGER, wis_score INTEGER, cha_score INTEGER,
    notes        TEXT,
    status       TEXT DEFAULT 'alive',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS quests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    description  TEXT,
    faction      TEXT,
    region       TEXT,
    difficulty   TEXT DEFAULT 'medium',
    status       TEXT DEFAULT 'active',
    reward       TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS encounters (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    status       TEXT DEFAULT 'planning',
    round        INTEGER DEFAULT 0,
    current_turn INTEGER DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS combatants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id   INTEGER REFERENCES encounters(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    combatant_type TEXT DEFAULT 'monster',
    initiative     INTEGER DEFAULT 0,
    hp             INTEGER DEFAULT 0,
    max_hp         INTEGER DEFAULT 0,
    ac             INTEGER DEFAULT 10,
    conditions     TEXT DEFAULT '[]',
    notes          TEXT DEFAULT '',
    is_active      INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS lore (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    content      TEXT,
    lore_type    TEXT DEFAULT 'session',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS maps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    map_data     TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loot (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id  INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    cr           INTEGER DEFAULT 0,
    gold         INTEGER DEFAULT 0,
    items        TEXT DEFAULT '[]',
    claimed      TEXT DEFAULT '[]',
    shared       INTEGER DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init() -> None:
    if _USE_SHARED:
        return
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript(SCHEMA)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def cursor():
    conn = _connect()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchall(sql: str, params: tuple = ()) -> list[dict]:
    with cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def fetchone(sql: str, params: tuple = ()) -> dict | None:
    with cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> int:
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid
