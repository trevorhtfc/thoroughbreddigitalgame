// The race view's sound: the crowd and the horses. Engine-neutral apart from the browser's Web Audio; it holds no race
// rules. The race view works out, each frame, how excited the crowd is, how near the camera is to the crowd and to the
// horses, and calls update(); this file turns that into sound. The sounds and every level live in
// assets/sound/sounds.json (tools/sound/mix_real_sounds.py makes the files from the owner's recordings).
//
// In sections (owner, 13 Nov): the crowd waiting (a loop), the off (one sound), the middle (a loop: the crowd a little
// muted, the gallop, the course commentator), the finish (one sound, timed to the line: the crowd and commentator rising
// to the cheer, then applause); plus the horses up close (a loop, by how near the shot looks, slowed in the replay) and
// the crowd lifting as a long race passes the stands. The race view says which section is playing.
//
// Browsers only let a page make sound after the player has tapped or clicked something. In the game the player has
// already tapped "Watch in 3D", so the game's own sound (already playing) is borrowed if there is one; otherwise, if
// the browser holds the sound back, the speaker button pulses and the first tap anywhere lets it out.

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

export async function create({ base = "assets/sound/", shared = null, on = false, onChange = null } = {}) {
  const CFG = await fetch(base + "sounds.json").then((r) => r.json());
  const MIX = CFG.mix;
  let ac = null, own = false, master = null, crowdBus = null, crowdLow = null, gallopGain = null, gallopLow = null, gallopPan = null, paBus = null;
  const buffers = {}, loops = {}, gains = {}, once = new Set();
  const bus = (name) => ({ crowd: crowdBus, hooves: gallopGain, pa: paBus }[name] || master);
  let loading = null, started = false, wanted = on, paused = false, hidden = false, locked = false;
  const S = { get on() { return wanted; }, get locked() { return locked; }, levels: {} };

  function context() {
    if (ac) return ac;
    const c = shared && shared();
    if (c && c.state === "running") { ac = c; own = false; }
    else { ac = new (window.AudioContext || window.webkitAudioContext)(); own = true; }
    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 3; comp.attack.value = 0.01; comp.release.value = 0.3;
    comp.connect(ac.destination);
    master = ac.createGain(); master.gain.value = 0; master.connect(comp);
    crowdLow = ac.createBiquadFilter(); crowdLow.type = "lowpass"; crowdLow.frequency.value = 16000; crowdLow.Q.value = 0.5; crowdLow.connect(master);
    crowdBus = ac.createGain(); crowdBus.connect(crowdLow);
    gallopPan = ac.createStereoPanner ? ac.createStereoPanner() : ac.createGain(); gallopPan.connect(master);
    gallopLow = ac.createBiquadFilter(); gallopLow.type = "lowpass"; gallopLow.frequency.value = 8000; gallopLow.connect(gallopPan);
    gallopGain = ac.createGain(); gallopGain.gain.value = 0; gallopGain.connect(gallopLow);
    paBus = ac.createGain(); paBus.connect(master);
    return ac;
  }
  // older Safari only has the callback form of decodeAudioData
  const decode = (data) => new Promise((res, rej) => { const p = ac.decodeAudioData(data, res, rej); if (p && p.then) p.then(res, rej); });
  function load() {
    if (!loading) loading = Promise.all(Object.entries(CFG.files).map(([k, f]) =>
      fetch(base + f.file).then((r) => r.arrayBuffer()).then(decode).then((b) => { buffers[k] = b; })
        .catch(() => console.warn("race sound: couldn't load", f.file))));
    return loading;
  }
  // a loop runs from 0.25 s in (its files carry half a second of the loop either side), starting somewhere random
  function startLoops() {
    if (started) return;
    started = true;
    for (const [k, f] of Object.entries(CFG.files)) {
      if (!f.loop || !buffers[k]) continue;
      const g = ac.createGain(); g.gain.value = 0; g.connect(bus(f.bus || (k === "gallop" ? "hooves" : "crowd")));
      const s = ac.createBufferSource(); s.buffer = buffers[k]; s.loop = true;
      s.loopStart = 0.25; s.loopEnd = Math.min(buffers[k].duration - 0.05, 0.25 + f.loop);
      s.connect(g); s.start(ac.currentTime + 0.02, 0.25 + Math.random() * f.loop);
      loops[k] = s; gains[k] = g;
    }
  }
  function stopLoops() {
    for (const k in loops) { try { loops[k].stop(); } catch (e) {} loops[k].disconnect(); gains[k].disconnect(); delete loops[k]; delete gains[k]; }
    started = false;
  }
  const to = (param, v, tc = 0.35) => { if (param) param.setTargetAtTime(v, ac.currentTime, tc); };
  // what's heard: on, and not paused or out of sight
  function apply() {
    if (!ac) return;
    const live = wanted && !paused && !hidden;
    to(master.gain, live ? MIX.master : 0, live ? 0.4 : 0.12);
    clearTimeout(apply.t);
    if (live) { if (ac.state !== "running") ac.resume().then(checkLock, checkLock); setTimeout(checkLock, 400); }
    else if (own) apply.t = setTimeout(() => { if (!(wanted && !paused && !hidden) && ac.state === "running") ac.suspend(); }, 600);
  }
  function checkLock() {
    const was = locked;
    locked = wanted && ac && ac.state !== "running" && !paused && !hidden;
    if (locked !== was && onChange) onChange(S);
  }
  // the first tap or key anywhere lets a held-back sound out
  const unlock = () => { if (ac && wanted && ac.state !== "running") ac.resume().then(checkLock, checkLock); };
  addEventListener("pointerdown", unlock, true); addEventListener("keydown", unlock, true); addEventListener("touchend", unlock, true);
  addEventListener("visibilitychange", () => { hidden = document.hidden; apply(); });

  S.set = async (v) => {
    wanted = v;
    if (v) { context(); apply(); await load(); if (wanted) startLoops(); }
    else apply();
    checkLock();
    if (onChange) onChange(S);
  };
  S.pause = (p) => { if (p !== paused) { paused = p; apply(); } };
  // each frame: layers { name: 0..1 } (the race view decides which section is playing: the crowd waiting, the middle,
  // the crowd lifting as a long race passes the stands), crowd { near 0..1 (camera to the crowd), duck 0..1 },
  // hooves { near 0..1, pan -1..1, rate (1 = the cruising gallop), moving 0..1 } for the horses up close
  S.update = ({ layers = {}, crowd, hooves }) => {
    if (!started) return;
    const C = CFG.crowd;
    const lv = { gallop: MIX.gallop * hooves.moving * hooves.near ** 1.6 };
    for (const k in layers) lv[k] = (MIX[k] ?? 1) * layers[k];
    for (const k in lv) if (gains[k]) to(gains[k].gain, lv[k], k === "gallop" ? 0.12 : 0.4);
    const n = crowd.near;
    to(crowdBus.gain, (C.farLevel + (1 - C.farLevel) * n) * (crowd.duck ?? 1), 0.6);
    to(crowdLow.frequency, C.farMuffle * (16000 / C.farMuffle) ** (n ** 0.7), 0.6);
    to(gallopLow.frequency, 500 * 16 ** hooves.near, 0.15);
    if (gallopPan.pan) to(gallopPan.pan, Math.max(-0.85, Math.min(0.85, hooves.pan)), 0.15);
    if (loops.gallop) to(loops.gallop.playbackRate, Math.max(0.2, Math.min(1.25, hooves.rate)), 0.2);
    S.levels = { playing: [...once].map((s) => s.label).join(","), near: +n.toFixed(2), hNear: +hooves.near.toFixed(2), ...Object.fromEntries(Object.entries(lv).map(([k, v]) => [k, +v.toFixed(2)])) };
  };
  // a one-off: the off, the finish. at: seconds from now (less than 0: start that far into it)
  S.play = (k, { level = 1, at = 0 } = {}) => {
    if (!started || !buffers[k] || !wanted) return false;
    if (-at >= buffers[k].duration) return false;
    const s = ac.createBufferSource(), g = ac.createGain(); s.buffer = buffers[k];
    g.gain.value = (MIX[k] ?? 1) * level; s.connect(g); g.connect(bus(CFG.files[k].bus));
    s.start(ac.currentTime + Math.max(0, at), Math.max(0, -at)); once.add(s); s.label = k;
    Object.assign(s, { g, t0: ac.currentTime + Math.max(0, at), pos: Math.max(0, -at), rate: 1, last: ac.currentTime + Math.max(0, at) });
    s.onended = () => { once.delete(s); s.disconnect(); g.disconnect(); };
    return true;
  };
  S.playing = (k) => [...once].some((q) => q.label === k);
  // keep a one-off in step with the race (a slow computer draws the race slower than real time): want = where in the
  // sound the race is now. Small drift: played a shade faster or slower; a big one (a pause, a jump): picked up there.
  S.sync = (k, want) => {
    if (!started) return;
    const s = [...once].find((q) => q.label === k); if (!s) return;
    const now = ac.currentTime; if (now < s.t0) return;
    s.pos += (now - s.last) * s.rate; s.last = now;
    const drift = want - s.pos;
    if (Math.abs(drift) > 1.5) {
      to(s.g.gain, 0, 0.05); setTimeout(() => { try { s.stop(); } catch (e) {} }, 250); once.delete(s);
      if (want < buffers[k].duration - 0.2) S.play(k, { at: -want });
      return;
    }
    s.rate = Math.max(0.94, Math.min(1.06, 1 + drift * 0.15));
    to(s.playbackRate, s.rate, 0.3);
  };
  // the one-offs cut short (the race restarted, or jumped)
  S.hush = () => { for (const s of once) { try { s.stop(); } catch (e) {} } once.clear(); };
  // the page is going: when the game's sound was borrowed, nothing of the race must play on under the board
  S.stop = () => { if (!ac) return; S.hush(); stopLoops(); master.disconnect(); if (own) ac.close(); };
  addEventListener("pagehide", S.stop);
  S.config = CFG;
  if (on) S.set(true);
  return S;
}
