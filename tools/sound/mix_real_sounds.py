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
  crowd-murmur.mp3   the crowd waiting (loop): the real crowds, softened and distant, with the Cheltenham crowd's buzz
  crowd-excited.mp3  the crowd stirring (loop): Aintree
  crowd-roar.mp3     the roar (loop): the Japan Cup and the Grand National finish together
  line.mp3           at the line: the Japan Cup's last surge, then it ebbs into applause (made here)
  gallop.mp3         the field galloping (loop): the gallop recording, doubled up into a field
  pa-race.mp3        the course commentary, through the loudspeakers from across the course (loop; a stand-in voice)
  pa-finish.mp3      the same commentator in the last furlongs (loop)

The commentary voice is eSpeak (the only speaking voice that runs here) put through the course's loudspeakers: a
horn speaker's narrow band, a little overdrive, the echo of speakers further along the stand and the open air, low
under the crowd, so the rise and fall of a commentator comes through but not the words. A real commentary recording
can take its place: put it in sources/ as commentary.mp3 (calm) and/or commentary-finish.mp3 and run this again.

    pip install --break-system-packages espeakng-loader      (once, for the commentary)
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
def clear_call(x, t):
    """Owner, 13 Nov: "you're missing the and they're off commentary as the roar goes up" / "it just says 'and', I can't
    hear the they're off". The call runs from CHEL_VOICE to about CALL_TO, the roar rising under its second half. A
    single voice is made of clear, evenly spaced notes (its harmonics); a roaring crowd is a smooth wash. So over the call,
    each moment's spectrum is compared with a smoothed copy of itself, and what stands above the wash (the commentator)
    is lifted, up to VOICE_LIFT_DB, between 150 Hz and 4 kHz; plus a gentle lift of the voice's presence band."""
    f, tt, Z = signal.stft(x, SR, nperseg=4096, noverlap=4096 - 512)
    mag = np.abs(Z) + 1e-12
    k = 15                                                    # about 160 Hz either way: wider than a harmonic, narrower than a vowel
    smooth = np.exp(signal.convolve(np.log(mag), np.ones((1, 2 * k + 1, 1)) / (2 * k + 1), mode="same"))
    gain = np.clip((mag / smooth) ** 1.6, 1, 10 ** (VOICE_LIFT_DB / 20))
    band = ((f > 150) & (f < 4000))[None, :, None]
    win = (np.clip((tt - (CHEL_VOICE - 0.08)) / 0.1, 0, 1) * np.clip((CALL_TO - tt) / 0.35, 0, 1))[None, None, :]
    G = 1 + (gain - 1) * band * win
    G = G * (1 + 0.4 * ((f > 1000) & (f < 3500))[None, :, None] * win)          # presence: consonants, the edge of the voice
    _, y = signal.istft(Z * G, SR, nperseg=4096, noverlap=4096 - 512)
    y = y[:, :x.shape[1]]
    if y.shape[1] < x.shape[1]: y = np.pad(y, ((0, 0), (0, x.shape[1] - y.shape[1])))
    return y

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

# ---------------------------------------------------------------- the crowd: waiting, stirring, roaring
def make_murmur():
    """The crowd between races and while they go down and load: the real crowds, distant and soft (no cheering), with the
    Cheltenham crowd's buzz before the off. The words of a big crowd far off run together; that's what's wanted here."""
    L = 26
    a = loop_of(crowd_eq(cut(aintree, 0.3, 23.0)), 20.5, 1.5)
    b = loop_of(crowd_eq(cut(japan, 3.0, 32.0)), 26, 2.5)
    c = loop_of(crowd_eq(cut(chel, 0.0, 3.9)), 2.4, 1.4)
    def tile(x): k = int(np.ceil(L * SR / x.shape[1])) + 1; return np.tile(x, k)[:, :int(L * SR)]
    a, b, c = tile(a), tile(np.roll(b, int(7 * SR), axis=1)), tile(c)
    def distant(x, lp, db):
        x = filt(x, "low", lp, 2); x = peak(x, 300, 3, 0.8); return level(x, db)
    M = distant(a, 1300, -24) + distant(b, 900, -26) + distant(c, 2200, -27)
    t = np.arange(M.shape[1]) / SR; M *= 1 + 0.12 * np.sin(2 * np.pi * t * 3 / L) + 0.07 * np.sin(2 * np.pi * t * 5 / L + 1.3)   # it breathes
    M = width(M, 1.3)
    # the loop is made of loops of other lengths; make the whole one join up
    M = loop_of(np.concatenate([M, M[:, :int(2 * SR)]], axis=1), L - 0.1, 2.0)
    return write("crowd-murmur", M, loop=True, rms_db=-21)
def make_excited():
    a = crowd_eq(cut(aintree, 0.2, 23.1)); a = peak(a, 2400, 2, 0.7)
    x = loop_of(a, 20.6, 2.2)
    return write("crowd-excited", width(x, 1.2), loop=True, rms_db=-18)
def make_roar():
    j = crowd_eq(cut(japan, 1.0, 36.0)); g = crowd_eq(cut(gn, 0.5, 32.0))
    j = loop_of(j, 31.0, 3.0); g = loop_of(g, 29.0, 2.5)
    L = 31.0; n = int(L * SR)
    g = np.tile(g, 2)[:, :n]                                  # (its 29 s loop inside 31 s; the whole is joined up below)
    M = level(j, -18) + level(g, -20.5)
    M = loop_of(np.concatenate([M, M[:, :int(3 * SR)]], axis=1), L - 0.5, 2.5)
    return write("crowd-roar", width(M, 1.25), loop=True, rms_db=-16.5)

# ---------------------------------------------------------------- at the line: the last surge, ebbing into applause
def make_line():
    from make_race_sounds import clap_kit                     # the made hand claps (no applause in the recordings)
    T = np.zeros((2, int(15 * SR)))
    surge = crowd_eq(cut(japan, 36.2, 40.6)); surge = fade(surge, 0.05, 0.6)
    place(T, level(surge, -15), 0.0)
    after = crowd_eq(cut(gn, 18.0, 30.0)); after = fade(after, 0.2, 9.0); place(T, level(after, -19), 2.6)
    kit = clap_kit(); clap = np.zeros(T.shape[1])
    claps = np.zeros((2, T.shape[1]))
    for _ in range(260):
        rate = rng.uniform(3.4, 6.5); start = 1.6 + rng.uniform(0, 2.2) ** 1.3; stop = start + 3 + rng.gamma(2.2, 1.8)
        d = rng.uniform(6, 70); g = 6.0 / d * rng.uniform(0.5, 1); pan = rng.uniform(-0.95, 0.95); c = kit[rng.integers(len(kit))]
        a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); tt = start
        while tt < min(stop, 14.5):
            i = int(tt * SR); j = min(len(c), T.shape[1] - i); f = np.clip((stop - tt) / 1.5, 0, 1) * rng.uniform(0.7, 1) * g
            claps[0, i:i + j] += c[:j] * f * a[0]; claps[1, i:i + j] += c[:j] * f * a[1]
            tt += 1 / rate * rng.uniform(0.92, 1.08)
    claps = tail(claps, 1.2, 0.35, 5000)[:, :T.shape[1]]
    place(T, level(claps, -22), 0)
    return write("line", T, rms_db=-17, tail_fade=1.5)

# ---------------------------------------------------------------- the field galloping
def make_gallop():
    x = filt(cut(gal, 0.05, 8.05), "low", 9000, 2)            # (the recording's whine above 10 kHz out)
    a = loop_of(x, 7.3, 0.6)
    b = np.roll(a, int(3.1 * SR), axis=1)                     # the same field again, a little further off: a bigger field
    b = filt(b, "low", 2500, 2); b = width(b[::-1], 1.0)      # (its sides swapped)
    c = np.roll(a, int(5.2 * SR), axis=1); c = filt(c, "low", 1200, 2)
    M = a + 0.55 * b + 0.35 * c
    return write("gallop", width(M, 1.1), loop=True, rms_db=-17)

# ---------------------------------------------------------------- the course commentary, across the course
CALM = ("They've gone a good even gallop early on, the leader just in front on the stands side. Tracking him, the "
        "favourite, travelling well, then a group of four in a line. Into the middle of the field it's tightly packed, "
        "and towards the rear, the outsider's being niggled along. They're coming to the halfway mark now, and nothing "
        "has made a move yet. The pace is steady, the leader's ears pricked, still going well. ")
FINISH = ("And now they're racing! Here comes the challenge down the outside! The leader is fighting back! Two of them "
          "locked together! Inside the final furlong! It's going to be close! They're neck and neck! Here they come to "
          "the line! ")

def human(v):
    """Takes the machine out of the made voice a little: its pitch wanders and its pace breathes (a slow, smooth change
    of playback speed), and a second, slightly different take under it blurs the buzz."""
    n = len(v); k = np.arange(n)
    def drift(depth, secs):
        w = signal.sosfiltfilt(sos("low", 1 / secs), rng.standard_normal(n)); return 1 + depth * w / (np.abs(w).max() + 1e-9)
    out = 0
    for depth, gain in ((0.045, 1.0), (0.03, 0.45)):
        pos = np.cumsum(drift(depth, 0.35)); pos = pos / pos[-1] * (n - 1)
        out = out + gain * np.interp(pos, k, v)
    return out
def speakers(v):
    """A voice through the course's loudspeakers, heard from across the course."""
    v = human(v)
    v = filt(v, "high", 380, 3); v = filt(v, "low", 3600, 3)
    v = peak(v, 1700, 6, 1.2); v = peak(v, 2600, 4, 2.0)                 # a horn speaker's honk
    v = np.tanh(v / (np.abs(v).max() + 1e-9) * 2.4) / np.tanh(2.4)          # driven a little hard
    n = len(v) + int(1.4 * SR); out = np.zeros((2, n))
    # the speakers along the stand: each further one later, quieter and duller, and from its own side
    for dly, g, lp, pan in ((0.0, 1.0, 3600, 0.15), (0.075, 0.6, 3000, -0.35), (0.17, 0.48, 2600, 0.5), (0.29, 0.36, 2200, -0.6),
                            (0.44, 0.26, 1800, 0.7), (0.63, 0.16, 1500, -0.75), (0.86, 0.09, 1300, 0.2)):
        s = signal.sosfilt(sos("low", lp, 2), v) * g; i = int(dly * SR)
        a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        out[0, i:i + len(s)] += s * a[0] * 1.41; out[1, i:i + len(s)] += s * a[1] * 1.41
    out = tail(out, 2.4, 0.95, 2400)
    return filt(out, "low", 2500, 2)
def make_pa():
    from make_race_sounds import speak
    for name, text, src, rate, pitch, rngp, L in (("pa-race", CALM, "commentary.mp3", 178, 46, 62, None),
                                                  ("pa-finish", FINISH, "commentary-finish.mp3", 228, 66, 95, None)):
        if (SRC / src).exists():                              # a real commentary, if there is one
            v = load(src).mean(0)
        else:
            # one commentator: the same voice throughout, phrase by phrase so each has its own lift, with a breath between
            parts = [p.strip() for p in text.replace("!", "!|").replace(".", ".|").split("|") if p.strip()]
            bits = []
            for p in parts:
                bits.append(speak(p, "m3", rate * rng.uniform(0.96, 1.05), pitch + rng.integers(-4, 6), rngp))
                bits.append(np.zeros(int(rng.uniform(0.18, 0.4) * SR)))
            v = np.concatenate(bits)
        x = speakers(v)
        L = x.shape[1] / SR - 1.6
        x = loop_of(x, L, 1.4)
        write(name, x, loop=True, rms_db=-20)

if __name__ == "__main__":
    which = sys.argv[1:] or ["off", "murmur", "excited", "roar", "line", "gallop", "pa"]
    for w in which:
        {"off": make_off, "murmur": make_murmur, "excited": make_excited, "roar": make_roar,
         "line": make_line, "gallop": make_gallop, "pa": make_pa}[w]()
    # each loop's exact length into sounds.json (by file name), so the race view loops it at exactly the join
    import json
    cfg_p = OUT / "sounds.json"; cfg = json.loads(cfg_p.read_text())
    for f in cfg["files"].values():
        stem = f["file"].rsplit(".", 1)[0]
        if stem in LOOPS: f["loop"] = LOOPS[stem]
    cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print("loops:", LOOPS)
