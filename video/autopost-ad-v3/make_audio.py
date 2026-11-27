"""v3 soundtrack: original 120 BPM bed (C-G-Am-F), effects only for on-screen events, Sarah's voiceover placed from
assets/audio/vo.json, music ducked under the voice. Everything but the voice is synthesized here (numpy).
Writes assets/audio/soundtrack.wav (and music/sfx/voice stems).  Usage: python make_audio.py [gain_db]
"""
import json
import pathlib
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).parent
SR, DUR, BPM = 44100, 18.0, 120
BEAT = 60 / BPM
N = int(SR * DUR)
LEAD = .015                      # effects lead the picture by 10-20 ms
rng = np.random.default_rng(23)
music = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def ta(sec): return np.arange(int(SR * sec)) / SR
def noise(sec): return rng.standard_normal(int(SR * sec))


def place(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    if i < 0: sig, i = sig[-i:], 0
    sig = sig[: N - i] * gain
    buf[i:i + len(sig), 0] += sig * np.cos((pan + 1) * np.pi / 4) * 1.414
    buf[i:i + len(sig), 1] += sig * np.sin((pan + 1) * np.pi / 4) * 1.414


def lowpass(x, c):
    a = np.exp(-2 * np.pi * c / SR); y = np.empty_like(x); acc = 0.0
    for k, v in enumerate(x): acc = (1 - a) * v + a * acc; y[k] = acc
    return y


def highpass(x, c): return x - lowpass(x, c)


def hz(n):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    return 440 * 2 ** ((names[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)


def sweep(f0, f1, sec, curve=1.0):
    t = ta(sec); return np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * (t / sec) ** curve) / SR)


# ---------- instruments ----------
def kick(l=1.0):
    t = ta(.4); return (np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-t * 30)) / SR) * np.exp(-t * 8) + highpass(noise(.4), 2500) * np.exp(-t * 300) * .2) * l
def clap():
    t = ta(.25); e = sum(np.exp(-np.clip(t - o, 0, None) * 60) * (t >= o) for o in (0, .01, .021)); return lowpass(highpass(noise(.25), 900) * e * .55, 6500)
def hat(open_=False):
    t = ta(.18 if open_ else .05); return highpass(noise(len(t) / SR), 7000) * np.exp(-t * (22 if open_ else 95)) * .3
def tick(l=1.0, f=2600):
    t = ta(.04); return (np.sin(2 * np.pi * f * t) * .5 + highpass(noise(.04), 4000) * .35) * np.exp(-t * 170) * l
def pad(freqs, sec, att=.2, rel=.3):
    t = ta(sec); s = sum(np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t + .3) for f in freqs) / len(freqs)
    return s * np.clip(t / att, 0, 1) * np.clip((sec - t) / rel, 0, 1)
def bass(f, sec):
    t = ta(sec); return lowpass((2 * ((t * f) % 1) - 1) * .45 + np.sin(2 * np.pi * f * t) * .8, 400) * np.exp(-t * 2.2 / sec)
def pluck(f, sec=.3, bright=1.0):
    t = ta(sec); return (np.sin(2 * np.pi * f * t) + .3 * bright * np.sin(4 * np.pi * f * t) + .12 * bright * np.sin(6 * np.pi * f * t)) * np.exp(-t * 13)


# ---------- effects ----------
def whoosh(sec, rising=True, lo=400, hi=4000):
    n = noise(sec); out = np.zeros_like(n)
    for s in range(0, len(n), 512):
        p = s / len(n); c = lo + (hi - lo) * (p if rising else 1 - p); out[s:s + 512] = highpass(lowpass(n[s:s + 512], c * 1.6), c * .5)
    return out * np.sin(np.pi * np.clip(ta(sec) / sec, 0, 1)) ** 2 * .7
def thump(f=70, l=1.0):
    t = ta(.3); return (np.sin(2 * np.pi * np.cumsum(f + 50 * np.exp(-t * 40)) / SR) * np.exp(-t * 16) + lowpass(noise(.3), 1500) * np.exp(-t * 80) * .4) * l
def pop(f0=900, l=1.0):
    t = ta(.11); return np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-t * 18) + 160) / SR) * np.exp(-t * 34) * l
def click(l=1.0):
    t = ta(.06); return highpass(noise(.06), 3000) * (np.exp(-t * 500) + .5 * np.exp(-np.clip(t - .03, 0, None) * 500) * (t > .03)) * l
def flap(n=6, gap=.025):
    out = np.zeros(int(SR * (n * gap + .06)))
    for k in range(n):
        s = tick(.8, 1800 + 160 * k); i = int(k * gap * SR); out[i:i + len(s)] += s
    return out
def impact(l=1.0):
    t = ta(.5); return (np.sin(2 * np.pi * np.cumsum(45 + 100 * np.exp(-t * 16)) / SR) * np.exp(-t * 7) + highpass(noise(.5), 1000) * np.exp(-t * 30) * .35) * l
def buzz(sec=.35):
    t = ta(sec); s = (np.sign(np.sin(2 * np.pi * 175 * t)) * .5 + np.sin(2 * np.pi * 350 * t) * .3) * (np.sin(2 * np.pi * 22 * t) > 0)
    return lowpass(s * np.clip(t / .01, 0, 1) * np.clip((sec - t) / .03, 0, 1), 2000)
def shing(sec=.35):
    return whoosh(sec, True, 3000, 9000) * 1.2
def crackle(t0, t1, n=20):
    for k in range(n):
        place(sfx, t0 + (t1 - t0) * k / n, tick(.6, 1500 + 90 * k), .2, pan=.3 * np.sin(k))
def squeak(sec=.25):
    t = ta(sec); return sweep(1800, 2600, sec) * np.exp(-t * 6) * (1 + .4 * np.sin(2 * np.pi * 40 * t)) * .25
def shimmer(sec=.8):
    t = ta(sec); return sum(np.sin(2 * np.pi * f * t) * np.exp(-((t - k * .08) * 18) ** 2) for k, f in enumerate([2093, 2349, 2637, 3136, 3520, 4186, 4699, 5274, 6272, 7040])) * .15


# ---------- music: 9 bars of 2 s, C G Am F ----------
CH = {"C": ["C3", "E3", "G3"], "G": ["G2", "B2", "D3"], "Am": ["A2", "C3", "E3"], "F": ["F2", "A2", "C3"]}
ROOT = {"C": "C2", "G": "G1", "Am": "A1", "F": "F1"}
PROG = ["C", "G", "Am", "F", "C", "G", "Am", "F", "C"]
for bar, ch in enumerate(PROG):
    s = bar * 2.0
    def on(t): return not (8.5 <= t < 9.0)                     # the full dropout before the poster prints
    arp = [hz(n) * 2 for n in CH[ch]] + [hz(CH[ch][0]) * 4]
    bright = 1.6 if 13.0 <= s < 15.0 else 1.0
    for k in range(16):                                         # pluck arpeggio, on from frame 0
        t = s + k * BEAT / 4
        if on(t) and not (13.9 <= t < 14.05): place(music, t, pluck(arp[k % 4] * (2 if bright > 1 and k % 4 == 3 else 1), .3, bright), .11, pan=-.3 + .2 * (k % 4))
    for k in range(4):                                          # soft kick
        t = s + k * BEAT
        if on(t) and not (13.9 <= t < 14.05): place(music, t, kick(.55 if s < 4 or s >= 15 else .8))
    for k in range(8):                                          # hats
        t = s + k * BEAT / 2
        if on(t): place(music, t, hat(), .35 if k % 2 else .22, pan=.25)
    if s >= 2.0 and s < 17.0:                                   # bass from the painted cut
        for k in range(8):
            t = s + k * BEAT / 2
            if on(t): place(music, t, bass(hz(ROOT[ch]), BEAT / 2 * .95), .38 if s < 15 else .25)
        place(music, s, pad([hz(n) for n in CH[ch]], 2.0 if s != 8.0 else .5), .1)
    if 4.0 <= s < 8.5:                                          # claps on 2 and 4
        for k in (1, 3):
            if on(s + k * BEAT): place(music, s + k * BEAT, clap(), .45)
place(music, 7.0, whoosh(1.5, True, 300, 6000) * np.linspace(0, 1, int(SR * 1.5)) ** 2, .35)   # filtered build into the dropout
for k in range(4): place(music, 8.6 + k * .1, tick(.5 + .15 * k, 2000 + 300 * k), .25)       # one rising tick through the dropout
place(music, 9.0, bass(hz("C2"), .9), .7); place(music, 9.0, kick(1.0)); place(music, 9.0, pad([hz(n) for n in CH["Am"]], 2.0, .02), .12)
place(music, 17.0, kick(.9)); place(music, 17.0, pad([hz(n) for n in CH["C"]] + [hz("C4")], 1.0, .01, .5), .18)
place(music, 17.0, bass(hz("C2"), .9), .5)
for k in range(4): place(music, 17.5 + k * BEAT / 4, hat(k == 3), .3)                       # pickup into frame 0 for the replay

# ---------- effects on screen events ----------
E = [(.45, pop(700), .45), (.90, flap(6), .4), (1.78, whoosh(.4), .5), (2.0, thump(90, .6), .35), (3.0, thump(90, .6), .35),
     (2.50, buzz(.35), .22), (2.40, tick(.7), .3), (2.75, tick(.7), .3), (3.05, tick(.7), .3), (3.50, kick(.9), .6),
     (4.23, whoosh(.6, True, 300, 3500), .5), (6.55, click(), .45), (9.60, impact(.9), .55), (9.60, pop(800), .4),
     (10.20, pop(1000), .35), (10.35, shing(), .3), (10.98, whoosh(.4, True, 400, 2500), .4), (12.10, click(), .5),
     (12.15, tick(.9, 2400), .4), (12.27, tick(.9, 3000), .4), (12.50, squeak(), .5), (13.00, whoosh(.35), .5), (13.00, kick(1.0), .6),
     (13.15, flap(5), .35), (13.45, flap(5), .35), (13.75, flap(5), .35), (13.15, whoosh(.25, False, 800, 3000), .3),
     (13.45, whoosh(.25, False, 800, 3000), .3), (13.75, whoosh(.25, False, 800, 3000), .3), (14.00, impact(1.1), .7),
     (14.54, whoosh(.3, True, 600, 5000), .45), (15.00, shimmer(.8), .55), (16.25, impact(.7), .45), (16.25, pop(900), .4)]
for t, s, g in E: place(sfx, t - LEAD, s, g, pan=0)
for k in range(14): place(sfx, 5.20 + k * .07 + (.12 if k > 8 else 0), tick(.5, 3200), .12)   # typing, with the backspace pause
for k in range(10): place(sfx, 7.20 + k * .105, tick(.35, 3600), .08)                      # streaming tokens
crackle(9.00, 9.60)                                                                       # the halftone print
room = lowpass(noise(1.5), 600) * .02; place(sfx, 2.0, room * np.clip(ta(1.5) / .1, 0, 1) * np.clip((1.5 - ta(1.5)) / .1, 0, 1))

# ---------- voice: Sarah, placed per vo.json; music ducks under it ----------
voice = np.zeros(N)
VO = json.loads((HERE / "assets" / "audio" / "vo.json").read_text(encoding="utf-8"))
for k, v in enumerate(VO):
    with wave.open(str(HERE / "assets" / "audio" / f"vo-{k}.wav")) as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768
    d = highpass(d, 90)                                         # clean up the low end
    i = int(v["place"] * SR); voice[i:i + len(d)] += d[:N - i]
peak = np.abs(voice).max() or 1
voice = np.tanh(voice / peak * 1.6) / np.tanh(1.6) * .9          # gentle compression, peaks ~ -1 dBFS before the master
act = (np.abs(voice) > .02).astype(float); win = int(.15 * SR); cs = np.concatenate([[0], np.cumsum(act)])
duck = np.clip((cs[np.minimum(np.arange(N) + win, N)] - cs[np.maximum(np.arange(N) - win, 0)]) / (2 * win) * 3, 0, 1)
music *= (1 - .45 * duck)[:, None]

gain = 10 ** (float(sys.argv[1]) / 20) if len(sys.argv) > 1 else .5
mix = np.tanh((music * .9 + sfx + voice[:, None] * 1.45) * gain / .84) * .84


def write(path, data):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(data, -1, 1) * 32767).astype("<i2").tobytes())


out = HERE / "assets" / "audio"
write(out / "soundtrack.wav", mix)
print("peak", round(float(np.abs(mix).max()), 3))
