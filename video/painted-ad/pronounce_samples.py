"""Six ways to say AWSAVYA, so the founders can pick the right one. Each clip says "<name>. Built by <name>."
with the name written as exact phonemes. Writes assets/pronounce/awsavya-1.wav .. -6.wav.
Run with the .tts venv:  .tts/Scripts/python pronounce_samples.py [voice]
"""
import pathlib
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = pathlib.Path(__file__).parent
OUT = HERE / "assets" / "pronounce"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
kokoro = Kokoro(str(HERE / "tts-models" / "kokoro-v1.0.onnx"), str(HERE / "tts-models" / "voices-v1.0.bin"))

VARIANTS = [   # same start ("uhv-suh"), six different endings
    ("ˈʌvsəvjə", "uhv-suh-vyuh (short 'vyuh')"),
    ("ˈʌvsəvi", "uhv-suh-vee (like 'savvy')"),
    ("ˈʌvsəvɪ", "uhv-suh-vih (very short 'vih')"),
    ("ˈʌvsəvjɪ", "uhv-suh-vyih ('vy' with a tiny 'ih')"),
    ("ˈʌvsəvjiː", "uhv-suh-vyee (a long 'yyy' at the end)"),
    ("ˈʌvsəvaɪ", "uhv-suh-vye (rhymes with 'bye')"),
]
built_by = kokoro.tokenizer.phonemize("Built by", "en-us")
for i, (ipa, label) in enumerate(VARIANTS, 1):
    samples, sr = kokoro.create(f"{ipa}. {built_by} {ipa}.", voice=VOICE, speed=0.95, lang="en-us", is_phonemes=True)
    sf.write(str(OUT / f"awsavya-{i}.wav"), np.asarray(samples, dtype=np.float32), sr)
    print(f"{i}: {label}  [{ipa}]  {len(samples) / sr:.1f}s")
