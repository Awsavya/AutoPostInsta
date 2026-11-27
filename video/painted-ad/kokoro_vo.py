"""Voiceover with Kokoro (open-source, runs locally). Same lines and beats as voiceover.py, but a natural voice and the
brand said the way the founders say it: "av-sa-vya", with a long "vya" (written as phonemes, so no guessing).
Writes assets/vo/line-N.wav and assets/vo/lines.json.  Run with the .tts venv:
  .tts/Scripts/python kokoro_vo.py [voice] [speed]
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = pathlib.Path(__file__).parent
OUT = HERE / "assets" / "vo"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
BRAND_IPA = "ˈʌvsəvjɑː"   # av-sa-vya, the "vya" drawn out
kokoro = Kokoro(str(HERE / "tts-models" / "kokoro-v1.0.onnx"), str(HERE / "tts-models" / "voices-v1.0.bin"))

LINES = [   # (start, latest end, text). BRAND marks where the brand name is said.
    (0.15, 2.9, "No time to post on Instagram?"),
    (3.05, 5.45, "And the orders keep piling up."),
    (6.35, 9.9, "Meet your helper, built by BRAND. It makes your ad for you,"),
    (10.0, 13.1, "and posts it on time, every single day."),
    (13.6, 15.6, "You bake. It posts."),
    (15.9, 18.95, "Your Instagram, on autopilot. BRAND dot in."),
]


def phonemes(text):
    """Phonemize the line, then put the brand's own pronunciation where BRAND was."""
    parts = text.split("BRAND")
    out = []
    for i, part in enumerate(parts):
        if part.strip():
            out.append(kokoro.tokenizer.phonemize(part.strip(), "en-us"))
        if i < len(parts) - 1:
            out.append(BRAND_IPA)
    return " ".join(out)


meta = []
for i, (start, end, text) in enumerate(LINES):
    ph = phonemes(text)
    speed = SPEED
    for _ in range(4):   # speed up a touch (never past 1.15x) only if the line would overrun its beat
        samples, sr = kokoro.create(ph, voice=VOICE, speed=speed, lang="en-us", is_phonemes=True)
        dur = len(samples) / sr
        if start + dur <= end or speed >= 1.15:
            break
        speed = min(1.15, speed * dur / (end - start) + .01)
    samples = np.asarray(samples, dtype=np.float32)
    sf.write(str(OUT / f"line-{i}.wav"), samples, sr)
    print(f"line {i}: {dur:.2f}s from {start:.2f} (to {end:.2f}) speed {speed:.2f} {'ok' if start + dur <= end else 'TOO LONG'} | {ph}")
    meta.append({"start": start, "end": end, "dur": dur, "text": text.replace("BRAND", "AWSAVYA")})
(OUT / "lines.json").write_text(json.dumps(meta, indent=1))
