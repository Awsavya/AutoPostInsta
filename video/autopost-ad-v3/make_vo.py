"""Voiceover for v3: ElevenLabs Sarah, one clip per line, placed on the plan's beats (final-plan.json "voiceover").
AWSAVYA is always given as exact sounds (approved: ˈʌvsəvjɛ), which needs the eleven_flash_v2 model; the other lines
use eleven_multilingual_v2 (the model of the audition the owner picked). Neighbouring lines are passed as context so
the delivery flows like one take. Writes assets/audio/vo-N.wav and assets/audio/vo.json.  Usage: python make_vo.py
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "painted-ad"))
import eleven_vo as e  # noqa: E402

BRAND = '<phoneme alphabet="ipa" ph="ˈʌvsəvjɛ">AWSAVYA</phoneme>'
plan = json.loads((HERE / "final-plan.json").read_text(encoding="utf-8"))["voiceover"]
texts = [v["text"] for v in plan]
OUT = HERE / "assets" / "audio"
OUT.mkdir(parents=True, exist_ok=True)
meta = []
for i, v in enumerate(plan):
    has_brand = "AWSAVYA" in v["text"]
    text = v["text"].replace("AWSAVYA", BRAND) if has_brand else v["text"]
    model = "eleven_flash_v2" if has_brand else "eleven_multilingual_v2"
    window = v["end"] - v["start"]
    speed = 1.0
    for _ in range(3):
        dur = e.eleven_tts(text, OUT / f"vo-{i}.wav", "Sarah", model=model, stability=.42, style=.35, speed=speed, seed=11 + i,
                           previous_text=" ".join(texts[max(0, i - 2):i]).replace("AWSAVYA", "Avsavyeh") or None,
                           next_text=(texts[i + 1].replace("AWSAVYA", "Avsavyeh") if i + 1 < len(texts) else None))
        # trim the leading/trailing silence so placement is exact
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"vo-{i}.wav"), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        str(OUT / f"vo-{i}-t.wav")], check=True)
        (OUT / f"vo-{i}-t.wav").replace(OUT / f"vo-{i}.wav")
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(OUT / f"vo-{i}.wav")],
                                   capture_output=True, text=True).stdout)
        if dur <= window + .25 or speed >= 1.07:
            break
        speed = min(1.07, round(speed * dur / window + .02, 2))
    fits = dur <= window + .25
    print(f"{i}: {dur:.2f}s for a {window:.2f}s window at {v['start']:.2f} speed {speed} {model} {'ok' if fits else 'LONG'} | {v['text']}")
    meta.append({"start": v["start"], "end": v["end"], "dur": dur, "text": v["text"], "model": model, "speed": speed})
(OUT / "vo.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
