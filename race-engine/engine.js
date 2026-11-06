// Thoroughbred Ascot: the race engine.
//
// One race at a time, seeded, so the same race with the same seed replays exactly. It follows the rules of the
// test bench (tools/race-bench/racebench.py), one race instead of thousands at once, and every number comes from
// race-engine/settings.json. It reads the course (courses/ascot.json), the stalls (courses/ascot-stalls.json) and
// the par times and going (courses/ascot-standards.json); it never fetches anything itself, so the race view and
// the game hand it those files, and Node can too.
//
//   import { runRace } from "./engine.js";
//   const { timeline, result } = runRace(race, runners, { course, stalls, standards, settings });
//
// race:    { course: "straight" | "roundMile" | "round", distance (m), start (a key in the stalls file's starts),
//            going: "Heavy" | "Softer" | "Good" | "Quicker" | "Quick", seed, handicap?: true }
// runners: in draw order (runners[0] is in stall 1). Each: { rating, style, flex, temperament, trip, goings,
//            mark?, jockey?, instruction?, shade?, name? } (see README.md)
//
// The timeline is what the race view plays back, and nothing else: { dt: 0.1, frames }, one frame every tenth of a
// second from the off (time 0, the gates opening), each runner in draw order as
//   [distance from the gate line along the inside rail (m, the horse's middle), across from the track's middle
//    (m, + towards the outer rail), speed (m/s), effort 0-3, heading off the course direction (radians)].
// The result: finishing order, margins in lengths, the winning time and a short list of race events.
//
// Plain JavaScript, no build step, works in a browser and in Node. Random numbers and the few curved functions
// it needs (logarithm, power, angle) are worked out with plain arithmetic, so every browser gives the same race.

// ---------------------------------------------------------------------------------------------- numbers
// Seeded random numbers: sfc32, seeded from a number or a string.
function hashSeed(seed) {
  const s = String(seed);
  let h = 1779033703 ^ s.length;
  for (let i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
  const out = [];
  for (let k = 0; k < 4; k++) { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); h ^= h >>> 16; out.push(h >>> 0); }
  return out;
}
export function makeRandom(seed) {
  let [a, b, c, d] = hashSeed(seed);
  const next = () => {
    a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
    let t = (a + b) | 0;
    a = b ^ (b >>> 9); b = (c + (c << 3)) | 0; c = (c << 21) | (c >>> 11); d = (d + 1) | 0; t = (t + d) | 0; c = (c + t) | 0;
    return (t >>> 0) / 4294967296;
  };
  for (let i = 0; i < 12; i++) next();
  let spare = null;
  const rnd = {
    next,                                                  // [0, 1)
    uniform: (lo, hi) => lo + (hi - lo) * next(),
    int: (lo, hi) => lo + Math.floor(next() * (hi - lo)),   // lo .. hi-1
    chance: (p) => next() < p,
    choice: (weights) => { let r = next() * weights.reduce((s, w) => s + w, 0); for (let i = 0; i < weights.length; i++) { r -= weights[i]; if (r < 0) return i; } return weights.length - 1; },
    normal(mean = 0, sd = 1) {                             // Marsaglia's polar method (no sines or cosines)
      if (spare !== null) { const s = spare; spare = null; return mean + sd * s; }
      let u, v, s;
      do { u = 2 * next() - 1; v = 2 * next() - 1; s = u * u + v * v; } while (s >= 1 || s === 0);
      const m = Math.sqrt(-2 * ln(s) / s);
      spare = v * m;
      return mean + sd * u * m;
    },
  };
  return rnd;
}
// Logarithm, power and angle from + - * / and sqrt only (these are exact in every browser; Math.log, Math.pow and
// Math.atan2 may differ in the last digit from one browser to another, which could change a race).
const LN2 = 0.6931471805599453;
function ln(x) {
  if (!(x > 0)) return x === 0 ? -Infinity : NaN;
  let k = 0;
  while (x > 1.4142135623730951) { x /= 2; k++; }
  while (x < 0.7071067811865476) { x *= 2; k--; }
  const y = (x - 1) / (x + 1), y2 = y * y;                 // ln x = 2 atanh y, |y| < 0.172
  let term = y, sum = 0;
  for (let n = 1; n < 40; n += 2) { sum += term / n; term *= y2; }
  return 2 * sum + k * LN2;
}
function exp(x) {
  const k = Math.round(x / LN2), r = x - k * LN2;
  let term = 1, sum = 1;
  for (let n = 1; n < 30; n++) { term *= r / n; sum += term; }
  let p = 1, b = k >= 0 ? 2 : 0.5;
  for (let i = Math.abs(k); i > 0; i--) p *= b;
  return sum * p;
}
const pow = (x, y) => (x === 0 ? 0 : exp(y * ln(x)));
function atan(x) {                                         // for |x| <= 1
  let k = 0;
  while (Math.abs(x) > 0.2) { x = x / (1 + Math.sqrt(1 + x * x)); k++; }   // atan x = 2 atan(x / (1 + sqrt(1 + x^2)))
  const x2 = x * x;
  let term = x, sum = 0;
  for (let n = 1; n < 40; n += 2) { sum += term / n; term *= -x2; }
  return sum * (1 << k);
}
const HALF_PI = 1.5707963267948966, PI = 3.141592653589793;
function atan2(y, x) {
  if (x === 0 && y === 0) return 0;
  if (Math.abs(x) >= Math.abs(y)) { const a = atan(y / x); return x > 0 ? a : y >= 0 ? a + PI : a - PI; }
  const a = atan(x / y);
  return y > 0 ? HALF_PI - a : -HALF_PI - a;
}
const clip = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
const sign = (v) => (v > 0 ? 1 : v < 0 ? -1 : 0);

// ---------------------------------------------------------------------------------------------- settings
// The settings file in sections; the rules read them as one flat set of names.
export function flatSettings(S) {
  const P = {};
  for (const sec of ["bench", "benchDefaults", "rules"]) for (const [k, v] of Object.entries(S[sec])) if (!k.startsWith("_")) P[k] = v;
  P.PPL = S.pointsPerLength; P.HORSE = S.horse; P.EFFORT = S.effort; P.EVENTS = S.events; P.AFTER = S.afterLine; P.FIELD = S.testField;
  return P;
}

// ---------------------------------------------------------------------------------------------- the course
// Which par time a race uses: the entry in the standards file for its course and distance.
export function standardFor(standards, course, distance) {
  const kind = course === "straight" ? "straight" : course === "roundMile" ? "roundMile" : "round";
  const same = standards.parTimes.filter((p) => p.course === kind);
  if (!same.length) throw new Error(`No par times for the ${kind} course`);
  return same.reduce((a, b) => (Math.abs(b.distance - distance) < Math.abs(a.distance - distance) ? b : a));
}

// The bends a race meets, as [metres to go where it starts, where it ends, angle turned (radians)], from the round
// course's inside rail in courses/ascot.json. A race that starts, or joins the loop (the round mile from the chute),
// part-way round a bend gets that share of its turn, as the bench does.
export function bendsFor(course, kind, distance) {
  if (kind === "straight") return { bends: [], home: 0 };
  const rc = course.roundCourse, pts = rc.insideRail.points, sp = rc.insideRail.spacing, n = pts.length, L = n * sp;
  const heading = (d) => {                                  // running direction at d metres to go on the loop
    const s = (((-d) % L) + L) % L, i = Math.round(s / sp) % n;
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n];
    return atan2(b[1] - a[1], b[0] - a[0]);
  };
  const turned = (from, to) => {                            // angle turned along the rail from 'from' to 'to'
    let tot = 0;
    for (let d = from; d > to + 1e-9; d -= sp) {
      const e = Math.max(to, d - sp);
      let a = heading(e) - heading(d);
      while (a > PI) a -= 2 * PI; while (a < -PI) a += 2 * PI;
      tot += a;
    }
    return Math.abs(tot);
  };
  const loop = rc.bends.map((b) => [b.from, b.to, turned(b.from, b.to)]);
  const join = kind === "roundMile" ? course.roundMileSpur.distanceToGoAtJoin : Infinity;
  const bends = [];
  for (let k = 0; k < 3; k++) for (const [a0, b0, ang0] of loop) {
    let A = a0 + k * L, B = b0 + k * L, ang = ang0;
    const top = Math.min(distance, join);
    if (B >= top) continue;
    if (A > top) { ang *= (top - B) / (A - B); A = top; }
    bends.push([A, B, ang]);
  }
  bends.sort((p, q) => q[0] - p[0]);
  return { bends, home: Math.min(...rc.bends.map((b) => b.to)) };   // the home straight starts where the last bend ends
}

// ---------------------------------------------------------------------------------------------- the runners
const PACE_NAMES = ["slow", "even", "strong", "fast"];
function paceLevel(P, frontShare, onPaceShare) {
  if (frontShare <= P.PACE_SLOW_FRONT) return 0;
  if (frontShare >= P.PACE_FAST_FRONT || onPaceShare >= P.PACE_FAST_ON_PACE) return 3;
  return frontShare > P.PACE_STRONG_FRONT ? 2 : 1;
}
const indexOf = (list, v, what) => {
  if (typeof v === "number") return v;
  const i = list.indexOf(String(v).toLowerCase().replace(/[^a-z]/g, ""));
  if (i < 0) throw new Error(`Unknown ${what}: ${v}`);
  return i;
};
// The pace a racecard promises, from the runners' running styles alone (as the jockeys read it before the off):
// "slow", "even", "strong" or "fast". For the game's race-day pace forecast; the race itself works it out the same way.
export function expectedPace(settings, styles) {
  const P = flatSettings(settings), s = styles.map((x) => indexOf(P.HORSE.STYLES, x, "style")), n = s.length || 1;
  return PACE_NAMES[paceLevel(P, s.filter((v) => v === 0).length / n, s.filter((v) => v <= 1).length / n)];
}
// Steps on the trip ladder for a race distance (furlongs to the nearest rung).
function tripStep(H, metres) {
  const f = metres / 201.168;
  let best = 0;
  H.TRIP_LADDER_FURLONGS.forEach((r, i) => { if (Math.abs(r - f) < Math.abs(H.TRIP_LADDER_FURLONGS[best] - f)) best = i; });
  return best;
}
// Race-day rating before form, and where the race sits in the horse's trip (the "shade").
export function raceDayRating(P, runner, race) {
  const H = P.HORSE;
  let r = runner.rating, steps = 0, shade = 0, ground = 0;
  if (runner.trip) {
    const at = tripStep(H, race.distance);
    const lo = H.TRIP_LADDER.indexOf(runner.trip[0]), hi = H.TRIP_LADDER.indexOf(runner.trip[runner.trip.length - 1]);
    if (lo < 0 || hi < 0) throw new Error(`Unknown trip: ${runner.trip}`);
    steps = at < lo ? lo - at : at > hi ? at - hi : 0;
    // a 7f/1m type in a mile (the race at the top of its trip, or beyond it) has a shade more sprint; a 1m/1m1f type
    // (the race at the bottom of its trip, or below it) a shade more tank
    shade = lo === hi ? 0 : at >= hi ? 1 : at <= lo ? -1 : 0;
  }
  if (runner.goings && runner.goings.length) {
    const g = H.GOING_LADDER.indexOf(race.going || "Good");
    const away = Math.min(...runner.goings.map((x) => Math.abs(H.GOING_LADDER.indexOf(x) - g)));
    ground = H.GROUND_POINTS[Math.min(away, H.GROUND_POINTS.length - 1)];
  }
  r += -H.TRIP_STEP_POINTS * steps + ground;
  if (race.handicap && runner.mark != null) r = (race.handicapBase ?? H.HANDICAP_BASE) + (r - runner.mark);
  if (runner.shade != null) shade = runner.shade;
  return { rating: r, tripSteps: steps, ground, shade };
}

// ---------------------------------------------------------------------------------------------- the race
export function runRace(race, runners, data, options = {}) {
  const keepFrames = options.timeline !== false;                 // { timeline: false } for bulk checks: the result only
  const P = flatSettings(data.settings);
  const n = runners.length;
  const start = data.stalls.starts[race.start];
  if (!start) throw new Error(`No start '${race.start}' in the stalls file`);
  if (n < 1 || n > data.stalls.maxRunners) throw new Error(`Field of ${n}: 1 to ${data.stalls.maxRunners} runners`);
  const rnd = makeRandom(race.seed ?? 1);
  const D = race.distance, kind = race.course === "straight" ? "straight" : race.course === "roundMile" ? "roundMile" : "round";
  const straight = kind === "straight";
  const W = data.course.trackWidth, MID = W / 2, Z0 = P.RAIL_CLEAR, Z1 = W - P.RAIL_CLEAR;
  const { bends, home } = bendsFor(data.course, kind, D);
  const join = bends.length ? bends[0][0] : D;
  const std = standardFor(data.standards, race.course, D);
  const goingName = data.standards.going[race.going] ? race.going : "Good";
  const going = data.standards.going[goingName];
  const PAR = (D / std.seconds) * P.PAR_FUDGE * going.speed;    // the par speed on the day
  const tscale = D / PAR / P.TANK_REF_SECONDS;                 // race length against the mile the settings were tuned on
  const ppl = P.PPL[std.key] ?? 2.0;
  const S = P.LENGTH / (ppl * D);                              // speed per rating point, as a share of par
  const CHECK_DV = P.CHECK_DV_BY_COURSE[straight ? "straight" : "round"];
  const H = P.HORSE;

  // --- the runners as they go to post
  const card = runners.map((r, i) => {
    const day = raceDayRating(P, r, { ...race, going: goingName });
    return {
      i, draw: i + 1, name: r.name || `No. ${i + 1}`,
      style: indexOf(H.STYLES, r.style ?? 1, "style"),
      flex: indexOf(H.FLEX, r.flex ?? 1, "flexibility"),
      keen: String(r.temperament || "calm").toLowerCase() === "keen",
      dayRating: day.rating, shade: day.shade, tripSteps: day.tripSteps, ground: day.ground,
      jockey: r.jockey, instruction: r.instruction,
      z: start.stalls[i].fromInsideRail,
    };
  });
  // form on the day: a small everyday wobble, an occasional big day, a rarer flop
  for (const c of card) {
    let f = rnd.normal(0, P.FORM_SD);
    if (rnd.chance(P.UP_P)) f += rnd.uniform(P.UP_MIN, P.UP_MAX);
    if (rnd.chance(P.FLOP_P)) f -= rnd.uniform(P.FLOP_MIN, P.FLOP_MAX);
    c.form = f;
    c.skill = c.jockey != null ? P.JOCKEY_SKILL[0] + (P.JOCKEY_SKILL[1] - P.JOCKEY_SKILL[0]) * (clip(c.jockey, 1, H.JOCKEY_LEVELS) - 1) / (H.JOCKEY_LEVELS - 1)
      : rnd.uniform(P.JOCKEY_SKILL[0], P.JOCKEY_SKILL[1]);
  }
  // the jockeys read the likely pace from the racecard and, if the horse allows, ride it to suit
  const expected = paceLevel(P, card.filter((c) => c.style === 0).length / n, card.filter((c) => c.style <= 1).length / n);
  for (const c of card) {
    let shift = 0;
    const wantShift = expected === 0 ? -1 : expected >= 3 ? 1 : expected === 2 ? (rnd.chance(0.5) ? 1 : 0) : 0;
    const reads = rnd.chance(P.JOCKEY_READ);
    if (reads && c.flex > 0) shift = wantShift;
    if (c.keen && shift > 0) shift = 0;                      // a keen horse won't settle further back
    if (c.flex === 2 && reads && rnd.chance(P.DOUBLE)) shift *= 2;
    c.ridden = clip(c.style + shift, 0, 3);
    if (c.instruction != null && c.instruction !== "jockey") {   // the trainer's instruction overrides the jockey
      const want = indexOf(H.STYLES, c.instruction, "instruction"), reach = H.INSTRUCTION_REACH[H.FLEX[c.flex]];
      c.ridden = want;
      if (Math.abs(want - c.style) > reach) c.keen = true;     // pushed past its flexibility it races keenly
    }
  }
  // the break (owner, 5 Nov): most within a length of each other; about 1 in 50 misses it and loses several lengths,
  // keen (fractious) horses far more often than calm ones; a horse ridden to be held up comes out a touch slower
  for (const c of card) {
    c.react = rnd.uniform(P.BREAK_MIN, P.BREAK_MAX);
    c.missed = rnd.chance(c.keen ? P.MISS_P_KEEN : P.MISS_P_CALM);
    if (c.missed) c.react += rnd.uniform(P.MISS_MIN, P.MISS_MAX);
    if (c.ridden === 3) c.react += P.HOLDUP_SLOW;
  }
  // groups on the straight course, contiguous by draw
  let groups = 1;
  if (straight) {
    const row = P.SPLIT.table.find((t) => n <= t[0]) || P.SPLIT.table[P.SPLIT.table.length - 1];
    const r = rnd.next();
    groups = r < row[1] ? 3 : r < row[2] ? 2 : 1;
    groups = Math.min(groups, n);
  }
  const base = Math.floor(n / groups), extra = n % groups;   // as numpy's array_split
  let at = 0;
  for (let g = 0; g < groups; g++) { const size = base + (g < extra ? 1 : 0); for (let k = 0; k < size; k++) card[at++].group = g; }
  const groupInfo = Array.from({ length: groups }, (_, g) => {
    const m = card.filter((c) => c.group === g);
    const mz = m.reduce((s, c) => s + c.z, 0) / m.length;
    return {
      centre: mz + (MID - mz) * P.GROUP_PULL_MIDDLE,
      pace: paceLevel(P, m.filter((c) => c.ridden === 0).length / m.length, m.filter((c) => c.ridden <= 1).length / m.length),
      draws: m.map((c) => c.draw),
    };
  });
  const paceAll = paceLevel(P, card.filter((c) => c.ridden === 0).length / n, card.filter((c) => c.ridden <= 1).length / n);
  const paceScale = straight ? 1 : P.PACE_ROUND_SCALE;          // bends steady the pace: less extreme both ways
  const paceA = P.PACE.map((p) => 1 + (p - 1) * paceScale);
  const paceNoise = 1 + rnd.normal(0, P.PACE_NOISE);

  // --- each horse's numbers for the race
  const x = new Float64Array(n).fill(-data.stalls.horseStandsBehind), z = new Float64Array(n), v = new Float64Array(n), vz = new Float64Array(n);
  const E = new Float64Array(n), fin = new Float64Array(n).fill(NaN), finV = new Float64Array(n);
  const vp = new Float64Array(n), vR = new Float64Array(n), vC = new Float64Array(n), ref = new Float64Array(n), vK0 = new Float64Array(n), burst = new Float64Array(n);
  const settle = new Float64Array(n), follow = new Float64Array(n), own = new Float64Array(n), kickAt = new Float64Array(n), R = new Float64Array(n), E0 = new Float64Array(n);
  const switchT = new Float64Array(n), switchDir = new Float64Array(n), since = new Float64Array(n).fill(9), lost = new Float64Array(n), blockedT = new Float64Array(n);
  for (const c of card) {
    const i = c.i, gi = groupInfo[c.group];
    z[i] = c.z;
    R[i] = c.dayRating + c.form + P.RUN_BOOST[gi.pace][c.ridden];
    vp[i] = (PAR * paceA[gi.pace] * (1 - P.GROUP_WATCH) + PAR * paceA[paceAll] * P.GROUP_WATCH) * paceNoise;
    vR[i] = PAR * (1 + (R[i] - P.RATING_REF) * S);
    vC[i] = vR[i] * P.COMFORT; ref[i] = (1 - P.COMFORT) * vR[i]; vK0[i] = vR[i] * P.TOP;
    burst[i] = vR[i] * (P.BURST + P.SHADE_TOP * c.shade + P.BURST_STYLE[c.ridden] * pow(D / P.MILE, P.BURST_DIST_EXP));
    E[i] = E0[i] = (P.TANK * tscale / going.sapping) * (1 - P.SHADE_TANK * c.shade);
    settle[i] = P.SETTLE[c.ridden]; follow[i] = P.FOLLOW[c.ridden]; own[i] = vR[i] * P.OWN;
    kickAt[i] = clip(P.KICK_FROM / P.MILE * D, P.KICK_MIN, P.KICK_MAX) + rnd.normal(0, P.JUDGE_SD);
  }

  // --- run it
  const dt = 0.1, BL = P.BODY_L, BW = P.BODY_W, SW = P.SIDE_W;
  const EF = P.EFFORT, EV = P.EVENTS, AF = P.AFTER;
  const frames = [];
  const want = new Float64Array(n), freeWant = new Float64Array(n), vfront = new Float64Array(n), kick = new Uint8Array(n), inB = new Uint8Array(n), blocked = new Uint8Array(n);
  const live = new Uint8Array(n), rank = new Int32Array(n), held = new Uint8Array(n), kap = new Float64Array(n);
  const xcap = new Float64Array(n), vcap = new Float64Array(n), effort = new Uint8Array(n), vNew = new Float64Array(n), arrive = new Float64Array(n), projected = new Int32Array(n), spare = new Float64Array(n), holdV = new Float64Array(n);
  const order = Array.from({ length: n }, (_, i) => i);
  const events = [], kickedAt = new Float64Array(n).fill(NaN);
  const ev = { leader: -1, cand: -1, candT: 0, lastSwitch: new Float64Array(n).fill(-99), room: new Float64Array(n), roomFrom: new Float64Array(n).fill(NaN), roomLast: [], spells: [], weak: new Uint8Array(n) };
  const pushFrame = () => keepFrames && frames.push(Array.from({ length: n }, (_, i) => [
    +x[i].toFixed(3), +(z[i] - MID).toFixed(3), +v[i].toFixed(3), effort[i], +atan2(vz[i], Math.max(v[i], 1)).toFixed(4)]));
  pushFrame();
  let t = 0, winT = Infinity, lastT = -Infinity;
  const tLimit = D / P.TIME_LIMIT_SPEED + P.TIME_LIMIT_EXTRA;
  const lenNow = (m) => m / P.LENGTH;
  const closeRoom = (i) => {                                    // the end of a spell short of room
    if (Number.isNaN(ev.roomFrom[i])) return;
    const last = ev.roomLast[i];
    if (last && ev.roomFrom[i] - last.until <= EV.ROOM_MERGE_S) { last.lost += ev.room[i]; last.until = t; }   // one spell, held up again
    else ev.spells.push(ev.roomLast[i] = { t: ev.roomFrom[i], until: t, lost: ev.room[i], runner: i });
    ev.roomFrom[i] = NaN; ev.room[i] = 0;
  };
  while (t < tLimit) {
    let anyLive = false;
    for (let i = 0; i < n; i++) { live[i] = Number.isNaN(fin[i]) ? 1 : 0; if (live[i]) anyLive = true; }
    if (!anyLive && t >= Math.max(lastT + AF.RUN_OUT_S, winT + AF.AFTER_WINNER_S)) break;
    // the running order (everyone, as the bench ranks them)
    order.sort((a, b) => x[b] - x[a] || a - b);
    for (let k = 0; k < n; k++) rank[order[k]] = k;

    // ---- what each horse wants (energy and pace)
    for (let i = 0; i < n; i++) {
      const toGo = D - x[i];
      const cruise = vp[i] <= own[i] ? vp[i] : follow[i] * vp[i] + (1 - follow[i]) * own[i];
      let w = x[i] < P.EARLY ? vp[i] * (1 - settle[i]) : cruise;
      const T = Math.max(toGo, 1) / Math.max(v[i], P.HOLD_MIN_SPEED);
      const hold = vC[i] + ref[i] * Math.sqrt(Math.max(E[i], 0) / (ref[i] * T));
      kick[i] = toGo <= kickAt[i] ? 1 : 0;
      inB[i] = kick[i] && toGo <= P.BURST_DIST && E[i] > P.BURST_NEEDS ? 1 : 0;
      if (kick[i]) w = Math.min(vK0[i], hold) + (inB[i] ? burst[i] : 0);
      if (t < card[i].react) w = 0;
      want[i] = w;
    }
    // ---- who is around whom (live horses only)
    for (let i = 0; i < n; i++) {
      if (!live[i]) continue;
      const toGo = D - x[i];
      let vf = Infinity, occOut = false, occIn = false, trouble = false, rep = 0, inlane = false, sideOut = false, sideIn = false, alongside = false, covered = false;
      const zo = z[i] + P.LANE_STEP, zi = z[i] - P.LANE_STEP;
      for (let j = 0; j < n; j++) {
        if (j === i || !live[j]) continue;
        const dx = x[j] - x[i], dz = z[j] - z[i], adz = Math.abs(dz), adx = Math.abs(dx);
        if (dx > 0 && dx < BL && adz < BW && v[j] < vf) vf = v[j];
        if (dx > -P.GAP_BEHIND && dx < P.GAP_AHEAD) { if (Math.abs(z[j] - zo) < BW) occOut = true; if (Math.abs(z[j] - zi) < BW) occIn = true; }
        if (dx > 0 && dx < P.SEE_AHEAD && adz < BW) trouble = true;
        if (adx < BL && adz < P.REPEL_W) rep += -sign(dz + 1e-6) * (P.REPEL_W - adz) * P.REPEL_GAIN;
        if (dx > 0 && dx < P.FAN_LOOK && adz < P.FAN_LANE_W) inlane = true;
        if (adx < BL && dz > 0 && dz < SW) sideOut = true;
        if (adx < BL && dz < 0 && dz > -SW && dx > -P.CUT_IN) sideIn = true;
        if (adx < BL && dz < 0 && dz > -P.ALONGSIDE_W) alongside = true;
        if (dx > P.DRAFT_MIN_DX && dx < P.DRAFT_LEN && adz < P.DRAFT_W) covered = true;
      }
      vfront[i] = vf;
      blocked[i] = Number.isFinite(vf) && want[i] > vf + P.BLOCK_MARGIN && x[i] > P.BLOCK_FROM ? 1 : 0;
      freeWant[i] = want[i];
      if (blocked[i]) { want[i] = Math.min(want[i], vf); blockedT[i] += dt; }
      // looking for a gap: the lane a horse-width to each side must be clear from a little behind to a length or so ahead
      const cOut = !occOut && zo > Z0 && zo < Z1, cIn = !occIn && zi > Z0 && zi < Z1;
      const seek = blocked[i] || (trouble && kick[i]);
      const classk = clip(1 + P.CLASS_LOOK * (R[i] - P.RATING_REF), P.CLASS_LOOK_RANGE[0], P.CLASS_LOOK_RANGE[1]);
      let started = false;
      if (seek && switchT[i] <= 0 && rnd.next() < (kick[i] ? card[i].skill * P.KICK_LOOK : card[i].skill) * classk) {
        const prefOut = straight ? rnd.next() < P.PREF_OUT_STRAIGHT : true;
        const dirn = cOut && (prefOut || !cIn) ? 1 : cIn ? -1 : 0;
        if (dirn !== 0) { switchDir[i] = dirn; switchT[i] = P.SWITCH_TIME; started = true; }
      }
      if (!started) switchT[i] -= dt;
      if (started && kick[i] && blocked[i] && t - ev.lastSwitch[i] > EV.SWITCH_GAP_S) {
        ev.lastSwitch[i] = t;
        events.push({ t, toGo, kind: "switched", runner: i, side: switchDir[i] > 0 ? "out" : "in" });
      }
      // ---- steering
      let tz;
      if (straight) tz = groupInfo[card[i].group].centre;
      else {
        // down the chute they hold their lines, drifting in gently; from the join they want the rail;
        // in the home straight only the leaders keep the rail, the rest hold their line and angle out for room
        tz = toGo > join ? Z0 + (z[i] - Z0) * P.CHUTE_AIM : Z0;
        if (toGo < home && rank[i] >= P.LEADERS_ON_RAIL) tz = z[i];
      }
      let az = clip((tz - z[i]) * P.STEER_GAIN, -P.STEER_MAX, P.STEER_MAX);
      const fanSide = straight ? (z[i] >= tz ? 1 : -1) : 1;
      const clearFan = fanSide > 0 ? cOut : cIn;
      if (inlane && clearFan && toGo < P.FAN_FROM && rank[i] >= 1 && (!straight || P.FAN_STRAIGHT > 0)) az = fanSide * P.FAN_RATE;
      const vzt = switchT[i] > 0 ? switchDir[i] * P.SWITCH_SPEED : az + rep;
      const free = clip((x[i] - P.FREE_FROM) / P.FREE_OVER, 0, 1);
      let nvz = clip(vz[i] + (vzt - vz[i]) * P.VZ_BLEND, -P.VZ_MAX * free, P.VZ_MAX * free);
      if (sideOut && nvz > 0) nvz = 0;
      if (sideIn && nvz < 0) nvz = 0;
      vz[i] = nvz;
      if (!straight) {
        const settling = z[i] > P.SETTLE_WIDE && alongside && toGo <= join + P.SETTLE_FROM && toGo > home && !kick[i] && x[i] > P.SETTLE_MIN_X;
        if (settling) want[i] *= card[i].ridden >= 2 ? 1 - P.EASE : 1 + P.PUSH;
        if (blocked[i]) want[i] = Math.min(want[i], vfront[i]);
      }
      if (switchT[i] > 0 && kick[i]) want[i] *= 1 - P.SWITCH_COST;
      // ---- speed and energy
      const acc = v[i] < P.ACC_START_BELOW ? P.ACC_START : P.ACC * clip(1 + P.CLASS_ACC * (R[i] - P.RATING_REF), P.ACC_CLASS[0], P.ACC_CLASS[1]);
      vNew[i] = v[i] + clip(want[i] - v[i], -P.DECEL * dt, acc * dt);    // applied after every horse has looked round
      const over = Math.max(vNew[i] - (inB[i] ? burst[i] : 0) - vC[i], 0), q = over / ref[i];
      E[i] -= ref[i] * q * q * dt * (covered ? 1 - P.DRAFT : 1) + (card[i].keen && vp[i] < own[i] && !kick[i] ? P.KEEN_BURN : 0) * dt;
      let k = 0;
      for (const [a, b, ang] of bends) if (toGo <= a && toGo > b) k = ang / (a - b);
      kap[i] = k;
    }
    for (let i = 0; i < n; i++) if (live[i]) v[i] = vNew[i];
    // finished horses: pulling up past the post (results are already settled; they only keep apart from each other)
    for (let i = 0; i < n; i++) {
      if (live[i]) continue;
      v[i] = Math.max(Math.min(v[i], AF.EASE_TO), v[i] - AF.PULL_UP * dt);
      vz[i] *= 0.9; kap[i] = 0; blocked[i] = 0;
    }
    for (let i = 0; i < n; i++) z[i] = clip(z[i] + vz[i] * dt, Z0, Z1);
    // no two horses in the same space: one that runs up behind another is held behind it
    for (let pass = 0; pass < P.COLLIDE_PASSES; pass++) {
      for (let i = 0; i < n; i++) {
        let xc = Infinity, vc = Infinity;
        for (let j = 0; j < n; j++) {
          if (j === i || live[j] !== live[i]) continue;     // the live race, and the pulled-up horses, separately
          const ddx = x[j] - x[i];
          if (ddx >= 0 && ddx < BL && Math.abs(z[j] - z[i]) < BW && (ddx > 0 || j < i)) { if (x[j] - BL < xc) xc = x[j] - BL; if (v[j] < vc) vc = v[j]; }
        }
        xcap[i] = xc; vcap[i] = vc;
      }
      for (let i = 0; i < n; i++) {
        const nx = Math.max(Math.min(x[i], xcap[i]), x[i] - P.MAX_CORR);
        x[i] = nx;
        if (Number.isFinite(vcap[i])) v[i] = Math.min(v[i], vcap[i] - (xcap[i] < nx + P.CHECK_TOUCH && live[i] ? CHECK_DV : 0));
      }
    }
    for (let i = 0; i < n; i++) {
      if (!live[i]) continue;
      held[i] = blocked[i] || Number.isFinite(vcap[i]) ? 1 : 0;
      since[i] = held[i] ? 0 : since[i] + dt;
      if (kick[i] && since[i] < P.LOST_RECOVER_S) {
        const l = Math.max(freeWant[i] - v[i], 0) * dt;
        lost[i] += l;
        if (held[i] && Number.isNaN(ev.roomFrom[i])) ev.roomFrom[i] = t;     // a spell short of room starts
        if (!Number.isNaN(ev.roomFrom[i])) ev.room[i] += l;
      } else closeRoom(i);

      if (kick[i] && Number.isNaN(kickedAt[i])) kickedAt[i] = t;
    }
    for (let i = 0; i < n; i++) x[i] += v[i] * dt / (1 + kap[i] * (z[i] - Z0));
    t = Math.round((t + dt) * 1e6) / 1e6;
    for (let i = 0; i < n; i++) if (live[i] && x[i] >= D) {
      fin[i] = t - (x[i] - D) / Math.max(v[i], P.FINISH_MIN_SPEED); finV[i] = v[i];
      if (fin[i] < winT) winT = fin[i];
      closeRoom(i);
      lastT = Math.max(lastT, fin[i]);
    }

    // ---- effort for the race view (what the jockey is doing), and the events
    order.sort((a, b) => x[b] - x[a] || a - b);
    const leadX = x[order[0]];
    // What the jockey can feel: how much his horse has left (the share of its top speed, over comfort, that its
    // energy will hold to the line), against the rest of the field; and where it would finish from here if every
    // horse kept going as it can. A tiring horse is ridden; one that is going nowhere is ridden; one that is
    // travelling well, or will hold or gain its place, waits.
    const spares = [];
    for (let i = 0; i < n; i++) {
      const T = Math.max(D - x[i], 1) / Math.max(v[i], P.HOLD_MIN_SPEED);
      const hold = vC[i] + ref[i] * Math.sqrt(Math.max(E[i], 0) / (ref[i] * T));
      arrive[i] = Math.max(D - x[i], 0) / Math.min(vK0[i], hold);          // seconds to the line at that speed
      spare[i] = (hold - vC[i]) / (vK0[i] - vC[i]);
      holdV[i] = Math.min(vK0[i], hold);
      if (Number.isNaN(fin[i])) spares.push(spare[i]);
    }
    spares.sort((a, b) => a - b);
    const midSpare = spares.length ? spares[spares.length >> 1] : 0;
    const byArrival = order.filter((i) => Number.isNaN(fin[i])).sort((p, q) => arrive[p] - arrive[q] || p - q);
    byArrival.forEach((i, k) => (projected[i] = k));
    const doneCount = n - byArrival.length;
    for (let i = 0; i < n; i++) {
      const toGo = D - x[i];
      if (!Number.isNaN(fin[i]) || t < card[i].react || v[i] < 1) { effort[i] = 0; continue; }
      const behindL = (leadX - x[i]) / P.LENGTH;
      const place = rank[i] - doneCount, proj = projected[i];
      const tiring = spare[i] < midSpare - EF.TIRED || !kick[i] && v[i] > holdV[i] * (1 + EF.OVER_HOLD);   // less left than its rivals, or going faster than it can last
      const nowhere = proj >= EF.CONTEND && proj >= place && behindL > EF.CHASE_LENGTHS;   // won't get into the race as it is
      const chasing = paceAll <= EF.SLOW_PACE && behindL > EF.CHASE_LENGTHS && place >= EF.CHASE_FROM * (n - doneCount);   // slowly run: the leaders won't come back
      const underPressure = tiring || nowhere;
      let e;
      if (!kick[i]) {
        // cruising, even at a strong pace; pushed only while working to make up ground (after a check, or across to a place)
        e = x[i] > P.EARLY && v[i] > vC[i] && want[i] - v[i] > EF.CATCH_UP ? 1 : 0;
        if (toGo <= kickAt[i] + EF.EARLY_FROM && x[i] > P.EARLY && (underPressure || chasing)) e = 1;   // getting busy early
      } else {
        // the run for home: driven if under pressure or near the line; a horse travelling well waits
        e = underPressure || chasing || toGo < kickAt[i] * EF.WAIT_SHARE ? 2 : 1;
        let close = false;
        if (toGo < EF.CLOSE_FROM) for (let j = 0; j < n; j++) if (j !== i && Number.isNaN(fin[j]) && Math.abs(x[j] - x[i]) < EF.CLOSE_LENGTHS * P.LENGTH) close = true;
        if (E[i] < EF.EMPTY * E0[i] || close) e = 3;
        if (toGo < EF.BEATEN_FROM && behindL > EF.BEATEN_LENGTHS) e = Math.min(e, 2);
      }
      effort[i] = e;
      // weakening: one of the leaders, out of energy and down to its comfort speed in the run for home
      if (kick[i] && !ev.weak[i] && rank[i] < EV.WEAK_PLACES && E[i] <= 0 && v[i] <= vC[i] * 1.001) {
        ev.weak[i] = 1; events.push({ t, toGo, kind: "weakening", runner: i, place: rank[i] + 1 });
      }
    }
    // the lead (from LEAD_FROM metres, once a new leader has held it for LEAD_HOLD_S)
    const L0 = order[0];
    if (leadX >= EV.LEAD_FROM && leadX < D) {
      if (ev.leader < 0) { ev.leader = L0; events.push({ t, toGo: D - leadX, kind: "led", runner: L0 }); }
      else if (L0 !== ev.leader) {
        if (ev.cand !== L0) { ev.cand = L0; ev.candT = t; }
        else if (t - ev.candT >= EV.LEAD_HOLD_S) { events.push({ t: ev.candT, toGo: null, kind: "lead change", runner: L0, from: ev.leader }); ev.leader = L0; ev.cand = -1; }
      } else ev.cand = -1;
    }
    pushFrame();
  }

  // ---- the result
  const fins = card.map((c) => c.i).sort((a, b) => fin[a] - fin[b]);
  const winner = fins[0];
  const lenAt = (i) => (fin[i] - fin[winner]) * finV[i] / P.LENGTH;
  const placed = fins.map((i, k) => {
    const c = card[i];
    return {
      place: k + 1, runner: i, draw: c.draw, name: c.name,
      time: +fin[i].toFixed(3),
      margin: k ? +((fin[i] - fin[fins[k - 1]]) * finV[i] / P.LENGTH).toFixed(2) : 0,   // lengths behind the one in front
      behind: +lenAt(i).toFixed(2),                                                    // lengths behind the winner
      style: H.STYLES[c.style], ridden: H.STYLES[c.ridden], group: c.group,
      dayRating: c.dayRating, form: +c.form.toFixed(2), lostLengths: +(lost[i] / P.LENGTH).toFixed(2),
    };
  });
  // the events, in order, with the kicks that mattered and only the weakening that cost places
  for (const sp of ev.spells) if (lenNow(sp.lost) >= EV.ROOM_MIN_LENGTHS) events.push({ t: sp.t, toGo: null, kind: "short of room", runner: sp.runner, lengths: +lenNow(sp.lost).toFixed(2) });
  const placeOf = new Map(placed.map((p) => [p.runner, p.place]));
  for (const c of card) if (c.missed) events.push({ t: 0, toGo: D, kind: "missed the break", runner: c.i });
  const firstKick = card.map((c) => c.i).filter((i) => !Number.isNaN(kickedAt[i])).sort((a, b) => kickedAt[a] - kickedAt[b])[0];
  for (const i of new Set([firstKick, winner])) if (i != null && !Number.isNaN(kickedAt[i])) events.push({ t: kickedAt[i], toGo: null, kind: "kicked", runner: i, first: i === firstKick });
  const kept = events.filter((e) => {
    if (e.kind === "weakening") return placeOf.get(e.runner) - e.place >= EV.WEAK_LOST;
    if (e.kind === "switched") return placeOf.get(e.runner) <= EV.NOTE_PLACES;
    if (e.kind === "short of room") return placeOf.get(e.runner) <= EV.NOTE_PLACES || e.lengths >= EV.ROOM_BIG_LENGTHS;
    return true;
  });
  for (const e of kept) {
    e.t = +e.t.toFixed(1);
    if (e.toGo == null) e.toGo = D - (keepFrames ? frames[Math.min(frames.length - 1, Math.round(e.t / dt))][e.runner][0] : x[e.runner]);
    e.toGo = Math.max(0, Math.round(e.toGo));
    e.text = describe(e, (i) => card[i].name);
  }
  kept.sort((a, b) => a.t - b.t);
  const result = {
    race: { course: race.course, distance: D, key: std.key, going: goingName, seed: race.seed ?? 1, runners: n, handicap: !!race.handicap },
    order: fins, placed,
    winner, winningTime: +fin[winner].toFixed(2), parTime: +(std.seconds / going.speed).toFixed(2), parSpeed: PAR,
    pace: { expected: PACE_NAMES[expected], run: PACE_NAMES[paceAll], groups: groupInfo.map((g) => ({ draws: g.draws, pace: PACE_NAMES[g.pace] })) },
    events: kept,
  };
  return { timeline: { dt, frames }, result };
}

function describe(e, name) {
  const who = name(e.runner), where = e.toGo >= 201 ? `${(e.toGo / 201.168).toFixed(1).replace(/\.0$/, "")}f out` : `${Math.round(e.toGo * 1.0936)} yds out`;
  switch (e.kind) {
    case "missed the break": return `${who} missed the break`;
    case "led": return `${who} leads early`;
    case "lead change": return `${who} takes the lead from ${name(e.from)}, ${where}`;
    case "short of room": return `${who} short of room, ${where} (about ${e.lengths.toFixed(1)} L lost)`;
    case "switched": return `${who} switched ${e.side === "out" ? "out" : "to the inside"}, ${where}`;
    case "kicked": return `${who} ${e.first ? "kicks first" : "kicks"}, ${where}`;
    case "weakening": return `${who} weakening, ${where}`;
    default: return `${who}: ${e.kind}`;
  }
}
