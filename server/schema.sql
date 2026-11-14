-- The leaderboard's database (Cloudflare D1: "thoroughbred-leaderboard"). Run once; safe to run again.
-- A player is a stable name on one phone or computer: the browser makes an id and a secret, and only a hash of the
-- secret is kept here, so nobody else can post scores under that name.
CREATE TABLE IF NOT EXISTS players (
  id TEXT PRIMARY KEY,
  secret_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  name_key TEXT NOT NULL UNIQUE,      -- the name in lower case with no spaces: one stable per name
  colours TEXT,                       -- the player's colours as SilksPaint.encode() writes them, e.g. j5.1.4-s6.0.5-c6.4.1
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL
);
-- One row per finished game. A day's card counts once per player (the first finish); a random game once per season number.
CREATE TABLE IF NOT EXISTS scores (
  n INTEGER PRIMARY KEY AUTOINCREMENT,
  player TEXT NOT NULL,
  season TEXT NOT NULL,               -- royal-ascot | newmarket
  kind TEXT NOT NULL,                 -- daily | random
  day TEXT NOT NULL DEFAULT '',       -- the daily card's day (UK), YYYY-MM-DD; empty for a random game
  seed INTEGER NOT NULL,
  prize INTEGER NOT NULL,
  wins INTEGER NOT NULL,
  title TEXT NOT NULL,
  created INTEGER NOT NULL,
  UNIQUE (player, season, kind, day, seed)
);
CREATE INDEX IF NOT EXISTS scores_board ON scores (season, kind, day, prize DESC);
CREATE INDEX IF NOT EXISTS scores_player ON scores (player, season);
