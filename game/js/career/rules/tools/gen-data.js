// Builds ../data.js for the rules and the reference game, from the live game's own data (stallions, mares, names, silks, Royal Ascot)
// and ../reference/big-races.txt (a compact copy of tools/calendar/big_races.txt).   node gen-data.js
const fs = require('fs'), path = require('path');
const REPO = process.argv[2] || path.join(__dirname, '../../../../..');
const rules = fs.readFileSync(path.join(REPO, 'game/js/rules.js'), 'utf8');
const TRIP = { '5f': 0, '6f': 1, '7f': 2, '1m': 3, '1m2f': 4, '1m4f': 5, '1m6f': 6, '2m+': 7 };
const GO = { Heavy: 0, Softer: 1, Good: 2, Quicker: 3, Quick: 4 };
const rows = JSON.parse(rules.match(/const PROFILE_ROWS = (\[.*?\]);/s)[1]).map(r => r.split('|'));
const RET = new Set(JSON.parse(rules.match(/const RETIRED = new Set\((\[.*?\])\)/s)[1]));
const prof = r => { const g = r[8].split('/').map(x => GO[x]); return { n: r[0], stars: +r[2], opt: Math.min(6, TRIP[r[4]]), peak: { '2YO': 'e', '3YO': 'n', '4YO': 'l' }[r[7]], gr: [Math.min(...g), Math.max(...g)], fee: +(r[10] || '').replace(/[^\d]/g, '') || 0 }; };
const stallions = rows.filter(r => r[1] === '1' && !RET.has(r[0])).map(prof).sort((a, b) => b.fee - a.fee || b.stars - a.stars);
const mares = rows.filter(r => r[1] !== '1').map(prof);
const NA = JSON.parse(rules.match(/const NAME_A = (\[.*?\]);/s)[1]), NB = JSON.parse(rules.match(/const NAME_B = (\[.*?\]);/s)[1]);
const sj = require(path.join(REPO, 'silks/silks.json'));
const PAT = { 'epaulets': 'epaulets', 'chevron': 'chevron', 'disc': 'disc', 'hooped band': 'hoop', 'sash': 'sash', 'crossbelts': 'cross', 'inverted chevron': 'chevron', 'seams': 'seams', 'triple diamond': 'diamond', 'three spots': 'spots', 'quartered': 'quartered', 'cross of lorraine': 'strip', 'halved': 'halved', 'strip': 'strip' };
const col = c => sj.palette[c] || '#888888';
const silks = sj.silks.map(s => ({ b: col(s.body.colour), b2: col(s.body.colour2 || s.sleeves.colour2 || s.cap.colour), p: PAT[s.body.pattern] || 'plain', s: col(s.sleeves.colour), c: col(s.cap.colour), t: s.tier }));
// Royal Ascot from the game's own meeting file
const ra = fs.readFileSync(path.join(REPO, 'game/js/meetings/royal-ascot.js'), 'utf8');
const pool = [...ra.matchAll(/\{ id: "[^"]+", day: (\d), name: "([^"]+)", grade: "([^"]+)", f: (\d+)[^}]*ages: \[(\d), (\d)\][^}]*?(?:sex: "(\w)")?[^}]*\}/g)];
const RG = { 'Group 1': ['G1', 400], 'Group 2': ['G2', 130], 'Group 3': ['G3', 80], 'Listed': ['L', 60], 'Handicap': ['HH', 60], 'Conditions': ['C', 50] };
const DEF = { G1: 250, G2: 90, G3: 50, L: 30, HH: 50, H: 20, C: 12, M: 8 };
const big = Array.from({ length: 16 }, () => []);
const fn = (mm, dd) => Math.min(15, Math.floor((Date.UTC(2026, mm - 1, dd) - Date.UTC(2026, 2, 23)) / 864e5 / 14));
for (const line of fs.readFileSync(path.join(__dirname, '../reference/big-races.txt'), 'utf8').split('\n')) {
  if (!line || line[0] === '#') continue;
  if (line === 'ROYAL_ASCOT') { for (const m of pool) { const [g, p] = RG[m[3]]; const sexLabel = (ra.slice(m.index, m.index + m[0].length).match(/sex: "(\w)"/) || [])[1] || ''; big[6].push({ n: m[2], co: 'Ascot', g, f: +m[4], a: [+m[5], Math.min(7, +m[6])], sx: sexLabel, p: m[2] === 'Royal Hunt Cup' || m[2] === 'Wokingham Stakes' ? 110 : p, mt: 'Royal Ascot' }); } continue; }
  const [d, co, n, g, f, ages, sx, p] = line.split('|');
  const a0 = parseInt(ages), a = [a0, ages.includes('+') ? 7 : a0];
  big[fn(+d.slice(0, 2), +d.slice(2))].push({ n, co, g, f: +f, a, sx: sx || '', p: +p || DEF[g] });
}
const out = { stallions, mares, NA, NB, silks, big };
fs.writeFileSync(path.join(__dirname, '../data.js'), '(function(r){r.TBDATA=' + JSON.stringify(out) + ';})(typeof window!=="undefined"?window:globalThis);\n');
console.log('stallions', stallions.length, 'mares', mares.length, 'silks', silks.length, 'big races', big.map(b => b.length).join(','), 'RA', pool.length, 'bytes', fs.statSync(path.join(__dirname, '../data.js')).size);
