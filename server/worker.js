// The game's small server (Cloudflare Worker). Everything under /api/ is the leaderboard; every other address is one
// of the game's files, served as before. The scores live in a D1 database (server/schema.sql), bound here as env.DB.
//
//   POST /api/player  { id, secret, name, colours }                          register a stable name, or change name or colours
//   POST /api/score   { id, secret, season, kind, day, seed, prize, wins, title }   post a finished game
//   GET  /api/board?season=royal-ascot&view=today|yesterday|best&id=...      the standings, and where this player is
//
// The game runs in the player's browser, so a score is what the browser says it is. This checks what it can (a
// sensible prize, the right day, one finish per day's card, a name's owner) but a determined cheat could still post a
// false score: the thorough answer, replaying a game's choices here, is for later.
const SEASONS = ["royal-ascot", "newmarket"], RACES = 10, PRIZE_CAP = 12000000;
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const bad = (error, status = 400) => json({ ok: false, error }, status);
const ukDay = (t) => { const o = {}; new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date(t)).forEach((x) => (o[x.type] = x.value)); return `${o.year}-${o.month}-${o.day}`; };
const idOk = (v) => typeof v === "string" && /^[A-Za-z0-9-]{16,64}$/.test(v);
const coloursOk = (v) => typeof v === "string" && /^j\d{1,2}\.\d{1,2}\.\d{1,2}-s\d{1,2}\.\d{1,2}\.\d{1,2}-c\d{1,2}\.\d{1,2}\.\d{1,2}$/.test(v);
async function sha(text) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)); return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join(""); }
// A stable name: 3 to 20 letters, numbers, spaces and a little punctuation; nothing rude
// (a short list of the words nobody should have to read on a leaderboard; kept to ones that rarely sit inside real names)
const RUDE = ["fuck", "shit", "cunt", "nigg", "fagg", "wank", "twat", "bitch", "rapist", "nazi", "hitler", "paedo", "whore", "slut"];
const plain = (k) => k.replace(/1/g, "i").replace(/0/g, "o").replace(/3/g, "e").replace(/4/g, "a").replace(/5/g, "s").replace(/7/g, "t");
function cleanName(v) {
  const name = String(v == null ? "" : v).replace(/\s+/g, " ").trim();
  if (name.length < 3 || name.length > 20 || !/^[A-Za-z0-9 '&.\-]+$/.test(name) || !/[A-Za-z]/.test(name)) return null;
  const key = name.toLowerCase().replace(/[^a-z0-9]/g, "");
  if (key.length < 3 || RUDE.some((w) => key.includes(w) || plain(key).includes(w))) return null;
  return { name, key };
}
async function owner(env, id, secret) {
  if (!idOk(id) || !idOk(secret)) return null;
  const p = await env.DB.prepare("SELECT id, secret_hash, name, colours FROM players WHERE id = ?").bind(id).first();
  return p && p.secret_hash === (await sha(secret)) ? p : null;
}

async function postPlayer(env, b) {
  if (!idOk(b.id) || !idOk(b.secret)) return bad("id");
  const nm = cleanName(b.name); if (!nm) return bad("name");
  const colours = coloursOk(b.colours) ? b.colours : null, now = Date.now(), hash = await sha(b.secret);
  const mine = await env.DB.prepare("SELECT secret_hash FROM players WHERE id = ?").bind(b.id).first();
  if (mine && mine.secret_hash !== hash) return bad("not yours", 403);
  const taken = await env.DB.prepare("SELECT id FROM players WHERE name_key = ? AND id <> ?").bind(nm.key, b.id).first();
  if (taken) return bad("taken", 409);
  try {
    if (mine) await env.DB.prepare("UPDATE players SET name = ?, name_key = ?, colours = COALESCE(?, colours), updated = ? WHERE id = ?").bind(nm.name, nm.key, colours, now, b.id).run();
    else await env.DB.prepare("INSERT INTO players (id, secret_hash, name, name_key, colours, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?)").bind(b.id, hash, nm.name, nm.key, colours, now, now).run();
  } catch (e) { return bad("taken", 409); }      // two players after the same name in the same moment
  return json({ ok: true, name: nm.name });
}

async function postScore(env, b) {
  const p = await owner(env, b.id, b.secret); if (!p) return bad("register first", 403);
  const season = b.season, kind = b.kind, prize = Number(b.prize), wins = Number(b.wins), seed = Number(b.seed);
  if (!SEASONS.includes(season) || !["daily", "random"].includes(kind)) return bad("season");
  if (!Number.isInteger(prize) || prize < 0 || prize > PRIZE_CAP || !Number.isInteger(wins) || wins < 0 || wins > RACES || !Number.isInteger(seed) || seed < 1) return bad("score");
  const title = String(b.title || "").replace(/[^A-Za-z '\-]/g, "").slice(0, 40) || "Owner", now = Date.now();
  let day = "";
  if (kind === "daily") {
    day = String(b.day || "");
    // today's card, or yesterday's finished after midnight
    if (day !== ukDay(now) && day !== ukDay(now - 864e5)) return bad("day");
    if (seed <= 1000000) return bad("score");
    const had = await env.DB.prepare("SELECT n FROM scores WHERE player = ? AND season = ? AND kind = 'daily' AND day = ?").bind(p.id, season, day).first();
    if (had) return json({ ok: true, kept: false });           // a day's card counts once: the first finish stands
  } else if (seed > 1000000) return bad("score");
  const r = await env.DB.prepare("INSERT OR IGNORE INTO scores (player, season, kind, day, seed, prize, wins, title, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)").bind(p.id, season, kind, day, seed, prize, wins, title, now).run();
  return json({ ok: true, kept: !!(r.meta && r.meta.changes) });
}

// The order of a board: most prize money, then most wins, then whoever finished first. AHEAD counts the rows in front
// of a score (?1 its prize, ?2 its wins, ?3 when it was posted).
const AHEAD = "(s.prize > ?1 OR (s.prize = ?1 AND s.wins > ?2) OR (s.prize = ?1 AND s.wins = ?2 AND s.created < ?3))";
// every stable's best game of a season, daily or random (SQLite gives the other columns from the row with the most prize money)
const BEST = (n) => `SELECT s.player, MAX(s.prize) AS prize, s.wins, s.title, s.created FROM scores s WHERE s.season = ?${n} GROUP BY s.player`;
async function getBoard(env, q) {
  const season = q.get("season"), view = q.get("view") || "today", id = q.get("id"), now = Date.now(), top = Math.max(1, Math.min(50, Number(q.get("top")) || 20));
  if (!SEASONS.includes(season)) return bad("season");
  const me = idOk(id) ? id : "", DB = env.DB;
  let rows, count, mine = null, day = null;
  if (view === "best") {
    rows = (await DB.prepare(`SELECT b.*, p.name, p.colours FROM (${BEST(1)}) b JOIN players p ON p.id = b.player ORDER BY b.prize DESC, b.wins DESC, b.created ASC LIMIT ?2`).bind(season, top).all()).results;
    count = (await DB.prepare("SELECT COUNT(DISTINCT player) AS c FROM scores WHERE season = ?1").bind(season).first()).c;
    if (me) {
      const m = await DB.prepare(`SELECT b.*, p.name, p.colours FROM (${BEST(1)}) b JOIN players p ON p.id = b.player WHERE b.player = ?2`).bind(season, me).first();
      if (m) { const a = await DB.prepare(`SELECT COUNT(*) AS c FROM (${BEST(4)}) s WHERE ${AHEAD}`).bind(m.prize, m.wins, m.created, season).first(); mine = { ...m, rank: a.c + 1 }; }
    }
  } else {
    day = view === "yesterday" ? ukDay(now - 864e5) : ukDay(now);
    const from = "FROM scores s JOIN players p ON p.id = s.player WHERE s.season = ?1 AND s.kind = 'daily' AND s.day = ?2";
    rows = (await DB.prepare(`SELECT s.player, s.prize, s.wins, s.title, s.created, p.name, p.colours ${from} ORDER BY s.prize DESC, s.wins DESC, s.created ASC LIMIT ?3`).bind(season, day, top).all()).results;
    count = (await DB.prepare("SELECT COUNT(*) AS c FROM scores s WHERE s.season = ?1 AND s.kind = 'daily' AND s.day = ?2").bind(season, day).first()).c;
    if (me) {
      const m = await DB.prepare(`SELECT s.player, s.prize, s.wins, s.title, s.created, p.name, p.colours ${from} AND s.player = ?3`).bind(season, day, me).first();
      if (m) { const a = await DB.prepare(`SELECT COUNT(*) AS c FROM scores s WHERE ${AHEAD} AND s.season = ?4 AND s.kind = 'daily' AND s.day = ?5`).bind(m.prize, m.wins, m.created, season, day).first(); mine = { ...m, rank: a.c + 1 }; }
    }
  }
  const show = (r, k) => ({ rank: r.rank || k + 1, name: r.name, colours: r.colours, prize: r.prize, wins: r.wins, title: r.title, me: !!me && r.player === me });
  return json({ ok: true, season, view: view === "best" ? "best" : view === "yesterday" ? "yesterday" : "today", day, today: ukDay(now), count, rows: rows.map(show), me: mine ? show(mine, 0) : null });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    try {
      if (request.method === "GET" && url.pathname === "/api/board") return await getBoard(env, url.searchParams);
      if (request.method === "POST") {
        const text = await request.text(); if (text.length > 2000) return bad("too long", 413);
        let body; try { body = JSON.parse(text); } catch (e) { return bad("json"); }
        if (!body || typeof body !== "object") return bad("json");
        if (url.pathname === "/api/player") return await postPlayer(env, body);
        if (url.pathname === "/api/score") return await postScore(env, body);
      }
      return bad("not found", 404);
    } catch (e) { console.log("api error", url.pathname, String(e && e.message || e)); return bad("server", 500); }
  },
};
