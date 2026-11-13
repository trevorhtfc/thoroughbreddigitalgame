"""The race view's sounds from the owner's recordings (13 Nov 2026), in tools/sound/sources/:

  cheltenham-roar.mp3        the Cheltenham roar: the crowd waiting, "and they're off" from 4.05 s, the roar
  stalls-rare-view.mp3       a rare view from the stalls: the latches click at 1.475 s, the doors crash at 1.93 s, the field breaks
  japan-cup-crowd.mp3        the Japan Cup crowd: a huge, steady roar with no single voice in it
  aintree-crowd.mp3          the Aintree crowd on Grand National day
  grand-national-finish.mp3  the crowd at the Grand National finish
  galloping-pixabay.mp3      horses galloping (Pixabay sound effect, free to use)

What it makes (race-view/assets/sound/, read by race-sound.js through sounds.json):
  off.mp3            the off: the stalls opening (1 to 2.5 s of the stalls recording, as it is) laid in at 3 s of the
                     Cheltenham roar, so the doors crash just before "and they're off", the roar blended up through it
  middle.mp3         from after the off to about 3f out (loop): the real crowds with their commentators (Cheltenham,
                     Aintree), muted, the field galloping (owner, 13 Nov)
  finish.mp3         from about 3f out: the Grand National finish (crowd and commentary) rising and opening up to the
                     line FINISH_LINE_AT seconds in, the Japan Cup roar under it, the surge, then applause (owner, 13 Nov)
  crowd-murmur.mp3   the crowd waiting, before the off and after the race (loop): the real crowds, softened and distant
  crowd-excited.mp3  Aintree (loop): a long race passing the stands
  gallop.mp3         the field galloping (loop), for close shots and the slow-motion replay

The commentary is the real commentators in the clips, overlaid with their own crowds (owner, 13 Nov: the made voice
"isn't great"), each brought forward a little out of its crowd (lift_voice).

    pip install --break-system-packages espeakng-loader      (once: make_race_sounds.py, for the claps, needs it)
    python3 tools/sound/mix_real_sounds.py
"""
import subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
SRC, OUT = HERE / "sources", HERE.parents[1] / "race-view" / "assets" / "sound"
SR = 44100
rng = np.random.default_rng(2026)
sys.path.insert(0, str(HERE))

def load(name):
    with tempfile.TemporaryDirectory() as d:
        w = Path(d) / "a.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SRC / name), "-ac", "2", "-ar", str(SR), str(w)], check=True)
        sr, x = wavfile.read(w)
    return x.T.astype(np.float64) / 32768.0                     # (2, n)

def sos(kind, f, order=2, q=None):
    if kind == "band": return signal.butter(order, f, "bandpass", fs=SR, output="sos")
    return signal.butter(order, f, kind, fs=SR, output="sos")
def filt(x, kind, f, order=2): return signal.sosfiltfilt(sos(kind, f, order), x, axis=-1)
def peak(x, f, gain_db, q=1.0):                                 # a bell boost or cut
    b, a = signal.iirpeak(f, q, fs=SR); y = signal.lfilter(b, a, x, axis=-1)
    return x + (10 ** (gain_db / 20) - 1) * y
def cut(x, t0, t1): return x[:, int(t0 * SR):int(t1 * SR)].copy()
def fade(x, a=0.0, b=0.0):
    x = x.copy(); n = x.shape[1]
    if a: k = int(a * SR); x[:, :k] *= np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    if b: k = int(b * SR); x[:, n - k:] *= np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    return x
def rms(x): return np.sqrt((x ** 2).mean())
def level(x, db): return x * 10 ** (db / 20) / max(rms(x), 1e-9)
def place(dst, src, t, g=1.0):
    i = int(t * SR); j = min(src.shape[1], dst.shape[1] - i)
    if j > 0: dst[:, i:i + j] += g * src[:, :j]
def width(x, w):                                                # stereo width: 0 mono, 1 as is, >1 wider
    mid, side = (x[0] + x[1]) / 2, (x[0] - x[1]) / 2
    return np.stack([mid + w * side, mid - w * side])
def tail(x, seconds, wet, tone=5000):
    """Open air: a soft, short tail."""
    m = int(seconds * SR); t = np.arange(m) / SR; out = np.zeros((2, x.shape[1] + m))
    for c in (0, 1):
        ir = rng.standard_normal(m) * np.exp(-t * 6.9 / seconds); ir = signal.sosfilt(sos("low", tone), ir)
        ir[: int(0.015 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
        out[c, :x.shape[1] + m - 1] = signal.fftconvolve(x[c], ir)
    y = np.zeros_like(out); y[:, :x.shape[1]] = x; return y + wet * out

def loop_of(x, length, xf=1.5):
    """A loop of 'length' seconds from x: its end crossfaded (equal power) into its start, so it joins up."""
    n, k = int(length * SR), int(xf * SR)
    assert x.shape[1] >= n + k, (x.shape[1] / SR, length, xf)
    body = x[:, :n].copy(); over = x[:, n:n + k]
    a = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    body[:, :k] = body[:, :k] * np.sqrt(a) + over * np.sqrt(1 - a)
    return body

LOOPS = {}                                                      # name -> the loop's exact length (s), for sounds.json
def write(name, x, loop=False, rms_db=None, peak_lim=0.89, tail_fade=0.05):
    if rms_db is not None: x = level(x, rms_db)
    p = np.abs(x).max()
    if p > peak_lim * 0.7: x = peak_lim * np.tanh(x / peak_lim)          # a soft limit, never a hard clip
    if loop:                                                    # half a second of the loop either side of it
        LOOPS[name] = round(x.shape[1] / SR, 4)
        h = SR // 2; x = np.concatenate([x[:, -h:], x, x[:, :h]], axis=1)
    elif tail_fade: x = fade(x, 0, tail_fade)
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        w = Path(d) / "a.wav"; wavfile.write(w, SR, (np.clip(x.T, -0.98, 0.98) * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-c:a", "libmp3lame", "-b:a", "128k", str(OUT / f"{name}.mp3")], check=True)
    print(f"{name}.mp3  {x.shape[1] / SR:5.1f} s  {(OUT / f'{name}.mp3').stat().st_size // 1024} KB  rms {20 * np.log10(rms(x)):.1f} dB")
    return x

# ---------------------------------------------------------------- the sources
chel, stall, japan, aintree, gn, gal = (load(n) for n in ["cheltenham-roar.mp3", "stalls-rare-view.mp3", "japan-cup-crowd.mp3",
                                                         "aintree-crowd.mp3", "grand-national-finish.mp3", "galloping-pixabay.mp3"])
CHEL_VOICE = 4.05                               # "and they're off" starts here in the Cheltenham clip
STALLS_FROM, STALL_LATCH, STALL_CRASH = 1.0, 1.475, 1.93   # the stalls clip: the opening (owner: 1 to 2.5 s), the latches, the crash
VOICE_LIFT_DB, STALLS_AFTER, CALL_TO = 10.0, 0.18, 5.7   # the call lifted up to this much, until CALL_TO; the stalls after their crash at this share
STALLS_IN = 2.8                                 # the stalls laid in at 2.8 s of the Cheltenham roar (owner said 3 s; 0.2 s earlier so the crash is over before the call at 4.0 s): latches at 3.275 s
crowd_eq = lambda x: filt(x, "high", 90, 2)     # the phones' rumble out of every crowd

# ---------------------------------------------------------------- the off: the stalls laid into the Cheltenham roar
def lift_voice(x, t0, t1, db, ramp_in=0.1, ramp_out=0.35):
    """Brings a voice forward out of a crowd: a single voice is made of clear, evenly spaced notes (its harmonics), a
    crowd is a smooth wash. Between t0 and t1 s, each moment's spectrum is compared with a smoothed copy of itself and
    what stands above the wash is lifted, up to db, between 150 Hz and 4 kHz, with a gentle lift of the voice's
    presence band."""
    f, tt, Z = signal.stft(x, SR, nperseg=4096, noverlap=4096 - 512)
    mag = np.abs(Z) + 1e-12
    k = 15                                                    # about 160 Hz either way: wider than a harmonic, narrower than a vowel
    smooth = np.exp(signal.convolve(np.log(mag), np.ones((1, 2 * k + 1, 1)) / (2 * k + 1), mode="same"))
    gain = np.clip((mag / smooth) ** 1.6, 1, 10 ** (db / 20))
    band = ((f > 150) & (f < 4000))[None, :, None]
    win = (np.clip((tt - t0) / ramp_in, 0, 1) * np.clip((t1 - tt) / ramp_out, 0, 1))[None, None, :]
    G = 1 + (gain - 1) * band * win
    G = G * (1 + 0.4 * (db / 10) * ((f > 1000) & (f < 3500))[None, :, None] * win)  # presence: consonants, the edge of the voice
    _, y = signal.istft(Z * G, SR, nperseg=4096, noverlap=4096 - 512)
    y = y[:, :x.shape[1]]
    if y.shape[1] < x.shape[1]: y = np.pad(y, ((0, 0), (0, x.shape[1] - y.shape[1])))
    return y
def clear_call(x, t):
    """Owner, 13 Nov: "you're missing the and they're off commentary as the roar goes up" / "it just says 'and', I can't
    hear the they're off". The call runs from CHEL_VOICE to about CALL_TO, the roar rising under its second half."""
    return lift_voice(x, CHEL_VOICE - 0.08, CALL_TO, VOICE_LIFT_DB)

def make_off():
    """Owner, 13 Nov: "lay [the stalls opening, 1 to 2.5 s of the stalls recording] into 3 secs of the Cheltenham roar
    and then just blend the sound up". One sound: the Cheltenham crowd waiting; at 3.0 s the stalls (their creak, the
    latches clicking at 3.475 s, the doors crashing at 3.93 s, the field breaking out); "and they're off" at 4.05 s; the
    roar swelling up through it as the stalls fade. The race view starts it so the latches click at the off
    (sounds.json: off.latchAt)."""
    chel_x = crowd_eq(cut(chel, 0.0, 10.4))
    t = np.arange(chel_x.shape[1]) / SR
    chel_x = clear_call(chel_x, t)
    chel_x = chel_x * (0.7 + 0.3 * np.clip((t - CALL_TO + 0.9) / 1.3, 0, 1))[None, :]   # the roar blended up, after the call
    chel_x = fade(chel_x, 2.2, 2.6)                           # (the race view starts it about half a second in: a soft way in)
    stalls = filt(cut(stall, STALLS_FROM, STALLS_FROM + 3.4), "high", 200, 4)    # (the stalls recording's wind rumble out)
    # the stalls as recorded up to the crash; then, so the call comes through, pulled down quickly to a background
    ts = np.arange(stalls.shape[1]) / SR; after = STALL_CRASH - STALLS_FROM + 0.07
    stalls = stalls * (STALLS_AFTER + (1 - STALLS_AFTER) * np.clip(1 - (ts - after) / 0.12, 0, 1))[None, :]
    stalls = fade(stalls, 0.04, 1.6)
    M = level(chel_x, -19.5)
    place(M, level(width(stalls, 1.3), -19.0), STALLS_IN)
    return write("off", M, rms_db=-19, tail_fade=0)

# ---------------------------------------------------------------- the pieces the sections are made of
def tile(x, n, start=0.0):
    """A seamless loop x laid end to end for n samples, starting 'start' seconds into it."""
    k = int(np.ceil((n + start * SR) / x.shape[1])) + 1
    return np.tile(x, k)[:, int(start * SR):int(start * SR) + n]

def murmur_loop():
    """The crowd waiting: the real crowds, distant and soft (no cheering), with the Cheltenham crowd's buzz before the
    off. The words of a big crowd far off run together; that's what's wanted here."""
    L = 26
    a = loop_of(crowd_eq(cut(aintree, 0.3, 23.0)), 20.5, 1.5)
    b = loop_of(crowd_eq(cut(japan, 3.0, 32.0)), 26, 2.5)
    c = loop_of(crowd_eq(cut(chel, 0.0, 3.9)), 2.4, 1.4)
    n = int(L * SR); a, b, c = tile(a, n), tile(np.roll(b, int(7 * SR), axis=1), n), tile(c, n)
    def distant(x, lp, db):
        x = filt(x, "low", lp, 2); x = peak(x, 300, 3, 0.8); return level(x, db)
    M = distant(a, 1300, -24) + distant(b, 900, -26) + distant(c, 2200, -27)
    t = np.arange(M.shape[1]) / SR; M *= 1 + 0.12 * np.sin(2 * np.pi * t * 3 / L) + 0.07 * np.sin(2 * np.pi * t * 5 / L + 1.3)   # it breathes
    M = width(M, 1.3)
    return loop_of(np.concatenate([M, M[:, :int(2 * SR)]], axis=1), L - 0.1, 2.0)
def excited_loop():
    a = crowd_eq(cut(aintree, 0.2, 23.1)); a = peak(a, 2400, 2, 0.7)
    return width(loop_of(a, 20.6, 2.2), 1.2)
def roar_loop():
    j = loop_of(crowd_eq(cut(japan, 1.0, 36.0)), 31.0, 3.0); g = loop_of(crowd_eq(cut(gn, 0.5, 32.0)), 29.0, 2.5)
    n = int(31.0 * SR); M = level(j, -18) + level(tile(g, n), -20.5)
    return width(loop_of(np.concatenate([M, M[:, :int(3 * SR)]], axis=1), 30.5, 2.5), 1.25)
def gallop_loop():
    x = filt(cut(gal, 0.05, 8.05), "low", 9000, 2)            # (the recording's whine above 10 kHz out)
    a = loop_of(x, 7.3, 0.6)
    b = np.roll(a, int(3.1 * SR), axis=1); b = filt(b, "low", 2500, 2); b = width(b[::-1], 1.0)   # the same field further off
    c = np.roll(a, int(5.2 * SR), axis=1); c = filt(c, "low", 1200, 2)
    return width(a + 0.55 * b + 0.35 * c, 1.1)
def applause(n, start):
    """Hand claps (made: there's no applause in the recordings), starting 'start' seconds in and tailing off."""
    from make_race_sounds import clap_kit
    kit = clap_kit(); claps = np.zeros((2, n))
    for _ in range(260):
        rate = rng.uniform(3.4, 6.5); st = start + rng.uniform(0, 2.2) ** 1.3; stop = st + 3 + rng.gamma(2.2, 1.8)
        d = rng.uniform(6, 70); g = 6.0 / d * rng.uniform(0.5, 1); pan = rng.uniform(-0.95, 0.95); c = kit[rng.integers(len(kit))]
        a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); tt = st
        while tt < min(stop, n / SR - 0.5):
            i = int(tt * SR); j = min(len(c), n - i); f = np.clip((stop - tt) / 1.5, 0, 1) * rng.uniform(0.7, 1) * g
            claps[0, i:i + j] += c[:j] * f * a[0]; claps[1, i:i + j] += c[:j] * f * a[1]
            tt += 1 / rate * rng.uniform(0.92, 1.08)
    return tail(claps, 1.2, 0.35, 5000)[:, :n]

# ---------------------------------------------------------------- the middle: from after the off to about 3 furlongs out (a loop)
# Owner, 13 Nov: "the commentary isn't great [the made voice]. Some of these clips have crowd and commentary which I'm
# happy for you to overlay to get the sound." So the commentary is now the real commentators, with their crowds.
MIDDLE = {"bed": -26.0, "murmur": -31.0, "gallop": -24.5}   # each part's level (dB), here and at the start of the finish
MIDDLE_TALK = [            # (clip, from, to, voice from, voice to): the crowd with its commentator, laid end to end
    ("chel", 7.6, 12.4, 8.5, 12.4),                         # Cheltenham: the commentator after the roar
    ("aintree", 0.2, 23.0, 0.2, 8.0),                       # Aintree: its announcer over the crowd (first 8 s)
]
def talk_bed(parts, xf=1.0):
    """The clips laid end to end with crossfades, each with its commentator brought forward, all at one level."""
    clips = {"chel": chel, "aintree": aintree, "gn": gn, "japan": japan}
    out = None
    for name, a, b, v0, v1 in parts:
        x = crowd_eq(cut(clips[name], a, b)); x = lift_voice(x, v0 - a, v1 - a, 6.0, 0.3, 0.5); x = level(x, -20)
        if out is None: out = x; continue
        k = int(xf * SR); r = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
        out = np.concatenate([out[:, :-k], out[:, -k:] * np.sqrt(1 - r) + x[:, :k] * np.sqrt(r), x[:, k:]], axis=1)
    return out
def make_middle():
    """Owner, 13 Nov: "a flexible looping middle section that can handle the off all the way till the 3f stage or so..
    a slightly more muted crowd, galloping and background PA announcer". One loop: the real crowds with their
    commentators, muted (quieter and softened, as if over the loudspeakers from across the course), the gallop, and the
    crowd waiting under it all so it never drops away."""
    bed = talk_bed(MIDDLE_TALK)
    L = bed.shape[1] / SR - 1.5; n = int((L + 1.5) * SR)
    bed = filt(bed, "low", 3200, 2); bed = peak(bed, 1800, 2.5, 1.0)          # muted, the voices kept clear
    M = level(bed, MIDDLE["bed"]) + level(tile(murmur_loop(), n, 4.0), MIDDLE["murmur"]) + level(tile(gallop_loop(), n), MIDDLE["gallop"])
    return write("middle", loop_of(M, L, 1.5), loop=True)

# ---------------------------------------------------------------- the finish: from about 3 furlongs out to the line and after
FINISH_LINE_AT = 37.0                                         # the line, this far into finish.mp3 (sounds.json: finish.lineAt)
GN_IN = 4.5                                                   # the Grand National finish clip (crowd and commentary) starts here
def make_finish():
    """Owner, 13 Nov: "the finish sound effect where the crowd get much more animated as does the background PA leading
    to the cheer as they cross the line"; then "overlay [the clips with crowd and commentary] to get the sound". Begins as
    the middle does (the race view crossfades into it about 3f out); the Grand National finish, crowd and commentary,
    comes in and opens up, louder and clearer all the way to the line, with the Japan Cup's roar under it; the gallop
    coming closer; the Japan Cup crowd's surge as they cross; then the roar ebbing into applause."""
    FL = FINISH_LINE_AT; total = FL + 14.0; n = int(total * SR); t = np.arange(n) / SR
    env = lambda pts: np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    db = lambda pts: 10 ** (env(pts) / 20)
    # the start: as the middle (its bed carried on, muted), handing over to the Grand National
    bed = talk_bed(MIDDLE_TALK); bed = peak(filt(bed, "low", 3200, 2), 1800, 2.5, 1.0)
    bed = level(tile(loop_of(bed, bed.shape[1] / SR - 1.5, 1.5), n, 9.0), MIDDLE["bed"]) * db([(0, 0), (GN_IN, -1), (GN_IN + 4, -14), (GN_IN + 7, -40), (total, -60)])[None]
    murmur = level(tile(murmur_loop(), n, 11.0), MIDDLE["murmur"]) * db([(0, 0), (12, -4), (24, -14), (FL, -30), (total, -40)])[None]
    # the Grand National finish, crowd and commentary: in from GN_IN, rising and opening up to the line
    g = crowd_eq(cut(gn, 0.0, 32.3)); g = lift_voice(g, 0.0, 32.3, 6.0, 0.3, 0.5)
    gl = g.shape[1] / SR; tg = np.arange(g.shape[1]) / SR
    g = fade(g, 2.5, 0.0)
    muffled = filt(g, "low", 2400, 2); open_ = np.clip((tg - 6) / 18, 0, 1)[None, :]   # muffled to begin with, opening up
    g = muffled * (1 - open_) + g * open_
    G = np.zeros((2, n)); place(G, level(g, -19), GN_IN)
    G *= db([(0, -60), (GN_IN, -9), (GN_IN + 6, -7), (20, -4), (28, -1.5), (FL - 1, 0), (GN_IN + gl - 0.5, 0), (GN_IN + gl, -60), (total, -60)])[None]
    roar = level(tile(roar_loop(), n, 5.0), -19) * db([(0, -40), (14, -26), (24, -12), (30, -6), (FL - 1, -2), (FL + 1, 0), (FL + 4, -6), (FL + 8, -16), (FL + 12, -30), (total, -40)])[None]
    hooves = level(tile(gallop_loop(), n, 2.5), MIDDLE["gallop"]) * db([(0, 0), (20, 2), (30, 5), (FL - 2, 6), (FL + 1, 3), (FL + 5, -12), (FL + 8, -40), (total, -60)])[None]
    M = bed + murmur + G + roar + hooves
    # the surge as they cross: the Japan Cup crowd's last swell, its peak (about 2 s into this cut) just after the line
    surge = fade(crowd_eq(cut(japan, 36.2, 40.6)), 0.6, 0.8); place(M, level(width(surge, 1.25), -15), FL - 1.6)
    claps = applause(n, FL + 1.4); place(M, level(claps[:, int((FL + 1.4) * SR):], -22.5), FL + 1.4)
    return write("finish", M, tail_fade=2.0)

# ---------------------------------------------------------------- the loops the race view also keeps
def make_murmur(): return write("crowd-murmur", murmur_loop(), loop=True, rms_db=-21)       # before the off and after the race
def make_excited(): return write("crowd-excited", excited_loop(), loop=True, rms_db=-18)    # a long race passing the stands
def make_gallop(): return write("gallop", gallop_loop(), loop=True, rms_db=-17)            # close shots and the replay

if __name__ == "__main__":
    which = sys.argv[1:] or ["off", "middle", "finish", "murmur", "excited", "gallop"]
    for w in which:
        {"off": make_off, "middle": make_middle, "finish": make_finish, "murmur": make_murmur, "excited": make_excited,
         "gallop": make_gallop}[w]()
    # each loop's exact length into sounds.json (by file name), so the race view loops it at exactly the join
    import json
    cfg_p = OUT / "sounds.json"; cfg = json.loads(cfg_p.read_text())
    for f in cfg["files"].values():
        stem = f["file"].rsplit(".", 1)[0]
        if stem in LOOPS: f["loop"] = LOOPS[stem]
    cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print("loops:", LOOPS)
