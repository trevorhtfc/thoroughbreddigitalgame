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
  middle.mp3         from after the off to about 3f out (loop): the crowd a little muted, the field galloping, the
                     course commentator in the background (owner, 13 Nov)
  finish.mp3         from about 3f out: the crowd and the commentator more and more animated, the line FINISH_LINE_AT
                     seconds in with the crowd's surge, then cheering ebbing into applause (owner, 13 Nov)
  crowd-murmur.mp3   the crowd waiting, before the off and after the race (loop): the real crowds, softened and distant
  crowd-excited.mp3  Aintree (loop): a long race passing the stands
  gallop.mp3         the field galloping (loop), for close shots and the slow-motion replay

The commentary voice is eSpeak (the only speaking voice that runs here) put through the course's loudspeakers: a
horn speaker's narrow band, a little overdrive, the echo of speakers further along the stand and the open air, low
under the crowd, so the rise and fall of a commentator comes through but not the words. A real commentary recording
can take its place (ask Claude: it would be cut into the middle and the finish).

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

# ---------------------------------------------------------------- the course commentary, across the course
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
def say(text, rate, pitch, rng_p, gap=(0.18, 0.4)):
    """The commentator (made voice, eSpeak), phrase by phrase so each has its own lift, a breath between: dry, mono."""
    from make_race_sounds import speak
    parts = [p.strip() for p in text.replace("!", "!|").replace(".", ".|").replace("?", "?|").split("|") if p.strip()]
    bits = []
    for p in parts:
        bits.append(speak(p, "m3", rate * rng.uniform(0.96, 1.05), pitch + rng.integers(-3, 5), rng_p))
        bits.append(np.zeros(int(rng.uniform(*gap) * SR)))
    return np.concatenate(bits[:-1])

# Generic calls: no names, no numbers, so they fit any race (and the words are barely caught from across the course)
MIDDLE_CALL = ("They're away and racing, and it's the leader who's quickly into his stride. Tracking him, the favourite, "
    "travelling sweetly. Then a group of four in a line across the track. Into the middle of the field it's tightly "
    "packed, nobody wanting to give an inch. Towards the rear, the outsider is being niggled along. They've gone a good "
    "even gallop. The leader's ears are pricked, he's enjoying himself out in front. The favourite is still on the bridle "
    "and waiting for a gap. Behind them the field is starting to string out. They're racing towards halfway, and "
    "nothing has made a serious move yet. ")
FINISH_CALLS = [   # (text, rate, pitch, pitch range, level dB): one continuous call, calm into excited, back to back
    ("Three furlongs out, and they're starting to quicken. The leader's being asked a question now. The favourite is "
     "beginning to close, and the rest are being pushed along.", 192, 52, 70, -28),
    ("Two furlongs to run! They're fanning out across the track! Here comes the challenge down the outside! The leader "
     "is fighting back! The favourite is in full flight!", 212, 60, 85, -25.5),
    ("Approaching the final furlong! It's the leader and the favourite, and here comes the one on the outside as well! "
     "Three of them in a line! Inside the final furlong! Two of them locked together! It's going to be desperately "
     "close! They're stride for stride!", 232, 70, 99, -23),
    ("Here they come! Nothing between them! It's all to play for! A furious finish! They're racing all the way to the "
     "line!", 244, 76, 99, -21.5),
]
LAST_CALL = ("Neck and neck to the line!", 248, 80, 99, -20.5)

# ---------------------------------------------------------------- the middle: from after the off to about 3 furlongs out (a loop)
MIDDLE = {"crowd": -25.0, "lift": -31.0, "gallop": -24.5, "pa": -27.5}   # each part's level (dB), here and at the start of the finish
def make_middle():
    """Owner, 13 Nov: "a flexible looping middle section that can handle the off all the way till the 3f stage or so..
    a slightly more muted crowd, galloping and background PA announcer". One loop, as long as the commentary."""
    pa = speakers(say(MIDDLE_CALL, 182, 48, 64))
    L = pa.shape[1] / SR - 1.2                                # the commentary's breath at the end overlaps its start
    n = int((L + 2.0) * SR)
    crowd = level(tile(murmur_loop(), n, 4.0), MIDDLE["crowd"])
    lift = level(filt(tile(excited_loop(), n, 9.0), "low", 1800, 2), MIDDLE["lift"])      # a little life in it
    hooves = level(tile(gallop_loop(), n), MIDDLE["gallop"])
    M = crowd + lift + hooves
    place(M, level(pa, MIDDLE["pa"]), 0.3)
    return write("middle", loop_of(M, L, 2.0), loop=True)

# ---------------------------------------------------------------- the finish: from about 3 furlongs out to the line and after
FINISH_LINE_AT = 37.0                                         # the line, this far into finish.mp3 (sounds.json: finish.lineAt)
def make_finish():
    """Owner, 13 Nov: "the finish sound effect where the crowd get much more animated as does the background PA leading
    to the cheer as they cross the line". Begins as the middle does (the race view crossfades into it about 3f out),
    the crowd stirring then roaring, the commentator rising through three calls to his last at the line, the gallop
    coming closer, the crowd's surge as they cross, then it ebbs into applause."""
    FL = FINISH_LINE_AT; total = FL + 14.0; n = int(total * SR); t = np.arange(n) / SR
    env = lambda pts: np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    db = lambda pts: 10 ** (env(pts) / 20)
    crowd = level(tile(murmur_loop(), n, 11.0), MIDDLE["crowd"]) * db([(0, 0), (8, 0), (18, -4), (26, -12), (FL, -30), (total, -40)])[None]
    stir = level(tile(excited_loop(), n, 3.0), -18) * db([(0, MIDDLE["lift"] + 18), (6, -12), (16, -5), (24, -1), (30, -2), (FL - 1, -4), (FL + 3, -14), (FL + 9, -30), (total, -40)])[None]
    stir[:, t < 8] = filt(stir, "low", 1800, 2)[:, t < 8]     # (as muffled as the middle's to begin with)
    roar = level(tile(roar_loop(), n, 5.0), -16.5) * db([(0, -40), (16, -30), (24, -12), (30, -5), (34, -1.5), (FL, 0), (FL + 2, -3), (FL + 7, -14), (FL + 12, -30), (total, -40)])[None]
    hooves = level(tile(gallop_loop(), n, 2.5), MIDDLE["gallop"]) * db([(0, 0), (20, 2), (30, 5), (FL - 2, 6), (FL + 1, 3), (FL + 5, -12), (FL + 8, -40), (total, -60)])[None]
    M = crowd + stir + roar + hooves
    # the surge as they cross: the Japan Cup crowd's last swell, its peak (about 2 s into this cut) just after the line
    surge = fade(crowd_eq(cut(japan, 36.2, 40.6)), 0.6, 0.8); place(M, level(width(surge, 1.25), -14.5), FL - 1.6)
    after = fade(crowd_eq(cut(gn, 18.0, 30.0)), 0.6, 8.0); place(M, level(after, -20.5), FL + 2.4)          # cheering on, ebbing
    claps = applause(n, FL + 1.4); place(M, level(claps[:, int((FL + 1.4) * SR):], -22.5), FL + 1.4)
    # the commentator: three calls rising, the last ending as they cross the line
    lt, lr, lp, lrng, ldb = LAST_CALL
    last = say(lt, lr, lp, lrng); at_last = FL - len(last) / SR - 0.05
    at = 1.5
    for text, rate, pitch, rngp, pdb in FINISH_CALLS:           # back to back, a short breath between
        room = int((at_last - 0.3 - at) * SR)
        if room < int(0.8 * SR): break
        v = say(text, rate, pitch, rngp)
        if len(v) > room: v = v[:room] * np.r_[np.ones(room - int(0.25 * SR)), np.linspace(1, 0, int(0.25 * SR))]
        if text is FINISH_CALLS[-1][0]: at = at_last - 0.3 - len(v) / SR   # (the last of them runs straight into the final call)
        place(M, level(speakers(v), pdb), at)
        at += len(v) / SR + 0.35
    place(M, level(speakers(last), ldb), at_last)
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
