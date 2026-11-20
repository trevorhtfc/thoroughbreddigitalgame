// Thoroughbred career: the screens. Everything on screen is rebuilt from the game state after each tap.
(function () {
'use strict';
const T = TB, D = T.D, CLS = T.CLS, LAB = T.LAB, GO = T.GOINGS; let S = null;
const UI = { tab: 'yard', sheet: null, rd: null, toast: null, setup: null, after: null };
const KEY = 'tb-career-v1', app = document.getElementById('app');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = n => (n < 0 ? '−' : '') + '£' + Math.abs(Math.round(n)).toLocaleString('en-GB');
const mk = n => { const a = Math.abs(n), s = n < 0 ? '−' : ''; return s + '£' + (a >= 1e6 ? (a / 1e6).toFixed(2).replace(/\.?0+$/, '') + 'm' : a >= 10000 ? Math.round(a / 1000) + 'k' : a >= 1000 ? (a / 1000).toFixed(1).replace('.0', '') + 'k' : a); };
const he = h => h.sex === 'f' ? 'she' : 'he', him = h => h.sex === 'f' ? 'her' : 'him', his = h => h.sex === 'f' ? 'her' : 'his', He = h => h.sex === 'f' ? 'She' : 'He';
const ord = n => n + (n % 10 === 1 && n !== 11 ? 'st' : n % 10 === 2 && n !== 12 ? 'nd' : n % 10 === 3 && n !== 13 ? 'rd' : 'th');
const hash = s => { let x = 7; for (let i = 0; i < s.length; i++) x = (x * 31 + s.charCodeAt(i)) | 0; return x >>> 0; };
const starTxt = n => '★'.repeat(n) + '☆'.repeat(5 - n);
function save() { try { localStorage.setItem(KEY, JSON.stringify(T.S)); } catch (e) { /* storage may be off: the game still plays */ } }
function load() { try { const j = localStorage.getItem(KEY); if (j) { const g = JSON.parse(j); if (g && (g.v === 1 || g.v === 2) && g.fn) { T.use(g); return true; } } } catch (e) { } return false; }

// ---------------------------------------------------------------- little pieces
const PAL = ['#eff5f5', '#1d1d1d', '#2156a6', '#333f52', '#614a82', '#64c3ac', '#ed2f24', '#eea1c7', '#f0a53f', '#f2e93f', '#3f9745', '#9f3a5a'];
const PATS = ['plain', 'chevron', 'hoops', 'sash', 'cross', 'spots', 'halved', 'quartered', 'strip', 'disc', 'diamond', 'epaulets'];
function silk(sp, size) {
  const c2 = sp.b2, P = {
    chevron: `<path d="M11 17l9 8 9-8v6l-9 8-9-8z" fill="${c2}"/>`, hoops: `<path d="M11 18h18v4H11zM11 26h18v4H11z" fill="${c2}"/>`, hoop: `<path d="M11 21h18v6H11z" fill="${c2}"/>`,
    sash: `<path d="M12 14h5l12 19v3h-3z" fill="${c2}"/>`, cross: `<path d="M12 14h4l13 20v2h-4zM28 14h-4L11 34v2h4z" fill="${c2}"/>`, spots: `<g fill="${c2}"><circle cx="16" cy="19" r="2.2"/><circle cx="24" cy="19" r="2.2"/><circle cx="20" cy="25" r="2.2"/><circle cx="16" cy="31" r="2.2"/><circle cx="24" cy="31" r="2.2"/></g>`,
    halved: `<path d="M20 14h8l1 3v19h-9z" fill="${c2}"/>`, quartered: `<path d="M20 14h8l1 3v8h-9zM11 25h9v11h-9z" fill="${c2}"/>`, strip: `<path d="M17.5 14h5v22h-5z" fill="${c2}"/>`, disc: `<circle cx="20" cy="24" r="5.5" fill="${c2}"/>`,
    diamond: `<path d="M20 16l6 8-6 8-6-8z" fill="${c2}"/>`, epaulets: `<path d="M12 14h5v4h-6v-1zM23 14h5l1 3v1h-6z" fill="${c2}"/>`, seams: `<path d="M15 14h1.5v22H15zM23.5 14H25v22h-1.5z" fill="${c2}"/>` };
  return `<svg class="silk" width="${size}" height="${size}" viewBox="0 0 40 40" aria-hidden="true"><g stroke="rgba(0,0,0,.28)" stroke-width=".8" stroke-linejoin="round"><path d="M11 15l-6 4v13h5v-9l1-1z" fill="${sp.s}"/><path d="M29 15l6 4v13h-5v-9l-1-1z" fill="${sp.s}"/><path d="M12 14h16l1 3v19H11V17z" fill="${sp.b}"/></g>${P[sp.p] || ''}<path d="M12 14h16l1 3v19H11V17z" fill="none" stroke="rgba(0,0,0,.28)" stroke-width=".8"/><path d="M13 11a7 6.5 0 0114 0h4.5v2H13z" fill="${sp.c}" stroke="rgba(0,0,0,.28)" stroke-width=".8" stroke-linejoin="round"/></svg>`;
}
const chip = c => `<span class="cls cls-${c}">${CLS[c].s}</span>`;
const chance = v => `<span class="ch ch${v.lv}">${v.label}${v.unsure ? ' ?' : ''}</span>`;
const fitRow = f => `<span class="fit"><i class="f-${f.trip}${f.tripq ? ' unsure' : ''}">Trip</i><i class="f-${f.gr}${f.grq ? ' unsure' : ''}">Ground</i><i class="f-${f.tr}${f.trq ? ' unsure' : ''}">Track</i></span>`;
const goingTxt = co => T.isAW(co) ? 'All-weather' : GO[T.goingAt(co)];
const ages = r => (r.a[0] === r.a[1] ? r.a[0] + 'yo' : r.a[0] + 'yo+') + (r.sx === 'F' ? ' fillies' : r.sx === 'C' ? ' colts' : '');
const rtitle = r => r.big ? r.n : T.fLabel(r.f) + ' ' + r.n;
const rsub = r => `${r.co} · ${T.fLabel(r.f)} · ${T.isAW(r.co) ? 'All-weather' : GO[r.g != null ? r.g : T.goingAt(r.co)]} · ${T.TYPE[T.ctype(r.co)]}`;
function pstars(h, big) { const k = h.k, lo = T.potStar(k.pe - k.pw), hi = T.potStar(k.pe + k.pw); return `<span class="stars${big ? ' big' : ''}" style="--lo:${Math.min(100, lo * 20)}%;--hi:${Math.min(100, hi * 20)}%" title="Potential">★★★★★</span>`; }
function pword(h) { const k = h.k, lo = T.potStar(k.pe - k.pw), hi = T.potStar(k.pe + k.pw), a = T.potWord(lo), b = T.potWord(hi); return a === b ? a : hi - lo > 2.6 ? 'Could be anything' : a + ' to ' + b.toLowerCase(); }
const fbar = f => `<span class="fbar ${f >= 75 ? '' : f >= 50 ? 'w' : 'b'}"><b style="width:${f}%"></b></span>`;
const formTxt = h => h.form.length ? h.form.slice(-5).join('-') : 'Unraced';
const sexWord = h => h.sex === 'f' ? (h.age >= 4 ? 'mare' : 'filly') : (h.age >= 4 ? 'horse' : 'colt');
const oddsCls = t => { const p = t === 'Evens' ? 1 : (a => a[0] / a[1])(t.split('/').map(Number)); return p <= 4 ? '' : p <= 10 ? 'o2' : p < 25 ? 'o3' : 'o4'; };
function mtxt(b) { if (b < 0.08) return 'nse'; if (b < 0.15) return 'sh hd'; if (b < 0.3) return 'hd'; if (b < 0.6) return 'nk'; if (b >= 10) return Math.round(b) + ' L'; const q = Math.round(b * 4) / 4, w = Math.floor(q), fr = { 0: '', 0.25: '¼', 0.5: '½', 0.75: '¾' }[q - w]; return (w || '') + fr + ' L'; }
function note(h) {
  if (h.inj > 0) return `On the easy list. Back in ${h.inj} fortnight${h.inj > 1 ? 's' : ''}.`;
  if (h.fresh < 50) return `${He(h)} needs a rest. Run ${him(h)} now and we risk an injury.`;
  if (h.fresh < 72) return `A bit flat after ${his(h)} last run. A fortnight off would do ${him(h)} good.`;
  if (h.runs === 0) { if (h.age === 2 && h.k.mat >= 1 && h.gs.mat === 'l') return `Backward. ${He(h)} will be a different horse next year, so expect little yet.`; return h.k.pw > 12 ? `Ready to run. We won't know what we have until ${he(h)} sees a racecourse.` : `Ready to run, and the work says ${he(h)} can win.`; }
  if (h.or == null) return `One more run and the handicapper gives ${him(h)} a mark.`;
  const d = T.estAb(h) - h.or; if (d >= 5) return `I think ${he(h)} is ahead of ${his(h)} mark. Strike while we can.`;
  if (d <= -5) return `The handicapper has ${him(h)} in his grip. Easier races, or wait for ${his(h)} ground.`;
  if (h.form[h.form.length - 1] === 1) return `In great heart since winning.`;
  if (h.age <= 3 && h.mat !== 'e') return `Still growing up. ${He(h)} improves with every week.`;
  return ['Working well and ready to go.', 'Eating up and bouncing.', 'Same as ever. Honest as the day.'][h.id % 3];
}

// ---------------------------------------------------------------- frame
function bar() { const t = T.T(); let cash = S.cash;
  if (S.phase === 'raceday' && S.rd) { const rd = S.rd; cash = rd.cash0; rd.res.forEach((R, i) => { if (i < rd.i || (i === rd.i && UI.rd && UI.rd.stage === 'result')) cash += R.mine.reduce((a, m) => a + m.prize, 0); }); }   // don't give the result away
  return `<header class="bar"><div class="brand">${silk(S.silk, 32)}<div style="min-width:0"><b>${esc(S.stable)}</b><i>Season ${S.season} · ${t.n}</i></div></div><div class="cash${cash < 0 ? ' neg' : ''}">${money(cash)}</div></header>`; }
const nav = () => `<nav class="nav">${[['yard', 'Yard'], ['card', 'Racecard'], ['season', 'Season'], ['stud', 'Stud']].map(([k, l]) => `<button data-a="tab" data-t="${k}" class="${UI.tab === k ? 'on' : ''}">${l}</button>`).join('')}</nav>`;
function render(keep) {
  S = T.S; const m = app.querySelector('main'), sb = app.querySelector('.sh-b'), st = keep && m ? m.scrollTop : 0, st2 = keep && sb ? sb.scrollTop : 0;
  let h;
  if (!S) h = vSetup();
  else if (S.phase === 'raceday') h = vRaceday();
  else if (S.phase === 'summary') h = vSummary();
  else if (S.phase === 'winter') h = vWinter();
  else h = bar() + `<main>${UI.tab === 'card' ? vCard() : UI.tab === 'season' ? vSeasonTab() : UI.tab === 'stud' ? vStud() : vYard()}</main>` + (UI.tab === 'yard' ? yardCta() : '') + nav();
  app.innerHTML = h + (UI.sheet ? vSheet() : '') + (UI.toast ? `<div class="toast" role="status">${esc(UI.toast)}</div>` : '');
  const m2 = app.querySelector('main'), sb2 = app.querySelector('.sh-b'); if (m2) m2.scrollTop = st; if (sb2) sb2.scrollTop = st2;
  if (UI.after) { const f = UI.after; UI.after = null; f(); }
}
let toastT = 0; function toast(t) { UI.toast = t; clearTimeout(toastT); toastT = setTimeout(() => { UI.toast = null; if (!(UI.rd && UI.rd.stage === 'run')) render(true); }, 2400); }

// ---------------------------------------------------------------- setup
function vSetup() {
  const u = UI.setup = UI.setup || { name: '', silk: { b: PAL[10], b2: PAL[9], p: 'chevron', s: PAL[10], c: PAL[9] } }, sp = u.silk;
  const sw = (key) => `<div class="sw">${PAL.map(c => `<button data-a="col" data-k="${key}" data-c="${c}" class="${sp[key] === c ? 'on' : ''}" style="background:${c}" aria-label="colour"></button>`).join('')}</div>`;
  return `<main>
    <div class="hero"><span class="kick">Thoroughbred</span><h1>Your racing career</h1><p class="sm">Start with three horses and £60,000. Find out what they are, place them to win, and build the yard that breeds a champion.</p></div>
    <div class="card" style="display:flex;flex-direction:column;gap:14px">
      <div class="field"><label for="sname">Your stable's name</label><input type="text" id="sname" maxlength="22" autocomplete="off" placeholder="e.g. Warren Hill Stud" value="${esc(u.name)}"></div>
      <div class="row" style="gap:14px"><div>${silk(sp, 76)}</div><div class="grow sm mut">Your colours. Your jockeys wear them in every race.</div></div>
      <div class="field"><label>Jacket</label>${sw('b')}</div>
      <div class="field"><label>Pattern</label><div class="pats">${PATS.map(p => `<button data-a="pat" data-p="${p}" class="${sp.p === p ? 'on' : ''}" aria-label="${p}">${silk(Object.assign({}, sp, { p }), 36)}</button>`).join('')}</div></div>
      <div class="field"><label>Second colour and cap</label>${sw('b2')}</div>
      <div class="field"><label>Sleeves</label>${sw('s')}</div>
    </div>
    <div class="card sm"><b>How a season goes</b><ul class="plain" style="margin-top:6px"><li>16 fortnights of racing, from the Lincoln to the November Handicap.</li><li>Each fortnight: pick a race for each horse, use your gallops, go racing.</li><li>In winter: sell, breed and buy for next year.</li></ul></div>
  </main><div class="cta"><button class="btn gold" data-a="start">Open the yard ▸</button></div>`;
}

// ---------------------------------------------------------------- the yard: every decision of the fortnight on one screen
function vYard() {
  const f = S.f, fn = S.fn, big = fn.races.filter(r => r.big).sort((a, b) => b.p - a.p), g1 = big.filter(r => r.cls === 'G1');
  const feat = (g1.length ? g1 : big).slice(0, 4).map(r => r.n).join(', ');
  let h = `<div class="hero"><span class="kick">Fortnight ${f + 1} of ${T.NF} · ${T.FN[f][1]}</span><h1>${T.FN[f][0]}</h1><p class="sm">${g1.length ? 'Group 1s: ' : 'Big races: '}${esc(feat)}.</p><p class="sm">Going is mostly ${GO[fn.base]}. Everyday racing at ${fn.ev.join(', ')}.</p><button class="link" data-a="tab" data-t="card">See every race ▸</button></div>`;
  if (!S.tips.intro) h += `<div class="card"><span class="kick">From your trainer</span><p class="note" style="margin:4px 0 8px">Morning, guv'nor. Three jobs each fortnight.</p><ul class="plain sm"><li><b>Pick a race</b> for each horse, or rest it. The chip shows my view of its chance.</li><li><b>Use your gallops</b> to learn about the young ones. Racing teaches us most.</li><li><b>Go racing.</b> Tap a horse's name to see everything we know about it.</li></ul><button class="btn sm ghost" style="margin-top:10px" data-a="tipOk">Got it</button></div>`;
  if (S.cash < 0) h += `<div class="card" style="border-color:var(--bad)"><b style="color:var(--bad)">You're overdrawn.</b> <span class="sm">Win some prize money or sell a horse. Below −£25,000 the bank stops you entering races.</span></div>`;
  const tg = T.T().gal;
  h += `<div class="gal"><span class="pips">${Array.from({ length: tg }, (_, i) => `<i class="${i < S.gal ? '' : 'off'}"></i>`).join('')}</span><span class="grow"><b>${S.gal} gallop${S.gal === 1 ? '' : 's'} left.</b> Work a horse to learn more, school it, or give it an easy week.</span></div>`;
  if (!S.horses.length) h += `<div class="card"><b>You have no horses in training.</b><p class="sm mut" style="margin:4px 0 10px">The next chance to buy is the winter sales.</p><button class="btn sm" data-a="toWinter">Go straight to the winter sales ▸</button></div>`;
  for (const x of S.horses) h += hcard(x);
  return h;
}
function hcard(h) {
  const e = h.entry != null ? T.race(h.entry) : null, p = h.inj > 0 ? {} : T.picks(h); let pb;
  if (h.inj > 0) pb = `<button class="pickb" disabled><span class="t"><b>Injured</b><span>Back in ${h.inj} fortnight${h.inj > 1 ? 's' : ''}</span></span></button>`;
  else if (e) { const v = T.view(h, e); pb = `<button class="pickb set" data-a="openEntry" data-h="${h.id}"><span class="t"><b>${chip(e.cls)} ${esc(rtitle(e))}</b><span>${e.co} · ${goingTxt(e.co)} · ${T.TYPE[T.ctype(e.co)]}</span></span>${chance(v)}</button>`; }
  else if (!p.best) pb = `<button class="pickb" disabled><span class="t"><b>No race open</b><span>Nothing ${he(h)} qualifies for this fortnight</span></span></button>`;
  else { const keen = h.fresh >= 72 && (p.best.v.lv >= 2 || h.or == null); pb = `<button class="pickb${keen ? ' need' : ''}" data-a="openEntry" data-h="${h.id}"><span class="t"><b>${keen ? 'Choose a race' : 'Resting'}</b><span>${p.n} open to ${him(h)} · best: ${p.best.v.label.toLowerCase()}</span></span><span class="go">▸</span></button>`; }
  return `<div class="card hc"><button class="top" data-a="openHorse" data-h="${h.id}"><span class="age${h.sex === 'f' ? ' f' : ''}"><span>${h.age}<small>YO</small></span></span><span class="grow"><span class="hn">${esc(h.n)}</span><br>${pstars(h)} <span class="sm mut">${pword(h)}</span></span><span class="or"><b>${h.or == null ? '–' : h.or}</b><i>Rating</i></span></button>
    <div class="fresh"><span>Fresh</span>${fbar(h.fresh)}<span class="form">${formTxt(h)}</span></div>
    <p class="note">“${note(h)}”</p>
    <div class="acts">${pb}<button class="galb" data-a="openGallop" data-h="${h.id}" ${S.gal <= 0 || h.inj > 0 ? 'disabled' : ''}>Gallops</button></div></div>`;
}
function yardCta() { const n = S.horses.filter(h => h.entry != null).length, blocked = S.cash < -25000 && n > 0; return `<div class="cta"><button class="btn ghost" data-a="auto">Trainer picks</button><button class="btn gold" data-a="go" ${blocked ? 'disabled' : ''}>${n ? `Go racing · ${n} runner${n > 1 ? 's' : ''} ▸` : 'Skip this fortnight ▸'}</button></div>`; }

// ---------------------------------------------------------------- sheets
const shead = (k, t, sub) => `<div class="sh-h"><div><span class="kick">${k}</span><h2>${t}</h2>${sub ? `<p class="sm mut" style="margin-top:3px">${sub}</p>` : ''}</div><button class="x" data-a="close" aria-label="Close">×</button></div>`;
function vSheet() {
  const s = UI.sheet; let h = '', full = false;
  if (s.t === 'entry') h = shEntry(T.horse(s.h));
  else if (s.t === 'gallop') h = shGallop(T.horse(s.h));
  else if (s.t === 'horse') { h = shHorse(s.lot != null ? S.w.lots[s.lot].h : (T.horse(s.h) || S.young.find(y => y.id === s.h)), s.lot != null); full = true; }
  else if (s.t === 'race') { h = shRace(T.race(s.r)); full = true; }
  else if (s.t === 'sire') { h = shSire(S.mares.find(m => m.id === s.m)); full = true; }
  else if (s.t === 'msg') h = shead(s.k, esc(s.title)) + `<div class="sh-b">${s.say ? `<p class="say">${esc(s.say)}</p>` : ''}${s.body || ''}${revs(s.rev)}<button class="btn" data-a="close">${s.ok || 'Carry on'}</button></div>`;
  else if (s.t === 'tier') { const t = T.T(), i = T.tier(), p = T.TIERS[i - 1]; h = `<div class="sh-b cele"><span class="kick">Your reputation has grown</span><h1>${t.n}</h1><p>The racing world has noticed ${esc(S.stable)}.</p><ul class="plain sm" style="text-align:left"><li>${t.boxes} boxes in the yard (was ${p.boxes})</li><li>${t.pad} broodmare paddock${t.pad > 1 ? 's' : ''} (was ${p.pad})</li>${t.gal > p.gal ? `<li>${t.gal} gallops a fortnight</li>` : ''}<li>Better lots at the sales, and stallions up to ${mk(t.fee)}</li><li>A sharper trainer's eye</li></ul><button class="btn gold" data-a="close" style="align-self:stretch">Onwards</button></div>`; }
  return `<div class="veil"><div class="sheet${full ? ' full' : ''}" role="dialog" aria-modal="true">${h}</div></div>`;
}
const revs = r => r && r.length ? `<div class="revs">${r.map((x, i) => `<span class="rev" style="animation-delay:${i * 0.15}s"><i>${x[0]}</i>${esc(x[1])}</span>`).join('')}</div>` : '';
function optRow(h, o, tags) { const r = o.r, v = o.v; return `<button class="opt${h.entry === r.id ? ' on' : ''}" data-a="pick" data-h="${h.id}" data-r="${r.id}"><span class="l1">${chip(r.cls)}<b>${esc(rtitle(r))}</b>${chance(v)}</span><span class="l2">${rsub(r)} · ${ages(r)} · ${mk(r.p * 1000)} to the winner</span><span>${tags}${fitRow(v.fit)}${v.low ? ' <span class="fit"><i class="f-n">Rated below this race</i></span>' : ''}</span></button>`; }
function shEntry(h) {
  const o = T.options(h), p = T.picks(h), all = UI.sheet.all, list = all ? o : o.slice(0, 6);
  if (p.rich && !list.some(x => x.r.id === p.rich.r.id)) list.push(p.rich);
  if (h.entry != null && !list.some(x => x.r.id === h.entry)) { const cur = o.find(x => x.r.id === h.entry); if (cur) list.unshift(cur); }
  return shead(`Fresh ${Math.round(h.fresh)} · ${h.or == null ? 'no rating yet' : 'rated ' + h.or}`, `Where does ${esc(h.n)} run?`, 'The chip is your trainer’s view of the chance, from what you know so far. A ? means untested.') +
    `<div class="sh-b"><button class="opt${h.entry == null ? ' on' : ''}" data-a="pick" data-h="${h.id}" data-r=""><span class="l1"><b>Rest this fortnight</b></span><span class="l2">Gets ${his(h)} freshness back.</span></button>
    ${list.map(x => optRow(h, x, (p.best && x.r.id === p.best.r.id ? '<span class="tag">Best chance</span>' : '') + (p.rich && x.r.id === p.rich.r.id ? '<span class="tag">Big prize</span>' : ''))).join('')}
    ${!all && o.length > list.length ? `<button class="btn ghost sm" data-a="showAll">Show all ${o.length} races</button>` : ''}</div>`;
}
function shGallop(h) {
  const k = h.k; let sch, schOk = true;
  if (h.quirk === 'slowstart' && k.quirk === 2) sch = `Stalls practice, to cure ${his(h)} slow starts.`;
  else if (h.craft < 3) sch = `Teach ${him(h)} the job. A green horse gives away lengths, and this takes some of that off.`;
  else if (Math.min(h.prof.s, h.prof.u) < 2) sch = h.prof.s <= h.prof.u ? `Practice round tight turns, so sharp tracks cost ${him(h)} less.` : `Work up and down the hill, so undulating tracks cost ${him(h)} less.`;
  else { sch = `${He(h)} knows ${his(h)} job. Nothing left to teach.`; schOk = false; }
  const o = (a, t, d, ok) => `<button class="opt" data-a="gallop" data-h="${h.id}" data-g="${a}" ${ok ? '' : 'disabled style="opacity:.45"'}><span class="l1"><b>${t}</b></span><span class="l2">${d}</span></button>`;
  return shead(`${S.gal} gallop${S.gal === 1 ? '' : 's'} left this fortnight`, `${esc(h.n)} on the gallops`) + `<div class="sh-b">
    ${o('work', 'Work', `A serious gallop. Sharpens your idea of ${his(h)} potential and usually tells you something new. Takes a little freshness.`, true)}
    ${o('school', 'School', sch, schOk)}
    ${o('easy', 'Easy week', h.fresh >= 100 ? `${He(h)} is as fresh as can be.` : `Puts 30 back on ${his(h)} freshness, on top of the usual rest.`, h.fresh < 100)}</div>`;
}
const CRAFT = ['Green', 'Learning', 'Nearly there', 'Professional'];
function tiles(h) {
  const k = h.k, g = h.gs, q = (lv, txt) => lv === 0 ? '?' : txt + (lv === 1 ? '?' : '');
  const pips = `<span class="gp">${['H', 'S', 'G', 'Qr', 'Qk'].map((l, i) => { const kn = k.gr[i], gu = k.gh ? (T.groundMod(k.gh, i) > 0 ? 2 : T.groundMod(k.gh, i) === 0 ? 1 : 0) : null; return `<u class="${kn != null ? 'g' + kn : gu != null ? 'h' + gu : ''}">${l}</u>`; }).join('')}</span>`;
  const t = [['mat', 'Maturity', q(k.mat, LAB.mat[g.mat]), k.mat], ['trip', 'Best trip', q(k.trip, T.tripLabel(g.trip)), k.trip], ['gr', 'Ground', pips, k.gsure ? 2 : k.gr.some(x => x != null) ? 1 : 1],
    ['build', 'Build', q(k.build, LAB.build[g.build]), k.build], ['style', 'Style', q(k.style, LAB.style[h.style]), k.style], ['temp', 'Temperament', q(k.temp, LAB.temp[g.temp]), k.temp],
    ['con', 'Constitution', q(k.con, LAB.con[g.con]), k.con], ['quirk', 'Quirk', k.quirk === 2 ? (h.quirk ? T.QUIRKS[h.quirk] : 'None') : '?', k.quirk === 2 ? 2 : 0], ['craft', 'Racecraft', CRAFT[Math.min(3, h.craft)], 2]];
  return `<div class="tiles">${t.map(x => `<button class="tile k${x[3]}${UI.sheet.tile === x[0] ? ' on' : ''}" data-a="tile" data-k="${x[0]}"><i>${x[1]}</i><b>${x[2]}</b></button>`).join('')}</div>`;
}
function tileInfo(h, key) {
  const k = h.k, g = h.gs, H = He(h), unk = 'Not known yet. Gallops give a first idea; racing settles it.';
  switch (key) {
    case 'mat': return k.mat ? { e: `${H} is forward. At ${his(h)} best at two and three.`, n: `A normal developer. Peaks at three and four.`, l: `${H} needs time. Best at four and five, so go gently early on.` }[g.mat] + (k.mat < 2 ? ' That is your trainer’s guess.' : '') : unk;
    case 'trip': return `${H} is ${k.trip < 2 ? 'bred for' : 'best over'} ${T.tripLabel(g.trip)}. Each step away from that costs about 5 lb.` + (k.trip < 2 ? ' A run over the trip will confirm it.' : '');
    case 'gr': return 'Heavy, Softer, Good, Quicker, Quick. Solid green means proven on it (worth 5 lb), amber means copes, red means hates it. Outlines are guesses from the pedigree. Each going must be raced on to be sure.';
    case 'build': return k.build ? { gal: `A long-striding galloper. Best on big galloping tracks. Sharp and undulating tracks cost ${him(h)} lengths until ${he(h)} learns them.`, agi: `Nimble and balanced. At ${his(h)} best on sharp and undulating tracks.`, ver: `Handles any track.` }[g.build] + (k.build < 2 ? ' That is a guess from how ' + he(h) + ' moves.' : '') : 'Not known yet. A run on a sharp or undulating track will tell you.';
    case 'style': return k.style ? { F: 'Likes to lead. Suited by a slow pace, when nobody takes ' + him(h) + ' on.', P: 'Races just behind the leaders. Rarely caught out by the pace.', M: 'Sits in midfield. Slightly suited by a strong pace.', H: 'Held up at the back. Needs a strong pace to run at.' }[h.style] : 'You will see it the first time ' + he(h) + ' runs.';
    case 'temp': return k.temp ? { calm: 'Laid-back. Runs to the same level almost every time.', even: 'Honest. Usually runs ' + his(h) + ' race.', hot: 'Highly strung. Brilliant one day, flat the next, and dislikes slow paces and big fields.' }[g.temp] + (k.temp < 2 ? ' A first impression only.' : '') : unk;
    case 'con': return k.con ? { tough: 'Tough. Can run nearly every fortnight.', sound: 'Sound. Two runs in every three fortnights suits ' + him(h) + '.', del: 'Delicate. Needs a fortnight off after every run.' }[g.con] + (k.con < 2 ? ' A first impression only.' : '') : unk;
    case 'quirk': return k.quirk === 2 ? T.QDESC[h.quirk || 'none'] : 'Quirks only show on the racecourse. Some horses have none.';
    default: return ['Green. First time out a horse gives away about 6 lb through inexperience.', 'Learning. Still gives away a few pounds.', 'Nearly there.', 'A professional. Nothing lost to inexperience.'][Math.min(3, h.craft)] + ' Every run teaches. Schooling helps too.';
  }
}
function shHorse(h, lot) {
  const mine = !!T.horse(h.id), young = !mine && !lot, v = mine ? T.valueOf(h) : 0;
  let b = `<div class="big3"><div><b>${h.or == null ? '–' : h.or}</b><i>Rating</i></div><div><b>${h.runs}·${h.wins}·${h.pl}</b><i>Runs·wins·places</i></div><div><b>${mk(h.earn)}</b><i>Prize money</i></div></div>
    <div class="card"><span class="kick">Potential</span><div class="row sp" style="margin-top:2px">${pstars(h, true)}<b>${pword(h)}</b></div><p class="sm mut" style="margin-top:4px">Your trainer's estimate. The pale stars are what ${he(h)} might be. Gallops and runs sharpen it.</p></div>
    ${tiles(h)}<p class="explain">${tileInfo(h, UI.sheet.tile || 'trip')}</p>`;
  if (mine) b += `<div class="fresh"><span>Freshness</span>${fbar(h.fresh)}<b class="num">${Math.round(h.fresh)}</b></div>`;
  if (h.big.length) b += `<div class="card sm"><span class="kick">Big wins</span><p>${h.big.map(esc).join(', ')}</p></div>`;
  if (h.hist.length) b += `<div class="sec">Races</div><div class="card"><div class="list">${h.hist.slice(-8).reverse().map(x => `<div class="li"><span class="pos p${x.pos}" style="width:34px;height:34px;font-size:15px">${ord(x.pos)}</span><span class="t"><b>${chip(x.cls)} ${esc(x.n)}</b><span>${x.co} · ${T.fLabel(x.d)} · ${x.g == null ? 'AW' : GO[x.g]} · of ${x.of}${x.pos === 1 ? ' · won by ' + mtxt(x.btn) : ' · beaten ' + mtxt(x.btn)}</span></span><b class="num sm">${x.pr ? mk(x.pr) : ''}</b></div>`).join('')}</div></div>`;
  if (mine) b += `<div class="sec">Name</div><div class="row"><input type="text" id="rename" maxlength="20" value="${esc(h.n)}"><button class="btn sm" data-a="rename" data-h="${h.id}">Save</button></div>
    ${S.phase === 'yard' ? `<button class="btn ${UI.sheet.sell ? 'bad' : 'ghost'}" style="flex:none" data-a="sell" data-h="${h.id}">${UI.sheet.sell ? `Yes, sell ${esc(h.n)} for ${money(v)}` : `Sell for ${money(v)}`}</button>` : ''}`;
  return shead(`${h.age < 2 ? (h.age === 1 ? 'Yearling' : 'Youngster') : h.age + 'yo'} ${h.age < 2 ? (h.sex === 'f' ? 'filly' : 'colt') : sexWord(h)}${h.bred ? ' · homebred' : ''}`, esc(h.n), `By ${esc(h.sire)} (${starTxt(h.ss)}) out of ${esc(h.dam)} (${starTxt(h.ds)})`) + `<div class="sh-b">${b}</div>`;
}
function whyNot(h, r) { if (h.inj > 0) return 'injured'; if (h.age < r.a[0]) return 'too young'; if (h.age > r.a[1]) return 'too old'; if (r.sx === 'F' && h.sex !== 'f') return 'fillies only'; if (r.sx === 'C' && h.sex !== 'c') return 'colts only'; if ((r.cls === 'M' || r.cls === 'MA') && h.wins) return 'has already won'; if (r.cls === 'MA') return 'cost too much for an auction race'; if (r.cls === 'N') return 'too many wins'; if (r.cap != null) return h.or == null ? 'no rating yet' : 'rated above ' + r.cap; return ''; }
function shRace(r) {
  const el = S.horses.filter(h => T.eligible(h, r)), hc = r.cap != null, fld = r.field.slice().sort((a, b) => (b.ab - (hc ? b.or : 0)) - (a.ab - (hc ? a.or : 0)) + ((hash(a.n) % 7) - (hash(b.n) % 7)) * 0.9);
  let b = `<div class="sec">Your horses</div><div class="card"><div class="list">${S.horses.length ? S.horses.map(h => { const ok = el.includes(h), v = ok ? T.view(h, r) : null; return `<div class="li"><span class="t"><b>${esc(h.n)}</b><span>${ok ? fitRow(v.fit) : 'Can’t run: ' + whyNot(h, r)}</span></span>${ok ? chance(v) + `<button class="btn sm ${h.entry === r.id ? '' : 'ghost'}" data-a="pick" data-h="${h.id}" data-r="${h.entry === r.id ? '' : r.id}" data-stay="1">${h.entry === r.id ? 'Entered ✓' : 'Enter'}</button>` : ''}</div>`; }).join('') : '<p class="sm mut">No horses in training.</p>'}</div></div>
    <div class="sec">The opposition <span>${r.field.length} runners</span></div><div class="card"><div class="list">${fld.map(x => `<div class="li">${silk(D.silks[x.s], 28)}<span class="t"><b>${esc(x.n)}${x.star ? ' <span class="tag" style="margin-left:4px">Star</span>' : ''}</b><span>${x.fm ? 'Form ' + x.fm.split('').join('-') : 'Unraced'} · ${LAB.style[x.st]}</span></span>${hc ? `<span class="or"><b style="font-size:16px">${x.or}</b><i>Rating</i></span>` : ''}</div>`).join('')}</div></div>`;
  return shead(`${CLS[r.cls].l}${r.cap != null ? ' · rated ' + T.floorOf(r) + ' to ' + r.cap : ''}`, esc(rtitle(r)), `${rsub(r)} · ${ages(r)} · ${mk(r.p * 1000)} to the winner`) + `<div class="sh-b">${b}</div>`;
}

// ---------------------------------------------------------------- racecard tab
function vCard() {
  const fn = S.fn, by = {}; for (const r of fn.races) (by[r.co] = by[r.co] || []).push(r);
  const w = co => by[co].reduce((a, r) => a + (r.big ? r.p : 0), 0) + (co === fn.main ? 1e6 : 0), cos = Object.keys(by).sort((a, b) => w(b) - w(a));
  let h = `<div class="hero"><span class="kick">Fortnight ${S.f + 1} · ${T.FN[S.f][1]}</span><h2>Every race this fortnight</h2><p class="sm">Tap a race to see the field and enter a horse.</p></div>`;
  for (const co of cos) { const rs = by[co].slice().sort((a, b) => b.p - a.p);
    h += `<div class="sec">${co} <span>${T.TYPE[T.ctype(co)]} · ${goingTxt(co)}</span></div><div class="card"><div class="list">${rs.map(r => { const mine = S.horses.filter(x => x.entry === r.id); return `<button class="li" data-a="race" data-r="${r.id}">${chip(r.cls)}<span class="t"><b>${esc(rtitle(r))}</b><span>${T.fLabel(r.f)} · ${ages(r)} · ${mk(r.p * 1000)}</span></span>${mine.length ? silk(S.silk, 26) : '<span class="mut">▸</span>'}</button>`; }).join('')}</div></div>`; }
  return h;
}
// ---------------------------------------------------------------- season tab
function ladder() { const i = T.tier(), t = T.TIERS[i], nx = T.TIERS[i + 1], pc = nx ? Math.min(100, 100 * (S.rep - t.rep) / (nx.rep - t.rep)) : 100;
  return `<div class="card"><span class="kick">Reputation</span><div class="row sp"><h2>${t.n}</h2><b class="num">${S.rep}${nx ? ' / ' + nx.rep : ''}</b></div><div class="prog" style="margin:8px 0 6px"><b style="width:${pc}%"></b></div><p class="sm mut">${nx ? `Next: <b>${nx.n}</b>. ${nx.boxes} boxes, ${nx.pad} paddocks, better sales and stallions.` : 'The top of the tree. Now breed a champion.'} Wins earn reputation, and bigger races earn more.</p></div>`; }
const goalsCard = () => `<div class="card"><span class="kick">This season's goals</span>${S.goals.map(g => { const d = T.goalDone(g), cur = S.ss[g.k]; return `<div class="goal"><span class="tick${d ? ' y' : ''}">${d ? '✓' : ''}</span><span class="grow"><b>${g.t}</b><br><span class="sm mut">${g.k === 'prize' ? mk(cur) + ' so far · ' : g.k === 'wins' ? cur + ' so far · ' : ''}reward ${mk(g.cash)} and ${g.rep} reputation</span></span></div>`; }).join('')}</div>`;
function vSeasonTab() {
  const ss = S.ss, allBig = [].concat(...D.big), g1s = [...new Set(allBig.filter(r => r.g === 'G1').map(r => r.n))], hh = [...new Set(allBig.filter(r => r.g === 'HH').map(r => r.n))], won = n => S.troph[n];
  let h = ladder() + goalsCard() + `<div class="big3"><div><b>${ss.runs}</b><i>Runs</i></div><div><b>${ss.wins}</b><i>Wins</i></div><div><b>${mk(ss.prize)}</b><i>Prize money</i></div></div>`;
  h += `<div class="sec">The season</div><div class="card cal">${T.FN.map((x, i) => { const g = D.big[i].filter(r => r.g === 'G1').map(r => r.n); return `<div class="li ${i < S.f ? 'past' : i === S.f ? 'now' : ''}"><span class="pos" style="width:30px;height:30px;font-size:14px">${i + 1}</span><span class="t"><b>${x[0]}</b><span>${x[1]}${g.length ? ' · ' + g.slice(0, 3).join(', ') + (g.length > 3 ? ' +' + (g.length - 3) : '') : ''}</span></span></div>`; }).join('')}</div>`;
  h += `<div class="sec">Trophy cabinet <span>${g1s.filter(won).length} of ${g1s.length} Group 1s</span></div><div class="card"><div class="cups">${g1s.map(n => `<span class="cup${won(n) ? ' won' : ''}">${esc(n)}${won(n) && won(n).length > 1 ? ' ×' + won(n).length : ''}</span>`).join('')}</div></div>`;
  h += `<div class="sec">Heritage handicaps <span>${hh.filter(won).length} of ${hh.length}</span></div><div class="card"><div class="cups">${hh.map(n => `<span class="cup${won(n) ? ' won' : ''}">${esc(n)}</span>`).join('')}</div></div>`;
  if (S.top) h += `<div class="card"><span class="kick">Best horse you've trained</span><div class="row sp"><h3>${esc(S.top.n)}</h3><b>Rated ${S.top.or}</b></div><p class="sm mut">Frankel was 140. Keep going.</p></div>`;
  if (S.hof.length) h += `<div class="sec">Hall of fame</div><div class="card"><div class="list">${S.hof.slice().sort((a, b) => b.peak - a.peak).slice(0, 12).map(x => `<div class="li"><span class="t"><b>${esc(x.n)}</b><span>${x.wins} wins from ${x.runs} · ${mk(x.earn)} · ${x.how}${x.big.length ? ' · ' + x.big.slice(0, 3).map(esc).join(', ') : ''}</span></span><b>${x.peak || '–'}</b></div>`).join('')}</div></div>`;
  h += `<div class="sec">How it works</div><div class="card sm"><ul class="plain"><li><b>Rating.</b> The handicapper's number for what a horse has shown on the track. It comes after two runs or a win, and moves after every run.</li><li><b>Handicaps.</b> Every horse carries weight to match its rating, so a horse that is better than its rating has the edge. Young, improving horses often are.</li><li><b>Maidens</b> are for horses yet to win. <b>Listed and Group races</b> are level weights: the best horse usually wins.</li><li><b>Potential stars.</b> Gold is what your trainer is sure of. Pale gold is what the horse might be.</li><li><b>Freshness.</b> Racing takes it, rest restores it. Below the green zone a horse runs flat, and in the red it can get hurt.</li><li><b>Trip, ground and track.</b> The wrong one costs lengths. You find out by trying.</li></ul></div>`;
  h += `<button class="btn ${UI.reset ? 'bad' : 'ghost'}" style="flex:none;margin-top:8px" data-a="reset">${UI.reset ? 'Yes, wipe this career and start again' : 'Start a new career'}</button>`;
  return h;
}
// ---------------------------------------------------------------- stud tab
const mareLine = m => `${starTxt(m.stars)} · ${T.tripLabel(m.opt)} · ${T.groundLabel(m.gr)}`;
function vStud() {
  const t = T.T(); let h = `<div class="hero"><span class="kick">The stud</span><h2>Breed your own</h2><p class="sm">Mares are covered in winter. The foal grows up here for a season, then comes into training as a two-year-old. The best mares breed the best foals.</p></div>`;
  h += `<div class="sec">Broodmares <span>${S.mares.length} of ${t.pad} paddocks</span></div><div class="card">${S.mares.length ? `<div class="list">${S.mares.map(m => `<div class="li"><span class="t"><b>${esc(m.n)}</b><span>${mareLine(m)}${m.peakOR ? ' · raced to ' + m.peakOR : ''}</span></span><span class="sm mut">${m.age}yo</span></div>`).join('')}</div>` : `<p class="sm mut">No mares yet. Retire a filly to stud in the winter, or buy a mare at the winter sale.</p>`}</div>`;
  h += `<div class="sec">Youngsters <span>${S.young.length}</span></div><div class="card">${S.young.length ? `<div class="list">${S.young.map(y => `<button class="li" data-a="openHorse" data-h="${y.id}"><span class="t"><b>${esc(y.n)}</b><span>${y.sex === 'f' ? 'Filly' : 'Colt'} by ${esc(y.sire)} out of ${esc(y.dam)}</span><span>${S.f >= 6 ? ['Small and backward so far.', 'Plain, but a good mover.', 'Athletic. The stud groom likes this one.', 'The best-looking youngster on the farm.'][y.looks] : 'Too early to say much.'} ${y.due === S.season + 1 ? 'Into training next season.' : 'Into training in two seasons.'}</span></span><span class="mut">▸</span></button>`).join('')}</div>` : `<p class="sm mut">Nothing on the ground. Send a mare to a stallion this winter.</p>`}</div>`;
  const st = S.studs.filter(s => s.until >= S.season);
  if (st.length) h += `<div class="sec">Your stallions</div><div class="card"><div class="list">${st.map(s => `<div class="li"><span class="t"><b>${esc(s.n)}</b><span>${starTxt(s.stars)} · ${T.tripLabel(s.opt)} · free to your mares until season ${s.until}</span></span></div>`).join('')}</div></div>`;
  return h;
}

// ---------------------------------------------------------------- race day
function vRaceday() {
  const rd = S.rd, R = rd.res[rd.i], u = UI.rd = UI.rd || { stage: 'card' }, n = rd.res.length, mineIds = R.mine.map(m => m.hid);
  const head = `<div class="hero"><span class="kick">Race ${rd.i + 1} of ${n} · ${R.co} · ${CLS[R.cls].l}</span><h2>${esc(R.big ? R.n : T.fLabel(R.f) + ' ' + R.n)}</h2><p class="sm">${rsub(R)} · ${ages(R)} · ${mk(R.p * 1000)} to the winner</p></div>`;
  if (u.stage === 'card') {
    const pace = { fast: 'Plenty of front-runners, so expect a strong pace. That suits horses held up.', slow: 'No obvious leader, so expect a slow pace. That suits horses ridden near the front.', even: 'An even pace looks likely. No excuses for anyone.' }[R.pace];
    const dec = t => t === 'Evens' ? 1 : (a => a[0] / a[1])(t.split('/').map(Number)), list = R.run.slice().sort((a, b) => dec(a.od) - dec(b.od) || hash(a.n) - hash(b.n));
    return bar() + `<main>${head}<p class="explain"><b>Pace forecast.</b> ${pace}</p><div class="card"><div class="list">${list.map(x => `<div class="li${x.you ? ' me' : ''}">${silk(x.you ? S.silk : D.silks[x.s], 30)}<span class="t"><b>${esc(x.n)}${x.you ? ' <span class="tag" style="margin-left:4px">Yours</span>' : ''}</b><span>${x.fm ? 'Form ' + String(x.fm).split('').join('-') : 'Unraced'} · ${LAB.style[x.st]}${x.or != null && R.cap != null ? ' · rated ' + x.or : ''}</span></span><span class="odds ${oddsCls(x.od)}">${x.od}</span></div>`).join('')}</div></div></main>
      <div class="cta"><button class="btn ghost" data-a="rdResult">Just the result</button><button class="btn gold" data-a="rdWatch">Watch the race ▸</button></div>`;
  }
  if (u.stage === 'run') { UI.after = () => playRace(R); return bar() + `<main>${head}<div class="rv"><div class="hd"><span id="rvd">${T.fLabel(R.f)} to run</span><span>${T.isAW(R.co) ? 'All-weather' : GO[R.g]}</span></div><div class="turf go" id="turf"></div><p class="call" id="call">They're going down to the start.</p></div><p class="sm mut" style="text-align:center">A stand-in for the 3D race view.</p></main><div class="cta"><button class="btn ghost" style="flex:1" data-a="rdResult">Skip to the result</button></div>`; }
  // result
  const top = R.run.slice(0, 4), extra = R.run.filter(x => x.you && x.pos > 4), last = rd.i === n - 1;
  let b = `<div class="card"><span class="kick">Result</span><div class="list">${top.concat(extra).map(x => `<div class="li${x.you ? ' me' : ''}"><span class="pos p${x.pos}" style="width:32px;height:32px;font-size:14px">${ord(x.pos)}</span>${silk(x.you ? S.silk : D.silks[x.s], 26)}<span class="t"><b>${esc(x.n)}</b><span>${x.pos === 1 ? 'Winner' : mtxt(x.btn) + ' behind'} · ${x.od}</span></span></div>`).join('')}</div></div>`;
  for (const m of R.mine) { const h = T.horse(m.hid) || { n: R.run.find(x => x.hid === m.hid).n };
    b += `<div class="res1${m.won ? ' win' : ''}"><span class="pos p${m.pos}">${ord(m.pos)}</span><span class="grow"><b style="font-size:17px">${esc(h.n)}${m.won ? ' wins!' : ''}</b><br><span class="sm">${m.prize ? money(m.prize) + ' prize money' : 'No prize money'}${m.rep ? ' · +' + m.rep + ' reputation' : ''}</span></span>${m.orNew != null ? `<span class="or"><b>${m.orNew}</b><i>${m.orOld == null ? 'First rating' : m.orNew > m.orOld ? 'Up ' + (m.orNew - m.orOld) : m.orNew < m.orOld ? 'Down ' + (m.orOld - m.orNew) : 'Rating'}</i></span>` : ''}</div>
      <p class="say">“${esc(m.say)}”</p>${m.rev.length ? `<div><span class="kick">What you learned</span><div style="margin-top:5px">${revs(m.rev)}</div></div>` : ''}`; }
  return bar() + `<main>${head}${b}</main><div class="cta">${last ? '' : `<button class="btn ghost" data-a="rdAll">Skip the rest</button>`}<button class="btn gold" data-a="rdNext">${last ? 'The fortnight in full ▸' : 'Next race ▸'}</button></div>`;
}
function playRace(R) {
  const turf = document.getElementById('turf'), call = document.getElementById('call'), dist = document.getElementById('rvd'); if (!turf) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) { UI.rd.stage = 'result'; render(); return; }
  const run = R.run, n = run.length, lh = n <= 10 ? 26 : n <= 14 ? 22 : 19, W = turf.clientWidth, order = run.map((x, i) => i).sort((a, b) => hash(run[a].n) % 997 - hash(run[b].n) % 997);
  let rs = hash(R.n) + R.rid; const rr = () => { rs = (rs * 1664525 + 1013904223) | 0; return (rs >>> 0) / 4294967296; };
  const E = { F: [0, 1.2], P: [1.6, 3.2], M: [3.6, 5.6], H: [6, 8.5] }, d = run.map(x => ({ e: E[x.st][0] + rr() * (E[x.st][1] - E[x.st][0]), g: Math.min(x.btn, 15), a: { F: 0.40, P: 0.45, M: 0.52, H: 0.6 }[x.st] + rr() * 0.07, w: rr() * 6.28 }));
  const gap = (i, t) => { const q = d[i]; let s = (t - q.a) / (1 - q.a); s = s < 0 ? 0 : s > 1 ? 1 : s * s * (3 - 2 * s); return q.e * (1 - s) + q.g * s + 0.3 * Math.sin(q.w + t * 10) * (1 - t); };
  const gaps = t => { const g = run.map((x, i) => gap(i, t)), mn = Math.min(...g); return g.map(x => x - mn); };
  turf.style.height = n * lh + 6 + 'px';
  turf.innerHTML = order.map((ri, li) => `<div class="lane${run[ri].you ? ' me' : ''}" style="height:${lh}px"><div class="runner" data-i="${ri}">${run[ri].you ? `<span class="nm">${esc(run[ri].n)}</span>` : ''}${silk(run[ri].you ? S.silk : D.silks[run[ri].s], lh - 3)}</div></div>`).join('') + '<div class="post" id="post" style="left:0"></div>';
  const els = [...turf.querySelectorAll('.runner')], post = document.getElementById('post'), X0 = W * 0.72, ppl = (X0 - 24) / 13, DUR = 9000 + (R.f > 10 ? 2000 : 0) + (R.f > 14 ? 1500 : 0);
  const me = run.findIndex(x => x.you), nameAt = (t, k) => { const g = gaps(t); return run.map((x, i) => [g[i], x]).sort((a, b) => a[0] - b[0])[k][1].n; }, rankAt = t => { const g = gaps(t); return g.filter(x => x < g[me]).length + 1; };
  const where = t => { const r = rankAt(t); return r === 1 ? 'leads' : r <= Math.max(2, n * 0.3) ? 'is up with the pace' : r <= n * 0.65 ? 'sits in midfield' : 'is held up at the back'; };
  const mn = run[me].n, r85 = rankAt(0.86), fin = run[me].pos;
  const calls = [[0.02, `They're off in the ${R.big ? R.n : T.fLabel(R.f) + ' ' + R.n.toLowerCase()}!`], [0.2, `${nameAt(0.2, 0)} leads from ${nameAt(0.2, 1)}. ${mn} ${where(0.2)}.`], [0.5, `Halfway. ${nameAt(0.5, 0)} still in front. ${mn} ${where(0.5)}.`],
    [0.74, rankAt(0.74) > rankAt(0.5) + 1 ? `${mn} is coming under pressure.` : rankAt(0.74) < rankAt(0.5) ? `${mn} is making ground!` : `They're racing now. ${mn} ${where(0.74)}.`],
    [0.88, fin === 1 ? (r85 === 1 ? `${mn} has gone for home!` : `Here comes ${mn}! Flying down the outside!`) : fin <= 3 ? `${mn} is right there with every chance!` : `${nameAt(0.88, 0)} and ${nameAt(0.88, 1)} have it between them.`],
    [1, fin === 1 ? `${mn} wins${run[1] && run[1].btn > 2.5 ? ' easily' : run[1] && run[1].btn < 0.4 ? ' in a photo' : ''}!` : `${run[0].n} wins. ${mn} is ${ord(fin)}.`]];
  let ci = 0, t0 = 0, token = UI.rd.token = Math.random();
  function frame(now) {
    if (!UI.rd || UI.rd.token !== token || UI.rd.stage !== 'run' || !document.body.contains(turf)) return;
    if (!t0) t0 = now; const t = (now - t0) / DUR, tt = Math.min(1, t), g = gaps(tt), over = t > 1 ? (t - 1) * DUR / 1000 * 150 : 0;
    for (const el of els) { const i = +el.dataset.i; el.style.transform = `translateX(${Math.max(-30, X0 - g[i] * ppl + over - (lh - 3))}px)`; }
    post.style.transform = `translateX(${X0 + (1 - tt) * W * 2.4}px)`;
    while (ci < calls.length && tt >= calls[ci][0]) { call.textContent = calls[ci][1]; ci++; }
    dist.textContent = tt >= 1 ? 'Finish' : T.fLabel(Math.max(0.5, Math.round(R.f * (1 - tt) * 2) / 2)) + ' to run';
    if (t >= 1) turf.classList.remove('go');
    if (t < 1.22) requestAnimationFrame(frame); else setTimeout(() => { if (UI.rd && UI.rd.token === token && UI.rd.stage === 'run') { UI.rd.stage = 'result'; render(); } }, 500);
  }
  requestAnimationFrame(frame);
}
// ---------------------------------------------------------------- the fortnight in full
function vSummary() {
  const rd = S.rd || { res: [] }, mine = [].concat(...rd.res.map(R => R.mine.map(m => ({ R, m })))), wins = mine.filter(x => x.m.won).length, prize = mine.reduce((a, x) => a + x.m.prize, 0), rep = mine.reduce((a, x) => a + x.m.rep, 0), fees = T.fortnightFees(), last = S.f === T.NF - 1;
  let h = `<div class="hero"><span class="kick">Fortnight ${S.f + 1} of ${T.NF} · ${T.FN[S.f][0]}</span><h1>${!mine.length ? 'A quiet fortnight' : wins ? (wins === 1 ? 'A winner!' : wins + ' winners!') : mine.some(x => x.m.pos <= 3) ? 'In the frame' : 'No luck this time'}</h1><p class="sm">${mine.length ? `${mine.length} runner${mine.length > 1 ? 's' : ''}, ${money(prize)} in prize money.` : 'The horses stayed at home and freshened up.'}</p></div>`;
  if (mine.length) h += `<div class="card"><div class="list">${mine.map(({ R, m }) => { const hh = T.horse(m.hid); return `<div class="li"><span class="pos p${m.pos}" style="width:36px;height:36px;font-size:15px">${ord(m.pos)}</span><span class="t"><b>${esc(hh ? hh.n : '')}</b><span>${chip(R.cls)} ${esc(R.big ? R.n : T.fLabel(R.f) + ' ' + R.n)} · ${R.co}</span></span><b class="num sm">${m.prize ? mk(m.prize) : ''}</b></div>`; }).join('')}</div></div>`;
  h += `<div class="card sm"><div class="row sp"><span>Prize money</span><b class="num">${money(prize)}</b></div><div class="row sp"><span>Training fees (${S.horses.length} horse${S.horses.length === 1 ? '' : 's'}${S.mares.length ? ', ' + S.mares.length + ' mare' + (S.mares.length > 1 ? 's' : '') : ''})</span><b class="num">${money(-fees)}</b></div><div class="row sp" style="border-top:1px solid var(--line);margin-top:6px;padding-top:6px"><b>The fortnight</b><b class="num" style="color:${prize - fees >= 0 ? 'var(--good)' : 'var(--bad)'}">${prize - fees >= 0 ? '+' : ''}${money(prize - fees)}</b></div></div>`;
  h += ladder() + goalsCard();
  return bar() + `<main>${h}</main><div class="cta"><button class="btn gold" data-a="next">${last ? 'End of the season ▸' : 'On to ' + T.FN[S.f + 1][0] + ' ▸'}</button></div>`;
}

// ---------------------------------------------------------------- winter
function vWinter() {
  const w = S.w, steps = `<div class="steps">${[0, 1, 2, 3].map(i => `<i class="${i <= w.step ? 'on' : ''}"></i>`).join('')}</div>`; let h = '', cta = '';
  if (w.step === 0) { const r = w.review;
    h = `<div class="hero"><span class="kick">Season ${S.season} · the review</span><h1>${r.wins >= 8 ? 'A fine season' : r.wins >= 3 ? 'A solid season' : r.wins ? 'On the board' : 'A hard season'}</h1><p class="sm">${r.best ? `${esc(r.best.n)} was your best horse${r.best.or ? ', rated ' + r.best.or : ''}.` : ''}</p></div>
      <div class="big3"><div><b>${r.runs}</b><i>Runs</i></div><div><b>${r.wins}</b><i>Wins</i></div><div><b>${mk(r.prize)}</b><i>Prize money</i></div></div>
      <div class="card"><span class="kick">Your goals</span>${S.goals.map((g, i) => `<div class="goal"><span class="tick${r.done[i] ? ' y' : ''}">${r.done[i] ? '✓' : ''}</span><span class="grow"><b>${g.t}</b><br><span class="sm mut">${r.done[i] ? `Done: ${mk(g.cash)} and ${g.rep} reputation` : 'Missed'}</span></span></div>`).join('')}</div>
      <div class="card sm"><div class="row sp"><span>Prize money</span><b class="num">${money(r.prize)}</b></div><div class="row sp"><span>Training fees</span><b class="num">${money(-r.fees)}</b></div>${r.gcash ? `<div class="row sp"><span>Goal rewards</span><b class="num">${money(r.gcash)}</b></div>` : ''}</div>` + ladder();
    cta = `<button class="btn gold" data-a="wStep" data-s="1">Decide who stays ▸</button>`;
  } else if (w.step === 1) { const t = T.T(), arr = T.arriving(), keep = S.horses.filter(x => w.plan[x.id] === 'keep').length + arr.filter(y => w.yplan[y.id] === 'keep').length, over = keep > t.boxes;
    h = `<div class="hero"><span class="kick">Winter · step 1 of 3</span><h2>Who stays in training?</h2><p class="sm">Horses turn a year older on 1 January. Sell the ones that have had their day, and retire the best to stud.</p></div>
      <div class="gal" style="${over ? 'background:#f0d9d5' : ''}"><span class="grow"><b>${keep} of ${t.boxes} boxes filled for next season.</b> ${over ? 'Too many. Sell or retire ' + (keep - t.boxes) + '.' : 'Leave room if you want to buy at the sales.'}</span></div>`;
    for (const x of S.horses) { const p = w.plan[x.id], cs = T.canStud(x), old = x.age >= 7, nextAb = x.age >= (x.mat === 'e' ? 4 : x.mat === 'n' ? 5 : 6);
      const adv = old ? `${He(x)} is ${x.age} and has earned ${his(x)} retirement.` : x.age === 2 ? (x.k.mat >= 1 && x.gs.mat !== 'e' ? `Only two. ${He(x)} should be better next year.` : `Forward for ${his(x)} age. Don't expect a big jump.`) : nextAb ? `Past ${his(x)} peak now. ${He(x)} won't get better.` : x.age === 3 && x.mat !== 'e' ? `Should still improve at four.` : `About as good as ${he(x)} will be.`;
      h += `<div class="card hc"><button class="top" data-a="openHorse" data-h="${x.id}"><span class="age${x.sex === 'f' ? ' f' : ''}"><span>${x.age}<small>YO</small></span></span><span class="grow"><span class="hn">${esc(x.n)}</span><br><span class="sm mut">${x.sr} runs, ${x.hist.filter(q => q.s === S.season && q.pos === 1).length} wins this season · ${mk(x.earn)} career</span></span><span class="or"><b>${x.or == null ? '–' : x.or}</b><i>Rating</i></span></button><p class="note">“${adv}”</p>
        <div class="seg">${old ? '' : `<button data-a="plan" data-h="${x.id}" data-p="keep" class="${p === 'keep' ? 'on' : ''}">Keep</button>`}<button data-a="plan" data-h="${x.id}" data-p="sell" class="sell ${p === 'sell' ? 'on' : ''}">Sell ${mk(T.valueOf(x))}</button>${cs ? `<button data-a="plan" data-h="${x.id}" data-p="stud" class="stud ${p === 'stud' ? 'on' : ''}">${x.sex === 'f' ? 'To stud' : 'Stallion +' + mk(T.studFee(x))}</button>` : ''}</div></div>`; }
    if (arr.length) { h += `<div class="sec">Coming into training <span>your homebreds</span></div>`; for (const y of arr) h += `<div class="card hc"><button class="top" data-a="openHorse" data-h="${y.id}"><span class="age${y.sex === 'f' ? ' f' : ''}"><span>2<small>YO</small></span></span><span class="grow"><span class="hn">${esc(y.n)}</span><br><span class="sm mut">By ${esc(y.sire)} out of ${esc(y.dam)}</span></span></button><div class="seg"><button data-a="yplan" data-h="${y.id}" data-p="keep" class="${w.yplan[y.id] === 'keep' ? 'on' : ''}">Into training</button><button data-a="yplan" data-h="${y.id}" data-p="sell" class="sell ${w.yplan[y.id] === 'sell' ? 'on' : ''}">Sell ${mk(T.yearlingValue(y))}</button></div></div>`; }
    const studF = S.horses.filter(x => w.plan[x.id] === 'stud' && x.sex === 'f').length, padOver = S.mares.length + studF > t.pad;
    if (padOver) h += `<div class="card" style="border-color:var(--bad)"><b style="color:var(--bad)">Not enough paddocks.</b> <span class="sm">You have room for ${t.pad - S.mares.length} more mare${t.pad - S.mares.length === 1 ? '' : 's'}.</span></div>`;
    cta = `<button class="btn ghost" data-a="wStep" data-s="0">Back</button><button class="btn gold" data-a="wStable" ${over || padOver ? 'disabled' : ''}>Confirm ▸</button>`;
  } else if (w.step === 2) { const t = T.T(), free = T.boxesFree();
    h = `<div class="hero"><span class="kick">Winter · step 2 of 3</span><h2>The sales</h2><p class="sm">Yearlings race for you next season as two-year-olds. You only know the pedigree, the look of them, and what your trainer whispers.</p></div>
      ${w.loan ? `<div class="card sm">An old friend has lent you enough to buy one cheap horse and start again.</div>` : ''}
      <div class="gal"><span class="grow"><b>${free} box${free === 1 ? '' : 'es'} free</b> · ${t.pad - S.mares.length} paddock${t.pad - S.mares.length === 1 ? '' : 's'} free · ${money(S.cash)} to spend</span></div>`;
    w.lots.forEach((l, i) => h += lotCard(l, i));
    cta = `<button class="btn gold" data-a="wSaleDone">Leave the sales ▸</button>`;
  } else {
    h = `<div class="hero"><span class="kick">Winter · step 3 of 3</span><h2>The covering season</h2><p class="sm">Choose a stallion for each mare. The foal takes after both parents in class, trip, ground and build. It comes into training the season after next.</p></div>`;
    if (!S.mares.length) h += `<div class="card"><p>You have no broodmares yet.</p><p class="sm mut" style="margin-top:4px">Retire a filly to stud next winter, or buy a mare at the sales. Breeding from your best mares is how champions are made.</p></div>`;
    for (const m of S.mares) { const s = m.cover ? T.sireOf(m.cover) : null; h += `<div class="card hc"><div class="row sp"><span class="hn">${esc(m.n)}</span><span class="sm mut">${m.age}yo mare</span></div><p class="sm">${mareLine(m)}</p><button class="pickb ${s ? 'set' : 'need'}" data-a="openSire" data-m="${m.id}"><span class="t"><b>${s ? 'In foal to ' + esc(s.n) : 'Choose a stallion'}</b><span>${s ? starTxt(s.stars) + ' · ' + (s.fee ? money(s.fee) : 'your own stallion, free') : 'Or leave her empty this year'}</span></span><span class="go">▸</span></button></div>`; }
    cta = `<button class="btn gold" data-a="wStart">Start season ${S.season + 1} ▸</button>`;
  }
  return bar() + `<main>${steps}${h}</main><div class="cta">${cta}</div>`;
}
const LOOKS = ['Small and backward', 'Plain, but a good walker', 'Athletic, with a lovely action', 'A real eyecatcher'], WH = ['“Not for me.”', '“Fine. Nothing special.”', '“I like this one.”', '“I love this one. Don’t lose it.”'];
function lotCard(l, i) {
  const nb = T.nextBid(l); let top, mid;
  if (l.ty === 'm') { const m = l.m; top = `<span class="hn">${esc(m.n)}</span><br><span class="sm mut">Broodmare, ${m.age}yo</span>`; mid = `<p class="sm">${mareLine(m)}</p>`; }
  else { const h = l.h, sire = T.sireOf(h.sire); top = `<span class="hn">${esc(h.n)}</span><br><span class="sm mut">${l.ty === 'y' ? 'Yearling ' + (h.sex === 'f' ? 'filly' : 'colt') : h.age + 'yo in training, rated ' + h.or} · by ${esc(h.sire)} (${starTxt(h.ss)}) out of a ${starTxt(h.ds)} mare</span>`;
    mid = l.ty === 'y' ? `<p class="sm">${LOOKS[h.looks]}. Bred for ${T.tripLabel(h.gs.trip)}${sire ? ', by a sire whose stock like ' + T.groundLabel(sire.gr) : ''}.</p><p class="note">${WH[l.wh]}</p>` : `<p class="sm">${h.runs} runs, ${h.wins} wins. Best at ${T.tripLabel(h.trip)}. ${LAB.con[h.con]}, ${LAB.temp[h.temp].toLowerCase()}.</p><p class="note">“You know what you're getting. Ready to run in the spring.”</p>`; }
  let act;
  if (l.done === 'you') act = `<div class="gal" style="background:#dcebdd"><b>Yours for ${money(l.price)}.</b></div>`;
  else if (l.done) act = `<div class="gal"><span class="mut">Sold to ${esc(l.by)} for ${money(l.price)}.</span></div>`;
  else act = `${l.lead === 'riv' ? `<p class="sm"><b>${esc(l.by)}</b> bids ${money(l.price)}.</p>` : ''}<div class="acts"><button class="btn sm" style="flex:1" data-a="bid" data-i="${i}">Bid ${money(nb)}</button><button class="btn sm ghost" data-a="pass" data-i="${i}">${l.lead ? 'Let it go' : 'Pass'}</button></div>`;
  return `<div class="card hc"><div class="row top"><button class="grow" ${l.ty !== 'm' ? `data-a="openLot" data-i="${i}"` : ''} style="text-align:left">${top}</button><span class="or"><b style="font-size:16px">${mk(l.guide)}</b><i>Guide</i></span></div>${mid}${act}</div>`;
}
function shSire(m) {
  const cur = m.cover, budget = S.cash + (cur ? (T.sireOf(cur) || { fee: 0 }).fee : 0), list = T.sires().slice().sort((a, b) => (a.fee > budget) - (b.fee > budget) || (b.own || 0) - (a.own || 0) || b.stars - a.stars || a.fee - b.fee);
  return shead(`For ${esc(m.n)}`, 'Choose a stallion', `She is ${mareLine(m)}. Stars are class. A sire also passes on his trip, his ground and when his stock mature.`) + `<div class="sh-b"><button class="opt${!cur ? ' on' : ''}" data-a="sire" data-m="${m.id}" data-s=""><span class="l1"><b>Leave her empty this year</b></span></button>
    ${list.map(s => `<button class="opt${cur === s.n ? ' on' : ''}" data-a="sire" data-m="${m.id}" data-s="${esc(s.n)}" ${s.fee > budget ? 'disabled style="opacity:.45"' : ''}><span class="l1"><b>${esc(s.n)}</b><span class="stars" style="--lo:${s.stars * 20}%;--hi:${s.stars * 20}%">★★★★★</span></span><span class="l2">${T.tripLabel(s.opt)} · ${T.groundLabel(s.gr)} · stock mature ${{ e: 'early', n: 'at three', l: 'late' }[s.peak]} · <b>${s.own ? 'yours, free' : money(s.fee)}</b></span></button>`).join('')}</div>`;
}

// ---------------------------------------------------------------- taps
const A = {
  tab(d) { UI.tab = d.t; UI.reset = false; render(); },
  close() { UI.sheet = null; if (S && T.tier() > S.seenTier && S.phase !== 'raceday') { S.seenTier = T.tier(); save(); } render(true); },
  col(d) { const sp = UI.setup.silk; sp[d.k] = d.c; if (d.k === 'b2') sp.c = d.c; grabName(); render(true); },
  pat(d) { UI.setup.silk.p = d.p; grabName(); render(true); },
  start() { grabName(); const u = UI.setup; T.newGame({ stable: u.name.trim() || 'Warren Hill Stud', silk: u.silk }); UI.tab = 'yard'; save(); render(); },
  tipOk() { S.tips.intro = 1; save(); render(true); },
  openEntry(d) { UI.sheet = { t: 'entry', h: +d.h }; render(true); },
  showAll() { UI.sheet.all = 1; render(true); },
  pick(d) { T.enter(+d.h, d.r === '' ? null : +d.r); save(); if (!d.stay) UI.sheet = null; render(true); },
  openGallop(d) { UI.sheet = { t: 'gallop', h: +d.h }; render(true); },
  gallop(d) { const h = T.horse(+d.h), r = T.gallop(+d.h, d.g); if (!r) return; save(); UI.sheet = { t: 'msg', k: 'From the gallops', title: h.n, say: r.text, rev: r.rev }; render(true); },
  openHorse(d) { UI.sheet = { t: 'horse', h: +d.h, tile: 'trip' }; render(true); },
  openLot(d) { UI.sheet = { t: 'horse', lot: +d.i, tile: 'trip' }; render(true); },
  tile(d) { UI.sheet.tile = d.k; render(true); },
  rename(d) { const el = document.getElementById('rename'), v = el && el.value.trim(); if (v) { T.horse(+d.h).n = v.slice(0, 20); save(); toast('Renamed.'); render(true); } },
  sell(d) { if (!UI.sheet.sell) { UI.sheet.sell = 1; render(true); return; } const h = T.horse(+d.h), v = T.sell(h.id); UI.sheet = null; save(); toast(`${h.n} sold for ${money(v)}.`); render(true); },
  race(d) { UI.sheet = { t: 'race', r: +d.r }; render(true); },
  auto() { const n = T.autoEnter(); save(); toast(n ? `Your trainer entered ${n} horse${n > 1 ? 's' : ''}.` : 'Your trainer sees nothing worth running in.'); render(true); },
  go() { T.goRacing(); UI.rd = { stage: 'card' }; UI.sheet = null; save(); render(); },
  rdWatch() { UI.rd.stage = 'run'; render(); },
  rdResult() { UI.rd.stage = 'result'; render(); },
  rdNext() { const rd = S.rd; if (rd.i < rd.res.length - 1) { rd.i++; UI.rd = { stage: 'card' }; } else { S.phase = 'summary'; UI.rd = null; tierCheck(); } save(); render(); },
  rdAll() { S.phase = 'summary'; UI.rd = null; tierCheck(); save(); render(); },
  next() { T.endFortnight(); S = T.S; UI.tab = 'yard'; UI.sheet = null; if (S.phase === 'winter') tierCheck(); save(); render(); },
  toWinter() { T.skipToWinter(); S = T.S; UI.sheet = null; tierCheck(); save(); render(); },
  wStep(d) { S.w.step = +d.s; save(); render(); },
  plan(d) { S.w.plan[+d.h] = d.p; save(); render(true); },
  yplan(d) { S.w.yplan[+d.h] = d.p; save(); render(true); },
  wStable() { T.applyStable(); save(); render(); },
  openSire(d) { UI.sheet = { t: 'sire', m: +d.m }; render(true); },
  sire(d) { if (!T.setCover(+d.m, d.s || null)) toast('You can’t afford that fee.'); UI.sheet = null; save(); render(true); },
  wSaleDone() { T.closeSale(); save(); render(); },
  bid(d) { const i = +d.i, l = S.w.lots[i], r = T.bid(i); save(); if (r === 'cash') toast('You can’t afford the next bid.'); else if (r === 'full') toast(l.ty === 'm' ? 'No paddock free for another mare.' : 'No box free. Your yard is full.'); else if (r === 'won') toast(`Sold! ${l.ty === 'm' ? l.m.n : l.h.n} is yours.`); render(true); },
  pass(d) { T.pass(+d.i); save(); render(true); },
  wStart() { T.startSeason(); UI.tab = 'yard'; save(); render(); },
  reset() { if (!UI.reset) { UI.reset = true; render(true); return; } try { localStorage.removeItem(KEY); } catch (e) { } UI.reset = false; UI.setup = null; UI.sheet = null; T.use(null); render(); }
};
function tierCheck() { if (T.tier() > S.seenTier) UI.sheet = { t: 'tier' }; }
function grabName() { const el = document.getElementById('sname'); if (el && UI.setup) UI.setup.name = el.value; }
app.addEventListener('click', e => { const el = e.target.closest('[data-a]'); if (!el) { if (e.target.classList.contains('veil')) A.close(); return; } if (el.disabled) return; const f = A[el.dataset.a]; if (f) f(el.dataset, el); });
app.addEventListener('input', e => { if (e.target.id === 'sname') UI.setup.name = e.target.value; });
load(); render();
window.TBUI = { UI, render, A };
})();
