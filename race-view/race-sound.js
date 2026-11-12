// The race view's sound: the crowd and the horses. Engine-neutral apart from the browser's Web Audio; it holds no race
// rules. The race view works out, each frame, how excited the crowd is, how near the camera is to the crowd and to the
// horses, and calls update(); this file turns that into sound. The sounds and every level live in
// assets/sound/sounds.json (tools/sound/make_race_sounds.py makes the files; any can be swapped for a real recording).
//
// Layers: the crowd's chatter, the crowd stirring (chatter and shouts), the roar, mixed by how excited the crowd is and
// muffled with distance; the field galloping, by how near the camera is to the horses, panned to where they are and
// sped up or slowed with them (slowed right down in the slow-motion replay); and one-off sounds (the stalls opening,
// the applause after the line).
//
// Browsers only let a page make sound after the player has tapped or clicked something. In the game the player has
// already tapped "Watch in 3D", so the game's own sound (already playing) is borrowed if there is one; otherwise, if
// the browser holds the sound back, the speaker button pulses and the first tap anywhere lets it out.

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

export async function create({ base = "assets/sound/", shared = null, on = false, onChange = null } = {}) {
  const CFG = await fetch(base + "sounds.json").then((r) => r.json());
  const MIX = CFG.mix;
  let ac = null, own = false, master = null, crowdBus = null, crowdLow = null, gallopGain = null, gallopLow = null, gallopPan = null;
  const buffers = {}, loops = {}, gains = {};
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
      const g = ac.createGain(); g.gain.value = 0; g.connect(k === "gallop" ? gallopGain : crowdBus);
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
  // each frame: crowd { excitement 0..1, near 0..1 (camera to the crowd), duck 0..1 }, hooves { near 0..1, pan -1..1,
  // rate (1 = the cruising gallop), moving 0..1 }
  S.update = ({ crowd, hooves }) => {
    if (!started) return;
    const E = crowd.excitement, C = CFG.crowd;
    const lv = {
      murmur: MIX.murmur * (1 - 0.7 * smooth(0.3, 0.9, E)),
      excited: MIX.excited * smooth(C.excitedFrom, C.excitedFull, E) * (1 - 0.6 * smooth(0.78, 1, E)),
      roar: MIX.roar * smooth(C.roarFrom, 1, E),
      gallop: MIX.gallop * hooves.moving * hooves.near ** 1.6,
    };
    for (const k in lv) if (gains[k]) to(gains[k].gain, lv[k], k === "gallop" ? 0.12 : 0.5);
    const n = crowd.near;
    to(crowdBus.gain, (C.farLevel + (1 - C.farLevel) * n) * (crowd.duck ?? 1), 0.6);
    to(crowdLow.frequency, C.farMuffle * (16000 / C.farMuffle) ** (n ** 0.7), 0.6);
    to(gallopLow.frequency, 500 * 16 ** hooves.near, 0.15);
    if (gallopPan.pan) to(gallopPan.pan, Math.max(-0.85, Math.min(0.85, hooves.pan)), 0.15);
    if (loops.gallop) to(loops.gallop.playbackRate, Math.max(0.2, Math.min(1.25, hooves.rate)), 0.2);
    S.levels = { E: +E.toFixed(2), near: +n.toFixed(2), hNear: +hooves.near.toFixed(2), hMoving: +hooves.moving.toFixed(2), rate: +hooves.rate.toFixed(2), pan: +hooves.pan.toFixed(2), ...Object.fromEntries(Object.entries(lv).map(([k, v]) => [k, +v.toFixed(2)])) };
  };
  // a one-off: the stalls opening, the applause
  S.play = (k, level = 1) => {
    if (!started || !buffers[k] || !wanted) return;
    const s = ac.createBufferSource(), g = ac.createGain(); s.buffer = buffers[k];
    g.gain.value = (MIX[k] ?? 1) * level; s.connect(g); g.connect(CFG.files[k].bus === "master" ? master : crowdBus);
    s.start(); s.onended = () => { s.disconnect(); g.disconnect(); };
  };
  // the page is going: when the game's sound was borrowed, nothing of the race must play on under the board
  S.stop = () => { if (!ac) return; stopLoops(); master.disconnect(); if (own) ac.close(); };
  addEventListener("pagehide", S.stop);
  S.config = CFG;
  if (on) S.set(true);
  return S;
}
