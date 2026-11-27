"""Synthesize this reel's own soundtrack and sound effects (deterministic, no samples, no network).

120 BPM, 2 s bars. Bar 1: near silence + clock ticks. Bars 2-3: ticks, soft pulse kick, a rising drone, a riser,
then half a beat of silence (the break). 6.0: the drop, C-G-Am-F groove, one new layer per bar. 14.0: resolve to C and fade.
Effects sit one frame after the picture they belong to. Writes assets/audio/music.wav and assets/audio/sfx.wav.
Usage: python make_audio.py [gain_db]   (gain applied to both, used for loudness matching)
"""
import pathlib
import sys
import wave

import numpy as np

SR, DUR, BPM = 44100, 16.0, 120
BEAT = 60 / BPM
N = int(SR * DUR)
F = 1 / 30  # one video frame: sound lands just after its picture
rng = np.random.default_rng(7)
OUT = pathlib.Path(__file__).parent / "assets" / "audio"


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def place(buf, start, sig, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i : i + len(sig), 0] += sig * left * 1.414
    buf[i : i + len(sig), 1] += sig * right * 1.414


def env(n_sec, attack=0.005, decay=0.2, curve=4.0):
    t = t_axis(n_sec)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-curve * np.clip(t - attack, 0, None) / max(decay, 1e-4))
    return a * d


def lowpass(x, cutoff):
    # one-pole low-pass, enough for softening noise and saws
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def note(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    pitch, octave = name[:-1], int(name[-1])
    return 440 * 2 ** ((names[pitch] + 12 * (octave + 1) - 69) / 12)


# ---------------- instruments ----------------

def kick(level=1.0):
    t = t_axis(0.45)
    freq = 50 + 110 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 7.5)
    click = highpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 300) * 0.25
    return (body + click) * level


def clap():
    t = t_axis(0.3)
    noise = highpass(rng.standard_normal(len(t)), 900)
    e = np.zeros_like(t)
    for off in (0, 0.011, 0.022):
        e += np.exp(-np.clip(t - off, 0, None) * 60) * (t >= off)
    return lowpass(noise * e * 0.6, 6000)


def hat(open_=False):
    t = t_axis(0.25 if open_ else 0.06)
    return highpass(rng.standard_normal(len(t)), 7000) * np.exp(-t * (18 if open_ else 90)) * 0.35


def tick():
    t = t_axis(0.05)
    return (np.sin(2 * np.pi * 2400 * t) * 0.5 + highpass(rng.standard_normal(len(t)), 4000) * 0.4) * np.exp(-t * 160)


def bass_note(freq, sec):
    t = t_axis(sec)
    saw = 2 * ((t * freq) % 1) - 1
    sub = np.sin(2 * np.pi * freq * t)
    return lowpass(saw * 0.5 + sub * 0.8, 420) * env(sec, 0.005, sec * 0.9, 2.5)


def pad(freqs, sec, attack=0.25):
    t = t_axis(sec)
    sig = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t + 0.4) for f in freqs) / len(freqs)
    a = np.clip(t / attack, 0, 1)
    r = np.clip((sec - t) / 0.3, 0, 1)
    return sig * a * r


def pluck(freq, sec=0.35):
    t = t_axis(sec)
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) + 0.12 * np.sin(2 * np.pi * freq * 3 * t)
    return tone * env(sec, 0.002, 0.12, 3.5)


# ---------------- music ----------------
music = np.zeros((N, 2))
CHORDS = {"C": ["C3", "E3", "G3"], "G": ["G2", "B2", "D3"], "Am": ["A2", "C3", "E3"], "F": ["F2", "A2", "C3"]}
ROOT = {"C": "C2", "G": "G1", "Am": "A1", "F": "F1"}

# Bars 1-3 (0-5.5): clock ticks every beat; from 2.0 a soft pulse kick; a low drone that slowly rises in level.
for b in range(11):
    place(music, b * BEAT, tick(), 0.16 if b < 4 else 0.2, pan=0.3 * (-1) ** b)
for b in range(4, 11):
    place(music, b * BEAT, kick(0.18 + 0.045 * (b - 4)), 1.0)  # fades in, no startle after the quiet hook
drone_t = t_axis(5.5)
drone = (np.sin(2 * np.pi * note("C2") * drone_t) + 0.5 * np.sin(2 * np.pi * note("G2") * drone_t)) * (0.35 + 0.65 * np.clip(drone_t / 5.5, 0, 1))
place(music, 0, drone * 0.22)
# Riser 5.0-5.5 into the break: filtered noise sweeping up plus a rising sine.
rt = t_axis(0.5)
riser = highpass(rng.standard_normal(len(rt)), 1500) * (rt / 0.5) ** 2 * 0.35
riser += np.sin(2 * np.pi * np.cumsum(300 + 900 * (rt / 0.5) ** 2) / SR) * (rt / 0.5) ** 2 * 0.15
place(music, 5.0, riser)
# 5.5-6.0: the break, total silence.

# 6.0-14.0: the groove. C - G - Am - F, one bar each, twice through the last bars as needed.
prog = ["C", "G", "Am", "F"]
for bar in range(4):  # bars starting 6, 8, 10, 12
    start = 6.0 + bar * 2
    ch = prog[bar]
    place(music, start, pad([note(n) for n in CHORDS[ch]], 2.0, attack=0.02 if bar == 0 else 0.15), 0.16)
    for i in range(8):  # bass eighths
        place(music, start + i * BEAT / 2, bass_note(note(ROOT[ch]), BEAT / 2 * 0.95), 0.5)
    for i in range(4):  # four-on-the-floor kick
        place(music, start + i * BEAT, kick(0.9))
    if bar >= 1:  # bar 5 adds clap and hats
        for i in (1, 3):
            place(music, start + i * BEAT, clap(), 0.55)
        for i in range(8):
            place(music, start + i * BEAT / 2, hat(open_=(i % 2 == 1)), 0.6 if i % 2 else 0.4, pan=0.25)
    if bar >= 2:  # bar 6 adds a sixteenth-note pluck arpeggio
        arp = [note(n) * 2 for n in CHORDS[ch]] + [note(CHORDS[ch][0]) * 4]
        for i in range(16):
            place(music, start + i * BEAT / 4, pluck(arp[i % 4]), 0.13, pan=-0.3 + 0.6 * (i % 4) / 3)
# 14.0: resolve to C, everything lands on the tonic and rings out to the end.
place(music, 14.0, kick(0.8))
place(music, 14.0, pad([note(n) for n in CHORDS["C"]] + [note("C4")], 2.0, attack=0.01), 0.2)
place(music, 14.0, bass_note(note("C2"), 1.9), 0.55)
for i, n in enumerate(["C5", "E5", "G5", "C6"]):
    place(music, 14.0 + i * BEAT / 4, pluck(note(n), 1.2), 0.12)
fade = np.ones(N)
fade[int(15.0 * SR):] = np.linspace(1, 0, N - int(15.0 * SR))
music *= fade[:, None]

# ---------------- sound effects ----------------
sfx = np.zeros((N, 2))


def whoosh(sec, rising=True):
    t = t_axis(sec)
    noise = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = 512
    for s in range(0, len(t), seg):  # sweep a band through the noise
        p = s / len(t)
        c = 400 + 3600 * (p if rising else 1 - p)
        out[s : s + seg] = highpass(lowpass(noise[s : s + seg], c * 1.6), c * 0.5)
    shape = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 2
    return out * shape * 0.7


def thud(freq=80, level=1.0):
    t = t_axis(0.35)
    body = np.sin(2 * np.pi * np.cumsum(freq + 60 * np.exp(-t * 40)) / SR) * np.exp(-t * 14)
    knock = lowpass(rng.standard_normal(len(t)), 1800) * np.exp(-t * 90) * 0.5
    return (body + knock) * level


def impact():
    t = t_axis(0.7)
    boom = np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-t * 18)) / SR) * np.exp(-t * 5)
    crack = highpass(rng.standard_normal(len(t)), 1200) * np.exp(-t * 35) * 0.45
    return boom + crack


def key_tick():
    t = t_axis(0.03)
    return highpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 260) * 0.5


def mouse_click():
    t = t_axis(0.06)
    c = highpass(rng.standard_normal(len(t)), 3000) * (np.exp(-t * 500) + 0.6 * np.exp(-np.clip(t - 0.035, 0, None) * 500) * (t > 0.035))
    return c * 0.8


def pop(f0=900, level=1.0):
    t = t_axis(0.12)
    freq = f0 * np.exp(-t * 18) + 180
    return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 35) + key_tick()[: len(t)].sum() * 0) * level


place(sfx, 1.5, whoosh(0.55), 0.4)                     # bar floods the frame -> cut 2.0
for t, g in zip((2.5, 3.0, 3.25, 3.5), (0.42, 0.55, 0.65, 0.75)):  # chores land on the pile, building
    place(sfx, t + F - 0.01, thud(75), g, pan=rng.uniform(-0.3, 0.3))
for t in (4.0, 4.5, 5.0):                               # Every. Single. Day.
    place(sfx, t + F - 0.01, impact(), 0.75)
place(sfx, 5.72, whoosh(0.32), 0.7)                     # whip up -> the drop at 6.0
place(sfx, 6.0 + F, thud(60, 0.6), 0.7)                 # card lands on the drop
keys = np.linspace(6.42, 7.18, 15) + rng.uniform(-0.012, 0.012, 15)
for k in keys:                                          # the idea types itself
    place(sfx, k, key_tick(), 0.45, pan=rng.uniform(-0.2, 0.2))
place(sfx, 7.5 + F - 0.005, mouse_click(), 0.9)         # click "Write it with AI"
place(sfx, 7.76, whoosh(0.26), 0.55)                    # zoom through
place(sfx, 8.25 + F, pop(1100), 0.35)                   # label
place(sfx, 9.0 + F, pop(700, 1.2), 0.6)                 # "Made by AI" sticker
place(sfx, 9.5 + F, pop(1000), 0.35)                    # CTA chip
place(sfx, 9.98, whoosh(0.3, rising=False), 0.35)       # into Publish
place(sfx, 10.5 + F - 0.005, mouse_click(), 0.9)        # click Publish
place(sfx, 11.0 + F, pop(850), 0.4)                     # Scheduled
for i in range(7):                                      # a week checked off
    place(sfx, 11.32 + i * 0.125 + F, pop(1200 + 60 * i), 0.22, pan=-0.6 + i * 0.2)
place(sfx, 12.3, whoosh(0.3), 0.5)                      # cut to the end card
place(sfx, 13.0 + F, thud(70, 0.6), 0.55)               # logo settles
place(sfx, 13.5 + F, pop(800, 1.3), 0.55)               # CTA lands

# ---------------- level and write ----------------
gain = 10 ** (float(sys.argv[1]) / 20) if len(sys.argv) > 1 else 0.5


def soft_limit(x, ceiling=0.84):  # about -1.5 dBFS
    return np.tanh(x / ceiling) * ceiling


def write(path, data):
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


OUT.mkdir(parents=True, exist_ok=True)
music_out, sfx_out = music * gain, sfx * gain
mix = soft_limit(music_out + sfx_out)
# keep the two stems consistent with the limited mix so they add up to it
scale = np.where(np.abs(music_out + sfx_out) > 1e-9, mix / np.where(np.abs(music_out + sfx_out) > 1e-9, music_out + sfx_out, 1), 1)
write(OUT / "music.wav", music_out * scale)
write(OUT / "sfx.wav", sfx_out * scale)
write(OUT / "mix-preview.wav", mix)
print("peak mix", round(float(np.abs(mix).max()), 3))
