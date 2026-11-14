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
                     Aintree before its finish builds) and the Japan Cup crowd early on, muted, the field galloping
  finish.mp3         from about 3f out: three real finishes (the Grand National with its commentary, Aintree, the Japan
                     Cup) laid so their own lines land on ours, FINISH_LINE_AT seconds in; then applause (owner, 13-14 Nov)
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
    """Hand claps (made: there's no applause in the recordings), starting 'start' seconds in and tailing off. Owner,
    14 Nov: "the applause is too prominent, it doesn't sound like a big crowd". So it's a big crowd now: some 1,400
    pairs of hands, nearly all of them far off down the stands (duller and later the further), so it reads as a wash."""
    from make_race_sounds import clap_kit
    kit = clap_kit(); out = np.zeros((2, n))
    for count, d0, d1, lp in ((120, 20, 50, 7000), (420, 50, 120, 4000), (860, 120, 260, 2200)):
        claps = np.zeros((2, n))
        for _ in range(count):
            rate = rng.uniform(3.4, 6.5); st = start + rng.uniform(0, 2.5) ** 1.3; stop = st + 3 + rng.gamma(2.2, 1.8)
            d = rng.uniform(d0, d1); g = 25.0 / d * rng.uniform(0.5, 1); pan = rng.uniform(-1, 1); c = kit[rng.integers(len(kit))]
            a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); tt = st + d / 343      # (sound takes its time)
            while tt < min(stop, n / SR - 0.5):
                i = int(tt * SR); j = min(len(c), n - i); f = np.clip((stop - tt) / 1.5, 0, 1) * rng.uniform(0.7, 1) * g
                claps[0, i:i + j] += c[:j] * f * a[0]; claps[1, i:i + j] += c[:j] * f * a[1]
                tt += 1 / rate * rng.uniform(0.92, 1.08)
        out += filt(claps, "low", lp, 2)
    return tail(out, 2.0, 0.6, 4000)[:, :n]

# ---------------------------------------------------------------- the middle: from after the off to about 3 furlongs out (a loop)
# Owner, 13 Nov: "the commentary isn't great [the made voice]. Some of these clips have crowd and commentary which I'm
# happy for you to overlay to get the sound." So the commentary is now the real commentators, with their crowds.
MIDDLE = {"murmur": -31.0, "stir": -31.5, "gallop": -32.0, "pa": -22.5}   # (owner, 14 Nov: "PA up")   # (owner, 14 Nov: "I can't really hear any PA announcer": the talk up, the rest down)
TALK_LIFT_DB = 11.0                                           # the commentators brought forward out of their crowds this much   # each part's level (dB), here and at the start of the finish
MIDDLE_TALK = [            # (clip, from, to, voice from, voice to): the crowd with its commentator, laid end to end
    ("chel", 8.3, 12.4, 8.5, 12.4),                         # Cheltenham: the commentator after the roar (its roar's tail left out)
    ("aintree", 0.2, 11.5, 0.2, 8.0),                       # Aintree: its announcer over the crowd, before its finish builds
    ("japan", 4.0, 14.0, 4.0, 4.0),                         # the Japan Cup crowd early in its race (no commentary): a breather
]
# Where each crowd's horses cross the line (owner, 14 Nov: "What a finish 22 secs, aintree crowd 21, japan cup 38"):
# in the finish all three are laid so their lines land on ours, so their own build-ups make the crescendo.
LINES = {"gn": 22.0, "aintree": 21.0, "japan": 38.0}
def even(x, win=1.5, range_db=6.0):
    """Rides the level of a stretch so it stays steady (like an engineer's hand on the fader), within range_db."""
    e = np.sqrt(signal.sosfiltfilt(sos("low", 1 / win, 1), (x ** 2).mean(0)).clip(1e-12))
    g = np.clip(np.sqrt((x ** 2).mean()) / e, 10 ** (-range_db / 20), 10 ** (range_db / 20))
    return x * g[None, :]
def match_tone(parts):
    """Gives a set of crowd pieces one tone (owner, 14 Nov: "a weird step … it needs blending"): each piece's long-run
    spectrum is nudged, within 6 dB and smoothly across frequency, towards the pieces' average."""
    f = np.fft.rfftfreq(8192, 1 / SR)
    specs = [signal.welch(x.mean(0), SR, nperseg=8192)[1] + 1e-14 for x in parts]
    target = np.exp(np.mean([np.log(p) for p in specs], axis=0))
    out = []
    for x, p in zip(parts, specs):
        g = 0.5 * np.log10(target / p) * 10                    # dB to apply, then smoothed over about a third of an octave
        lf = np.log2(np.maximum(f, 20)); sm = np.array([g[np.abs(lf - l) < 1 / 6].mean() for l in lf])
        sm = np.clip(sm, -6, 6); n = x.shape[1]; F = np.fft.rfftfreq(n, 1 / SR)
        G = 10 ** (np.interp(F, f, sm) / 20)
        out.append(np.fft.irfft(np.fft.rfft(x, axis=1) * G[None, :], n, axis=1))
    return out
def talk_bed(parts, xf=2.5):
    """The clips laid end to end with long crossfades, each with its commentator brought forward, matched in tone, all
    at one level."""
    clips = {"chel": chel, "aintree": aintree, "gn": gn, "japan": japan}
    xs = []
    for name, a, b, v0, v1 in parts:
        x = crowd_eq(cut(clips[name], a, b)); x = lift_voice(x, v0 - a, v1 - a, TALK_LIFT_DB, 0.3, 0.5); xs.append(level(x, -20))
    xs = [level(x, -20) for x in match_tone(xs)]
    out = xs[0]; k = int(xf * SR); r = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    for x in xs[1:]:
        out = np.concatenate([out[:, :-k], out[:, -k:] * np.sqrt(1 - r) + x[:, :k] * np.sqrt(r), x[:, k:]], axis=1)
    return even(out)

# ---------------------------------------------------------------- the commentator over the loudspeakers (owner, 14 Nov: "PA up")
PA_TALK = [("chel", 8.45, 12.4), ("aintree", 0.2, 4.1), ("aintree", 4.1, 8.0)]   # the clearest commentary in the clips
def isolate(x):
    """The commentator lifted out of his crowd: what stands above the crowd's smooth wash (a voice's harmonics) kept,
    the wash turned well down."""
    f, tt, Z = signal.stft(x, SR, nperseg=4096, noverlap=4096 - 512)
    mag = np.abs(Z) + 1e-12
    k = 15; smooth = np.exp(signal.convolve(np.log(mag), np.ones((1, 2 * k + 1, 1)) / (2 * k + 1), mode="same"))
    G = np.clip((mag / smooth) ** 2.2 * 0.5, 0.12, 2.5) * (((f > 160) & (f < 4200))[None, :, None] * 0.9 + 0.1)
    _, y = signal.istft(Z * G, SR, nperseg=4096, noverlap=4096 - 512)
    return y[:, :x.shape[1]]
def pa_snippets():
    clips = {"chel": chel, "aintree": aintree}
    return [level(fade(isolate(crowd_eq(cut(clips[c], a, b))), 0.08, 0.25).mean(0), -20) for c, a, b in PA_TALK]
def tannoy(v):
    """A voice through the course's loudspeakers: a horn speaker's band and honk, a little drive, the speakers further
    along the stand echoing it, the open air."""
    v = filt(v, "high", 300, 3); v = filt(v, "low", 4000, 3); v = peak(v, 1700, 5, 1.2)
    v = np.tanh(v / (np.abs(v).max() + 1e-9) * 1.8) / np.tanh(1.8)
    n = len(v) + int(0.8 * SR); out = np.zeros((2, n))
    for dly, g, lp, pan in ((0.0, 1.0, 4000, 0.1), (0.09, 0.42, 3000, -0.45), (0.21, 0.28, 2400, 0.55), (0.36, 0.16, 1900, -0.6)):
        sv = signal.sosfilt(sos("low", lp, 2), v) * g; i = int(dly * SR)
        a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        out[0, i:i + len(sv)] += sv * a[0] * 1.41; out[1, i:i + len(sv)] += sv * a[1] * 1.41
    return tail(out, 1.4, 0.45, 3200)
def pa_run(n, t0, t1, rate=lambda t: 1.0, gap=lambda t: 0.45, start=0):
    """The commentary snippets one after another from t0 to t1 seconds (cycling), each sped up by rate(t) (a shade
    faster and higher as it gets exciting), gap(t) between them."""
    snips = pa_snippets(); out = np.zeros((2, n)); at = t0; i = start
    while True:
        v = snips[i % len(snips)]; r = rate(at)
        if r != 1.0: v = np.interp(np.arange(0, len(v) - 1, r), np.arange(len(v)), v)
        if at + len(v) / SR > t1: break
        place(out, tannoy(v), at); at += len(v) / SR + gap(at); i += 1
    return out

def middle_crowd(n, start=0.0):
    """The middle's crowd: the crowd waiting and a muffled Aintree, both long seamless loops (owner, 14 Nov: "a weird
    step … it needs blending": no stitched pieces any more; the talk is the loudspeaker layer above it)."""
    a = level(tile(murmur_loop(), n, 4.0 + start), MIDDLE["murmur"])
    b = level(filt(tile(excited_loop(), n, 9.0 + start), "low", 2200, 2), MIDDLE["stir"])
    return a + b
def make_middle():
    """Owner, 13 Nov: "a flexible looping middle section that can handle the off all the way till the 3f stage or so..
    a slightly more muted crowd, galloping and background PA announcer"; 14 Nov: "turn the PA up … at the start as
    well". One loop as long as the crowd waiting (26 s): the crowd, muted; the gallop; the commentator over the
    loudspeakers on top, his phrases spread evenly through it."""
    L = 25.9; n = int((L + 3.0) * SR)
    M = middle_crowd(n) + level(tile(gallop_loop(), n), MIDDLE["gallop"])
    snips = pa_snippets(); talk = sum(len(v) for v in snips) / SR
    k = 2; gap = (L - k * talk) / (k * len(snips))             # two rounds of the phrases, evenly spaced, round the loop
    pa = np.zeros((2, n)); at = gap / 2
    for j in range(k * len(snips)):
        v = snips[j % len(snips)]; place(pa, tannoy(v), at); at += len(v) / SR + gap
    pa[:, :int(3.0 * SR)] += pa[:, int(L * SR):int((L + 3.0) * SR)]   # (what runs past the loop's end comes round to its start)
    pa[:, int(L * SR):] = pa[:, :n - int(L * SR)]
    M = M + pa * (10 ** (MIDDLE["pa"] / 20) / max(rms(pa[:, :int(L * SR)]), 1e-9))
    return write("middle", loop_of(M, L, 3.0), loop=True)

# ---------------------------------------------------------------- the finish: from about 3 furlongs out to the line and after
FINISH_LINE_AT = 37.0                                         # the line, this far into finish.mp3 (sounds.json: finish.lineAt)
# The finish's build (owner, 14 Nov: "I don't feel the excitement evolving"): the crowd's loudness (dB, its level on its
# own) and brightness (0 muffled and far off, 1 full and close) over the finish, the line at FINISH_LINE_AT. It starts
# where the middle is and climbs slowly, then faster and faster: about 14 dB to the line.
BUILD = [(0, -33), (8, -31), (14, -29), (19, -26.5), (24, -23.5), (28, -20.5), (31, -18), (34, -15), (36.2, -13), (37.4, -11.5),
         (39.5, -13), (43, -17), (47, -23), (51, -30)]
PA_BUILD = [(0, 0), (14, 0), (24, 2.5), (31, 5), (36.8, 7.5), (37.4, -30), (51, -30)]   # the commentator over the middle's level (dB)
BRIGHT = [(0, 0.0), (10, 0.05), (18, 0.25), (25, 0.55), (30, 0.8), (33, 1.0), (51, 1.0)]
def make_finish():
    """Owner, 13 Nov: "the finish sound effect where the crowd get much more animated as does the background PA leading
    to the cheer as they cross the line"; then "overlay [the clips with crowd and commentary] to get the sound"; 14 Nov:
    where each crowd's line is, and "I don't feel the excitement evolving". Begins as the middle does (the middle's
    commentators, carried on); the three real finishes, each laid so its own line lands on ours (the Japan Cup from the
    start, the Grand National with its commentary and Aintree from about 20 s out), made into one crowd and then shaped:
    far off and muffled to begin with, coming closer and brighter, climbing slowly then faster and faster to the line
    (BUILD, BRIGHT); the gallop coming up with it; after the line the cheering ebbs into applause."""
    FL = FINISH_LINE_AT; total = FL + 14.0; n = int(total * SR); t = np.arange(n) / SR
    env = lambda pts: np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    db = lambda pts: 10 ** (env(pts) / 20)
    clips = {"gn": gn, "aintree": aintree, "japan": japan}
    def finish_clip(name, lift, fade_in=3.0):
        """The whole clip, its voices brought forward, laid so its line is at FL (anything before 0 cut off)."""
        x = crowd_eq(clips[name]); x = lift_voice(x, 0.0, x.shape[1] / SR, lift, 0.3, 0.5); x = level(x, -20)
        at = FL - LINES[name]
        if at < 0: x = x[:, int(-at * SR):]; at = 0.0
        else: x = fade(x, fade_in, 0)
        X = np.zeros((2, n)); place(X, x, at); return X, at
    J, _ = finish_clip("japan", 3.0)
    G, ga = finish_clip("gn", TALK_LIFT_DB)
    A, aa = finish_clip("aintree", 4.0)
    roar = level(tile(roar_loop(), n, 5.0), -20)              # carries the cheer on as the Japan Cup and Aintree clips end
    # one crowd: the Japan Cup on its own at first, the others joining; each clip ends just after the line
    crowd = (J * db([(0, -2), (ga, -2), (ga + 4, -4), (FL + 2.5, -4), (FL + 2.8, -60), (total, -60)])[None]
             + G * db([(0, 0), (FL + 6, 0), (FL + 12, -6), (total, -12)])[None]
             + A * db([(0, -3), (FL + 2.0, -3), (FL + 2.2, -60), (total, -60)])[None]
             + roar * db([(0, -60), (FL - 1, -30), (FL + 2, -2), (FL + 6, -4), (total, -10)])[None])
    crowd = even(crowd, 1.0, 9.0)                             # its own ups and downs taken out: the shape is BUILD's
    b = env(BRIGHT)[None]
    lo1, lo2 = filt(crowd, "low", 1100, 2), filt(crowd, "low", 2600, 2)
    crowd = lo1 * (1 - b) ** 2 + lo2 * 2 * b * (1 - b) + crowd * b ** 2
    crowd = crowd / max(rms(crowd), 1e-9)
    # the gain that gives BUILD's loudness at every moment (measured over half a second, smoothed)
    e = np.sqrt(signal.sosfiltfilt(sos("low", 2.0, 1), (crowd ** 2).mean(0)).clip(1e-12))
    crowd = crowd / e[None] * db(BUILD)[None]
    # the middle's crowd carried on at the start, handing over as the finishes come in
    bed = middle_crowd(n, 7.0) * db([(0, 0), (12, 0), (17, -3), (21, -10), (25, -40), (total, -60)])[None]
    hooves = level(tile(gallop_loop(), n, 2.5), MIDDLE["gallop"]) * db([(0, 0), (16, 1), (24, 4), (30, 7), (FL - 1.5, 9), (FL + 1, 6), (FL + 5, -10), (FL + 8, -40), (total, -60)])[None]
    # the commentator over the loudspeakers all the way to the line: louder, and a shade quicker and higher, as it builds
    pa = pa_run(n, 0.3, FL - 0.2, rate=lambda u: 1.0 + 0.09 * np.clip((u - 12) / (FL - 12), 0, 1),
                gap=lambda u: 0.45 - 0.3 * np.clip((u - 12) / (FL - 12), 0, 1), start=1)
    pa = pa * 10 ** (MIDDLE["pa"] / 20) / max(rms(pa[:, :int(14 * SR)]), 1e-9) * db(PA_BUILD)[None]   # (its start at the middle's level)
    M = crowd + bed + hooves + pa
    claps = applause(n, FL + 1.4); place(M, level(claps[:, int((FL + 1.4) * SR):], -29.5), FL + 1.4)
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
