"""Soundtrack for the painted bakery reel, synthesized for this film (no samples, no network). Writes assets/soundtrack.wav.

120 BPM, 2 s bars. 0-3: quiet dawn (warm pad, clock ticks, kneading thumps, phone buzzes). 3-5.25: the rush (kick, fast
ticking clock, tray clanks, croissants flopping). 5.25-5.5 push, 5.5-6.0 silence (the break). 6.0: the oven bangs open
and the groove drops with Tile. 13.15: shimmer into the flash. 13.4: calm morning with birds. 16.0: resolve, fade to 19.
Every effect sits one frame after the picture it belongs to.  Usage: python make_audio.py [gain_db]
"""
import pathlib
import sys
import wave

import numpy as np

SR, DUR, BPM = 44100, 19.0, 120
BEAT = 60 / BPM
N = int(SR * DUR)
F = 1 / 24
rng = np.random.default_rng(11)
OUT = pathlib.Path(__file__).parent / "assets" / "soundtrack.wav"
mix = np.zeros((N, 2))


def ta(sec):
    return np.arange(int(SR * sec)) / SR


def place(start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    mix[i : i + len(sig), 0] += sig * np.cos((pan + 1) * np.pi / 4) * 1.414
    mix[i : i + len(sig), 1] += sig * np.sin((pan + 1) * np.pi / 4) * 1.414


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def noise(sec):
    return rng.standard_normal(int(SR * sec))


def hz(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    return 440 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69) / 12)


def sweep(f0, f1, sec, curve=1.0):
    t = ta(sec)
    f = f0 + (f1 - f0) * (t / sec) ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------------- instruments ----------------
def kick(level=1.0):
    t = ta(0.4)
    return (np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-t * 30)) / SR) * np.exp(-t * 8) + highpass(noise(0.4), 2500) * np.exp(-t * 300) * .2) * level


def clap():
    t = ta(0.25)
    e = sum(np.exp(-np.clip(t - o, 0, None) * 60) * (t >= o) for o in (0, .01, .021))
    return lowpass(highpass(noise(0.25), 900) * e * .55, 6500)


def hat():
    t = ta(0.05)
    return highpass(noise(0.05), 7000) * np.exp(-t * 95) * .3


def tick(level=1.0):
    t = ta(0.04)
    return (np.sin(2 * np.pi * 2600 * t) * .5 + highpass(noise(0.04), 4000) * .35) * np.exp(-t * 170) * level


def pad(freqs, sec, attack=.3, release=.4):
    t = ta(sec)
    s = sum(np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 2 * f * t + .3) for f in freqs) / len(freqs)
    return s * np.clip(t / attack, 0, 1) * np.clip((sec - t) / release, 0, 1)


def bass(f, sec):
    t = ta(sec)
    saw = 2 * ((t * f) % 1) - 1
    return lowpass(saw * .45 + np.sin(2 * np.pi * f * t) * .8, 400) * np.exp(-t * 2.2 / sec)


def pluck(f, sec=.3):
    t = ta(sec)
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 14)


def marimba(f, sec=.5):
    t = ta(sec)
    return (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)) * np.exp(-t * 7)


# ---------------- effects ----------------
def whoosh(sec, rising=True, lo=400, hi=4000):
    n = noise(sec)
    out = np.zeros_like(n)
    for s in range(0, len(n), 512):
        p = s / len(n)
        c = lo + (hi - lo) * (p if rising else 1 - p)
        out[s : s + 512] = highpass(lowpass(n[s : s + 512], c * 1.6), c * .5)
    return out * np.sin(np.pi * np.clip(ta(sec) / sec, 0, 1)) ** 2 * .7


def thump(f=70, level=1.0):
    t = ta(0.3)
    return (np.sin(2 * np.pi * np.cumsum(f + 50 * np.exp(-t * 40)) / SR) * np.exp(-t * 16) + lowpass(noise(0.3), 1500) * np.exp(-t * 80) * .4) * level


def buzz(sec=.35, muffled=False):
    t = ta(sec)
    s = np.sign(np.sin(2 * np.pi * 175 * t)) * .5 + np.sin(2 * np.pi * 350 * t) * .3
    s *= (np.sin(2 * np.pi * 22 * t) > 0) * np.clip(t / .01, 0, 1) * np.clip((sec - t) / .03, 0, 1)
    return lowpass(s, 600 if muffled else 2200) * (.5 if muffled else 1)


def clank():
    t = ta(0.6)
    return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * a for f, d, a in ((523, 6, .5), (1310, 9, .35), (2290, 14, .25), (3570, 20, .15))) + highpass(noise(.6), 2000) * np.exp(-t * 60) * .3


def flop():
    t = ta(0.12)
    return lowpass(noise(0.12), 900) * np.exp(-t * 45) * .7 + np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40) * .3


def boing(f0=300, f1=900, sec=.28):
    t = ta(sec)
    return sweep(f0, f1, sec, .6) * np.exp(-t * 6) * (1 + .3 * np.sin(2 * np.pi * 18 * t)) * .5


def pop(f0=900, level=1.0):
    t = ta(0.11)
    return np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-t * 18) + 160) / SR) * np.exp(-t * 34) * level


def shutter():
    t = ta(0.12)
    c = highpass(noise(0.12), 2500)
    return c * (np.exp(-t * 400) + .8 * np.exp(-np.clip(t - .06, 0, None) * 300) * (t > .06)) * .9


def swish(sec=.3):
    return whoosh(sec, True, 1500, 6000) * 1.1


def boom():
    t = ta(0.9)
    return np.sin(2 * np.pi * np.cumsum(42 + 90 * np.exp(-t * 14)) / SR) * np.exp(-t * 4.5) + highpass(noise(.9), 900) * np.exp(-t * 18) * .35


def bird(t0, f=3200):
    for i in range(3):
        t = ta(0.07)
        place(t0 + i * .09, sweep(f, f * 1.35, .07) * np.exp(-t * 25) * np.sin(np.pi * t / .07), .12, pan=.5)


# ---------------- music ----------------
CH = {"C": ["C3", "E3", "G3", "B3"], "G": ["G2", "B2", "D3", "F#3"], "Am": ["A2", "C3", "E3", "G3"], "F": ["F2", "A2", "C3", "E3"]}
ROOT = {"C": "C2", "G": "G1", "Am": "A1", "F": "F1"}
# dawn 0-3: warm pad, clock tick, soft kneading thumps on the beat
place(0, pad([hz(n) for n in CH["C"]], 3.2, .02, .5), .16)
place(0, pad([hz(n) for n in CH["F"]], 3.2, 1.5, .5) * 0, 0)
for b in range(6):
    place(b * BEAT, tick(.8), .18, pan=.3 * (-1) ** b)
    place(b * BEAT + F, thump(90, .5), .35)
# the rush 3.0-5.25: kick on the beat, hats, clock racing
for b in range(6, 11):
    place(b * BEAT, kick(.75))
for i in range(int(2.4 / (BEAT / 4))):
    place(3.0 + i * BEAT / 4, tick(.6), .12, pan=.3)
for i in range(9):
    place(3.0 + i * BEAT / 2, hat(), .5, pan=-.2)
place(3.0, pad([hz(n) for n in CH["Am"]], 2.3, .1, .3), .1)
# a rising tone into the push, then the break (5.5-6.0 silent)
place(4.5, sweep(220, 660, 1.0, 2) * np.linspace(0, 1, int(SR * 1.0)) ** 2 * .12)
# 6.0 the drop: the groove, C - G - Am - F, a bar each, from 6 to 14
for bar, ch in enumerate(["C", "G", "Am", "F"]):
    s = 6.0 + bar * 2
    place(s, pad([hz(n) for n in CH[ch]], 2.0, .02 if bar == 0 else .15, .2), .14)
    for i in range(8):
        place(s + i * BEAT / 2, bass(hz(ROOT[ch]), BEAT / 2 * .95), .45)
    for i in range(4):
        place(s + i * BEAT, kick(.85))
    if bar >= 1:
        for i in (1, 3):
            place(s + i * BEAT, clap(), .5)
        for i in range(8):
            place(s + i * BEAT / 2, hat(), .45 if i % 2 else .3, pan=.25)
    if bar >= 2:  # a marimba melody over the posts landing
        mel = {"Am": ["E5", "C5", "A4", "C5", "E5", "G5", "E5", "C5"], "F": ["F5", "C5", "A4", "C5", "F5", "A5", "G5", "E5"]}[ch]
        for i, n in enumerate(mel):
            place(s + i * BEAT / 2, marimba(hz(n)), .12, pan=-.2 + .05 * i)
# 13.4 morning: calm, lighter groove, birds
for bar, ch in enumerate(["C", "F"]):
    s = 13.4 + bar * 1.3
    place(s, pad([hz(n) for n in CH[ch]], 1.4, .2, .3), .15)
for i in range(5):
    place(13.5 + i * BEAT, pluck(hz(["E5", "G5", "C6", "G5", "E5"][i]), .5), .1, pan=.3)
for i in range(6):
    place(14.0 + i * BEAT, kick(.5))
    place(14.0 + i * BEAT + BEAT / 2, hat(), .3)
bird(13.55); bird(14.4, 3600); bird(15.3, 3000)
# 16.0 resolve and ring out
place(16.0, kick(.7))
place(16.0, pad([hz(n) for n in CH["C"]] + [hz("C4")], 3.0, .02, 1.6), .2)
place(16.0, bass(hz("C2"), 2.5), .5)
for i, n in enumerate(["C5", "E5", "G5", "C6"]):
    place(16.0 + i * BEAT / 4, marimba(hz(n), 1.2), .12)

# ---------------- effects on the picture ----------------
place(1.0 + F, buzz(), .2, pan=.4); place(2.25 + F, buzz(.45), .28, pan=.4)
place(1.0 + F, thump(160, .5), .35, pan=.4); place(2.25 + F, thump(160, .5), .35, pan=.4)  # the phone knocks the counter as it hops          # phone buzzes
place(2.8, whoosh(.38), .6)                                                          # whip pan
for t, p in ((3.2, -.6), (3.7, -.6)):
    place(t, whoosh(.3, True, 300, 1800), .35, pan=p)                                # trays slide in
place(3.5 + F, clank(), .35, pan=-.5); place(4.0 + F, clank(), .35, pan=-.4)         # and clank down
for i in range(16):
    place(4.35 + i * .05 + .32 + F, flop(), .45, pan=.1 + .3 * np.sin(i))              # croissants flop onto the pile
place(5.25 + F, buzz(.35, muffled=True), .5, pan=.3)                                  # muffled buzz under the pile
place(5.22, whoosh(.3, True), .45)                                                    # push into the oven
place(6.0 + F, boom(), .48); place(6.0 + F, clank(), .22)                               # the oven door bangs open
place(6.4, boing(260, 820), .5, pan=.3); place(7.0 + F, pop(500, 1.2), .5)          # Tile hops out, lands
place(7.25 + F, tick(1), .4)                                                          # salute
place(8.0 + F, shutter(), .7); place(8.0, whoosh(.25, False, 2000, 7000), .3)        # FLASH
for t in (8.3, 8.65, 8.95):
    place(t, swish(.3), .45, pan=-.2)                                                 # brush strokes
place(8.65 + .1 + F, pop(1000), .35); place(9.5 + F, pop(800, 1.2), .5)             # croissant appears, check pops
place(10.0, boing(320, 900, .3), .4, pan=.1); place(10.35 + F, pop(600), .3)        # phone hops out of the pile
place(10.25, whoosh(.5, False, 900, 3500), .5)                                        # the throw
place(10.8 + F, pop(1200, 1.1), .5)                                                   # it lands in the phone
for i in range(8):
    place(11.25 + i * BEAT / 2 + F, pop(1100 + 70 * i), .5, pan=-.4 + .1 * i)        # a post every day
for i in range(6):
    place(12.5 + i * .28 + F, pop(1600, .6), .12, pan=.3)                            # hearts
place(12.9, sweep(600, 2400, .5, 2) * np.linspace(0, 1, int(SR * .5)) ** 2 * .15)  # shimmer into the flash
place(14.25, boing(300, 900), .4, pan=-.2); place(14.75 + F, pop(500, 1.1), .45)    # Tile hops to the shoulder
place(15.1 + F, pop(1300), .35)                                                       # heart
place(15.65, swish(.4), .6)                                                           # yellow brush wipe
place(16.55 + F, thump(70, .6), .4); place(17.15 + F, pop(800, 1.3), .5)            # logo, button

fade = np.ones(N)
fade[int(17.6 * SR):] = np.linspace(1, 0, N - int(17.6 * SR))
mix *= fade[:, None]

# ---------------- voiceover: placed at its beats, music and effects duck under it ----------------
import json  # noqa: E402
VO = OUT.parent / "vo"
if (VO / "lines.json").exists():
    voice = np.zeros(N)
    for i, L in enumerate(json.loads((VO / "lines.json").read_text())):
        with wave.open(str(VO / f"line-{i}.wav")) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768
        i0 = int(L["start"] * SR)
        voice[i0 : i0 + len(data)] += data[: N - i0]
    voice *= .9 / max(1e-6, np.abs(voice).max())
    act = (np.abs(voice) > .02).astype(float)
    win = int(.18 * SR)  # a moving average makes the duck ease in and out instead of pumping
    cs = np.concatenate([[0], np.cumsum(act)])
    smooth = np.clip((cs[np.minimum(np.arange(N) + win, N)] - cs[np.maximum(np.arange(N) - win, 0)]) / (2 * win) * 3, 0, 1)
    mix *= (1 - .5 * smooth)[:, None]
    mix += voice[:, None] * 1.5
gain = 10 ** (float(sys.argv[1]) / 20) if len(sys.argv) > 1 else .5
out = np.tanh(mix * gain / .84) * .84
OUT.parent.mkdir(exist_ok=True)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes())
print("peak", round(float(np.abs(out).max()), 3))
