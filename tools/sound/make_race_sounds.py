"""(12 Nov 2026; since 13 Nov the race view's files come from tools/sound/mix_real_sounds.py and the owner's recordings.
This script is kept for its made voices and hand claps, which that one borrows. Running it on its own still writes the
old made-up files, over the real ones: don't, unless going back.)

The race view's sounds: the crowd (murmur, excited, roar, applause), the field galloping, the stalls opening.

Everything is made here from scratch (no recordings, so nothing to license): the crowd's chatter and shouts are the
eSpeak NG speaking voice, dozens to hundreds of voices at a time at different pitches, speeds and distances, so no
single voice is heard; the roar is "aah"/"ooh" voices built from vowel shapes; the applause is hundreds of hand claps;
the hooves are four-beat gallops with the horses' breathing. Any of the files can later be swapped for a real
recording of the same kind (same name, same length for the loops): see race-view/assets/sound/sounds.json.

Loops are written with half a second of the loop before and after it, so the race view can loop them from 0.25 s in
without a click, whatever the browser does with the start of an MP3 file.

    pip install --break-system-packages espeakng-loader      (once)
    python3 tools/sound/make_race_sounds.py                   (writes race-view/assets/sound/*.mp3)
"""
import ctypes, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
OUT = Path(__file__).resolve().parents[2] / "race-view" / "assets" / "sound"
rng = np.random.default_rng(1851)          # the same sounds every time the script runs

# ---------------------------------------------------------------- the speaking voice (eSpeak NG, bundled by the pip package)
import espeakng_loader as E
_lib = ctypes.CDLL(E.get_library_path())
_CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
VSR = _lib.espeak_Initialize(2, 0, E.get_data_path().encode(), 0)
_buf = []
def _cb(wav, n, ev):
    if n > 0: _buf.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
    return 0
_cbref = _CB(_cb); _lib.espeak_SetSynthCallback(_cbref)

VOICES = ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "f1", "f2", "f3", "f4", "f5", "Andy", "Annie", "david", "edward",
          "grandpa", "aunty", "belinda", "ian", "john", "adam", "benjamin", "michael", "Mike", "Alex", "Gene", "Lee"]
FEMALE = {"f1", "f2", "f3", "f4", "f5", "Annie", "aunty", "belinda"}

def speak(text, voice, rate, pitch, rng_=50):
    _buf.clear()
    _lib.espeak_SetVoiceByName(f"en-gb+{voice}".encode())
    for p, v in ((1, rate), (3, pitch), (4, rng_)): _lib.espeak_SetParameter(p, int(v), 0)
    b = text.encode(); _lib.espeak_Synth(b, len(b) + 1, 0, 1, 0, 0, None, None); _lib.espeak_Synchronize()
    if not _buf: return np.zeros(1)
    x = np.concatenate(_buf).astype(np.float64) / 32768.0
    x = signal.resample_poly(x, SR, VSR)
    nz = np.flatnonzero(np.abs(x) > 1e-3)                  # trim the silence either side
    return x[nz[0]:nz[-1] + 1] if len(nz) else x

# ---------------------------------------------------------------- helpers
def sos(kind, f, q=None, order=2):
    if kind == "band":
        lo, hi = f / (1 + 0.5 / q), f * (1 + 0.5 / q)
        return signal.butter(order, [lo, min(hi, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
    return signal.butter(order, min(f, SR / 2 - 100), kind, fs=SR, output="sos")
def filt(x, kind, f, q=None, order=2): return signal.sosfilt(sos(kind, f, q, order), x)

def pink(n):
    w = rng.standard_normal(n); X = np.fft.rfft(w); k = np.arange(len(X)); k[0] = 1
    return np.fft.irfft(X / np.sqrt(k), n) * 30

class Track:
    """A stereo buffer. Loops wrap what runs past the end round to the start, so they join up exactly."""
    def __init__(self, seconds, loop):
        self.n = int(seconds * SR); self.loop = loop; self.x = np.zeros((2, self.n + (0 if loop else SR * 4)))
    def put(self, src, t, gain=1.0, pan=0.0):
        i = int(t * SR); a = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        for c in (0, 1):
            s = src * gain * a[c] * 1.4142
            if self.loop:
                k, p = 0, i % self.n
                while k < len(s):
                    j = min(len(s) - k, self.n - p); self.x[c, p:p + j] += s[k:k + j]; k += j; p = 0
            else:
                j = min(len(s), self.x.shape[1] - i)
                if j > 0: self.x[c, i:i + j] += s[:j]
    def reverb(self, seconds, wet, tone=4000, pre=0.012):
        """Open air in front of a stand: a short, soft tail. Loops are reverberated round the join too."""
        m = int(seconds * SR); t = np.arange(m) / SR
        out = np.zeros_like(self.x)
        for c in (0, 1):
            ir = rng.standard_normal(m) * np.exp(-t * 6.9 / seconds); ir = filt(ir, "low", tone)
            ir[: int(pre * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
            if self.loop:
                L = self.n; irw = np.zeros(L); np.add.at(irw, np.arange(m) % L, ir)
                out[c] = np.fft.irfft(np.fft.rfft(self.x[c]) * np.fft.rfft(irw), L)
            else:
                out[c] = signal.fftconvolve(self.x[c], ir)[: self.x.shape[1]]
        self.x = self.x + wet * out
    def norm(self, rms_db=-18.0, peak=0.89):
        r = np.sqrt((self.x ** 2).mean()); self.x *= 10 ** (rms_db / 20) / max(r, 1e-9)
        p = np.abs(self.x).max()
        if p > peak * 0.7: self.x = peak * np.tanh(self.x / peak)               # a soft limit, never a hard clip
    def write(self, name, seconds_out=None):
        if self.loop:   # half a second of the loop either side of it
            h = SR // 2; x = np.concatenate([self.x[:, -h:], self.x, self.x[:, :h]], axis=1)
        else:
            x = self.x[:, : int((seconds_out or self.x.shape[1] / SR) * SR)]
            f = int(0.05 * SR); x[:, -f:] *= np.linspace(1, 0, f)
        with tempfile.TemporaryDirectory() as d:
            w = Path(d) / "a.wav"; wavfile.write(w, SR, (np.clip(x.T, -0.98, 0.98) * 32767).astype(np.int16))
            OUT.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-c:a", "libmp3lame", "-b:a", "112k", str(OUT / f"{name}.mp3")], check=True)
        print(f"{name}.mp3  {x.shape[1] / SR:.1f} s  {(OUT / f'{name}.mp3').stat().st_size // 1024} KB")

def distance(x, d):
    """A voice d metres away: quieter, duller, and closer voices a little clearer."""
    return filt(x, "low", float(np.clip(9000 - d * 85, 1100, 9000)), order=2) * (6.0 / max(d, 6.0))

# what people say (chatter) and shout (the finish)
CHAT = ["Lovely day for it, isn't it?", "Have you got anything for the next race?", "I fancy the grey, he looked well in the paddock.",
        "Shall we get another glass?", "My tip was a non runner.", "Where are the others?", "He's drawn badly, I think.",
        "The going's quicker than they said.", "Did you see the hats over there?", "I've had a fiver each way.",
        "We should go down to the rail.", "What price is the favourite now?", "Oh look, they're going down to the start.",
        "I think it'll stay dry.", "She won here last year, you know.", "Is that the one in the pink and green?",
        "I can't see a thing from here.", "Right, who's getting the drinks?", "Lovely horse, lovely horse.",
        "It's a big field, isn't it?", "I've no idea, I just liked the name.", "They say the trainer's in form.",
        "We'll meet you by the bandstand.", "Have you seen the queue for the loos?", "Twenty to one, that's a good price.",
        "Look at him, he's sweating up.", "I backed the outsider.", "Honestly, it's always the one I don't pick."]
SHOUT = ["Come on!", "Go on!", "Go on, my son!", "Come on, come on!", "Get up!", "Yes!", "Kick on!", "Go on then!",
         "Push him out!", "Come on, son!", "Keep going!", "Go on, go on!", "Come on, my beauty!", "Get there!", "Hold on!"]

def chatter(track, n, dmin, dmax, loud=1.0):
    L = track.n / SR
    for _ in range(n):
        v = VOICES[rng.integers(len(VOICES))]; fem = v in FEMALE
        x = speak(CHAT[rng.integers(len(CHAT))], v, rng.integers(135, 205), rng.integers(30, 70) + (10 if fem else 0), rng.integers(30, 70))
        d = dmin + (dmax - dmin) * rng.random() ** 0.7
        track.put(distance(x, d) * loud * rng.uniform(0.6, 1.0), rng.random() * L, 1.0, rng.uniform(-0.9, 0.9))

def shouts(track, n, dmin, dmax, loud=1.0, tmax=None, t0=0.0):
    L = (tmax or track.n / SR) - t0
    for _ in range(n):
        v = VOICES[rng.integers(len(VOICES))]; fem = v in FEMALE
        x = speak(SHOUT[rng.integers(len(SHOUT))], v, rng.integers(190, 290), rng.integers(62, 99), rng.integers(60, 99))
        x = np.tanh(filt(x, "high", 250) * 2.2)                      # vocal effort: brighter, pushed
        x = x + 0.8 * filt(x, "band", 2200, 1.2)
        d = dmin + (dmax - dmin) * rng.random() ** 0.8
        track.put(distance(x, d) * loud * rng.uniform(0.5, 1.0), t0 + rng.random() * L, 1.0, rng.uniform(-0.95, 0.95))

VOWELS = {"a": (800, 1200, 2700), "ah": (700, 1100, 2600), "o": (500, 850, 2500), "oo": (330, 800, 2300), "e": (550, 1750, 2500), "ay": (450, 2000, 2650)}
def aah(dur, f0, vowel, rise=1.15, effort=1.0):
    """One voice holding a shout: a buzzing voice through the shape of a vowel, rising with excitement."""
    n = int(dur * SR); t = np.arange(n) / SR
    contour = 1 + (rise - 1) * np.sin(np.pi * np.minimum(t / dur * 1.3, 1)) + 0.012 * np.sin(2 * np.pi * rng.uniform(4.5, 6.5) * t)
    contour *= 1 + 0.004 * np.cumsum(rng.standard_normal(n)) / np.sqrt(SR)          # a little wander
    ph = np.cumsum(f0 * contour / SR) % 1.0
    src = (2 * ph - 1) ** 3 * 0.6 + (2 * ph - 1) * 0.4                                # a buzz, softer than a sawtooth
    src = src + 0.25 * effort * rng.standard_normal(n) * (0.5 + 0.5 * (ph < 0.4))      # breath, pulsed with the voice
    f1, f2, f3 = (f * rng.uniform(0.9, 1.1) * (1.06 if f0 > 200 else 1) for f in VOWELS[vowel])
    y = filt(src, "band", f1, 3) * 1.0 + filt(src, "band", f2, 4) * 0.55 + filt(src, "band", f3, 5) * 0.3 * effort
    a = min(0.12 + rng.random() * 0.15, dur * 0.3); r = min(0.25 + rng.random() * 0.4, dur * 0.5)
    env = np.minimum(1, np.minimum(t / a, (dur - t) / r)) ** 1.5
    return np.tanh(y * env * 3) / 3

def roar_voices(track, n, dmin, dmax, loud=1.0, durs=(1.0, 3.5), t0=0.0, tmax=None, rise=(1.05, 1.3)):
    L = (tmax or track.n / SR) - t0
    for _ in range(n):
        fem = rng.random() < 0.38
        f0 = rng.uniform(210, 400) if fem else rng.uniform(115, 230)
        x = aah(rng.uniform(*durs), f0, ["a", "ah", "o", "oo", "e", "ay"][rng.integers(6)], rng.uniform(*rise))
        d = dmin + (dmax - dmin) * rng.random() ** 0.8
        track.put(distance(x, d) * loud * rng.uniform(0.5, 1.0), t0 + rng.random() * L, 1.0, rng.uniform(-0.95, 0.95))

def wash(track, level, centre=900, width=1.0, mod=0.0):
    """The sound of a big crowd as a whole: shaped noise, slowly breathing."""
    for c in (0, 1):
        w = filt(pink(track.n), "band", centre, width, order=1)
        if mod:
            t = np.arange(track.n) / SR; L = track.n / SR
            w *= 1 + mod * np.sin(2 * np.pi * (rng.integers(2, 5) / L) * t + rng.random() * 6)
        w *= level / np.sqrt((w ** 2).mean())
        track.x[c, :track.n] += w

# ---------------------------------------------------------------- the crowd before and between: chatter (24 s loop)
def crowd_murmur():
    T = Track(24, True)
    chatter(T, 260, 14, 90)                 # the crowd beyond: indistinct
    chatter(T, 26, 7, 14, 0.45)             # a few nearer, still not quite caught
    wash(T, 0.012, 600, 1.2, 0.3)
    T.reverb(1.1, 0.35, 3500)
    T.norm(-19); T.write("crowd-murmur")

# ---------------------------------------------------------------- the crowd stirring: chatter rising into shouts (20 s loop)
def crowd_excited():
    T = Track(20, True)
    chatter(T, 160, 12, 80, 1.1)
    shouts(T, 320, 8, 70)
    roar_voices(T, 120, 15, 90, 0.5, (0.8, 2.2), rise=(1.02, 1.15))
    wash(T, 0.02, 800, 1.0, 0.25)
    T.reverb(1.2, 0.4, 4000)
    T.norm(-18); T.write("crowd-excited")

# ---------------------------------------------------------------- the crowd roaring them home (16 s loop)
def crowd_roar():
    T = Track(16, True)
    roar_voices(T, 700, 10, 110, 1.0, (1.2, 4.0))
    shouts(T, 380, 8, 60, 1.2)
    wash(T, 0.035, 1000, 0.9, 0.15)
    T.reverb(1.4, 0.45, 4500)
    T.norm(-17); T.write("crowd-roar")

# ---------------------------------------------------------------- the applause and cheers after the line (one go, 14 s)
def clap_kit(k=40):
    kit = []
    for _ in range(k):
        n = int(0.05 * SR); t = np.arange(n) / SR
        x = rng.standard_normal(n) * np.exp(-t / rng.uniform(0.004, 0.011))
        y = filt(x, "band", rng.uniform(900, 2600), rng.uniform(1.2, 3)) + 0.5 * filt(x, "band", rng.uniform(350, 650), 1.5) + 0.15 * filt(x, "high", 3000)
        kit.append(y / np.abs(y).max())
    return kit
def applause():
    T = Track(14, False); kit = clap_kit()
    for _ in range(230):                    # each pair of hands: its own speed, its own start and stop
        rate = rng.uniform(3.4, 6.5); start = rng.uniform(0, 0.9) ** 1.6
        stop = 5.0 + rng.gamma(2.2, 1.6); d = rng.uniform(5, 70) * rng.uniform(0.6, 1)
        g = 6.0 / max(d, 6) * rng.uniform(0.5, 1); pan = rng.uniform(-0.95, 0.95); c = kit[rng.integers(len(kit))]
        tt = start
        while tt < min(stop, 13.5):
            fade = np.clip((stop - tt) / 1.5, 0, 1)
            T.put(c * fade * rng.uniform(0.7, 1), tt, g, pan)
            tt += 1 / rate * rng.uniform(0.92, 1.08)
            if tt > stop - 2 and rng.random() < 0.1: tt += rng.uniform(0.2, 0.8)     # tailing off unevenly
    roar_voices(T, 160, 10, 80, 0.55, (0.6, 1.8), t0=0.0, tmax=4.5, rise=(1.1, 1.4))   # the cheer as they cross
    shouts(T, 70, 8, 50, 0.7, tmax=5.5)
    for _ in range(5):                      # finger whistles
        n = int(rng.uniform(0.5, 1.2) * SR); t = np.arange(n) / SR; f = rng.uniform(2400, 3400)
        fr = f * (1 + 0.12 * np.sin(np.pi * t / t[-1])) * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))
        w = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.minimum(1, np.minimum(t / 0.04, (t[-1] - t) / 0.08))
        w += 0.05 * filt(rng.standard_normal(n), "band", f, 4)
        T.put(w * 0.12, rng.uniform(0.6, 5.5), rng.uniform(0.3, 0.8), rng.uniform(-0.8, 0.8))
    T.reverb(1.3, 0.4, 5000)
    T.norm(-17); T.write("applause", 14)

# ---------------------------------------------------------------- the field galloping (8 s loop)
def hoof(v=1.0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = rng.uniform(65, 105) * np.exp(-t * 9) + 40
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / rng.uniform(0.03, 0.05))
    turf = filt(rng.standard_normal(n), "band", rng.uniform(350, 900), 1.2) * np.exp(-t / 0.018) * 0.45
    clod = filt(rng.standard_normal(n), "band", rng.uniform(1500, 3200), 1.5) * np.exp(-np.maximum(t - 0.01, 0) / 0.03) * (t > 0.01) * 0.08
    return (thud + turf + clod) * v
def gallop():
    T = Track(8, True)
    for h in range(14):
        strides = int(rng.integers(17, 21)); P = 8 / strides; t0 = rng.random() * P
        v = rng.uniform(0.5, 1.0); pan = rng.uniform(-0.7, 0.7); k = P / 0.43
        for s in range(strides):
            base = t0 + s * P + rng.normal(0, 0.004)
            for j, off in enumerate((0.0, 0.07, 0.155, 0.215)):
                T.put(hoof(v * (0.8 if j < 2 else 1.0) * rng.uniform(0.85, 1.1)), base + off * k + rng.normal(0, 0.003), 1.0, pan)
            # the breath: out as the forelegs land, every stride
            n = int(0.2 * SR); tt = np.arange(n) / SR
            br = filt(rng.standard_normal(n), "band", rng.uniform(300, 700), 0.9) * np.sin(np.pi * np.minimum(tt / 0.16, 1)) ** 2
            T.put(br * 0.28 * v, base + 0.2 * k, 1.0, pan)
    for c in (0, 1):                        # the ground under them
        r = filt(pink(T.n), "low", 110, order=2); T.x[c, :T.n] += r * 0.02 / np.sqrt((r ** 2).mean())
    T.reverb(0.6, 0.2, 2500)
    T.norm(-17); T.write("gallop")

# ---------------------------------------------------------------- the stalls opening (one go)
def stalls():
    T = Track(3, False)
    for g in range(16):
        t = g * rng.uniform(0.002, 0.006) + rng.uniform(0, 0.01); pan = -0.8 + 1.6 * g / 15
        n = int(1.2 * SR); tt = np.arange(n) / SR
        bang = filt(rng.standard_normal(n), "high", 900) * np.exp(-tt / 0.004) * 0.7
        ring = sum(np.sin(2 * np.pi * f * rng.uniform(0.93, 1.07) * tt + rng.random() * 6) * np.exp(-tt / d) * a
                   for f, d, a in ((190, 0.35, 0.5), (430, 0.3, 0.45), (760, 0.22, 0.35), (1180, 0.18, 0.3), (1710, 0.12, 0.22), (2440, 0.08, 0.15), (3350, 0.05, 0.1)))
        rattle = filt(rng.standard_normal(n), "band", 2800, 2) * np.exp(-tt / 0.06) * (1 + np.sin(2 * np.pi * 38 * tt)) * 0.15
        T.put((bang + ring * 0.35 + rattle) * np.minimum(1, (tt[-1] - tt) / 0.4) * rng.uniform(0.6, 1), t, 1.0, pan)
        T.put(filt(rng.standard_normal(int(0.15 * SR)), "low", 140) * np.exp(-np.arange(int(0.15 * SR)) / SR / 0.05) * 0.6, t, 1.0, pan)   # the thump of the frame
    T.reverb(0.9, 0.3, 5000)
    T.norm(-21); T.write("stalls", 2.5)

if __name__ == "__main__":
    which = sys.argv[1:] or ["murmur", "excited", "roar", "applause", "gallop", "stalls"]
    for w in which:
        {"murmur": crowd_murmur, "excited": crowd_excited, "roar": crowd_roar, "applause": applause, "gallop": gallop, "stalls": stalls}[w]()
