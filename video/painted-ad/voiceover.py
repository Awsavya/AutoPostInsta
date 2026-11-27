"""Voiceover for the painted reel: one TTS clip per line, timed to the story beats, using the free Workers AI
allowance on the Cloudflare accounts in the env file. Writes assets/vo/line-N.wav and assets/vo/lines.json
(start time and length of each line). Never prints secrets.  Usage: python voiceover.py [model] [speaker]
"""
import base64
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"D:\Projects\AutoPostInsta")
from post_instagram import DEFAULT_ENV, read_env  # noqa: E402

HERE = pathlib.Path(__file__).parent
OUT = HERE / "assets" / "vo"
OUT.mkdir(parents=True, exist_ok=True)
env = read_env(DEFAULT_ENV)
MODEL = sys.argv[1] if len(sys.argv) > 1 else "@cf/deepgram/aura-1"
SPEAKER = sys.argv[2] if len(sys.argv) > 2 else "luna"

# (start, latest end, text). Each line must finish before the next beat it belongs to.
LINES = [
    (0.15, 2.9, "No time to post on Instagram?"),
    (3.05, 5.45, "And the orders keep piling up."),
    (6.35, 9.9, "Meet your helper, built by Awsavya. It makes your ad for you,"),
    (10.0, 13.1, "and posts it on time, every single day."),
    (13.6, 15.6, "You bake. It posts."),
    (15.9, 18.95, "Your Instagram, on autopilot. Awsavya dot in."),
]


def accounts():
    for n in [""] + [f"_{i}" for i in range(2, 21)]:
        if env.get(f"CF_ACCOUNT_ID{n}") and env.get(f"CF_API_TOKEN{n}"):
            yield n or "_1", env[f"CF_ACCOUNT_ID{n}"], env[f"CF_API_TOKEN{n}"]


def tts(text):
    body = {"text": text, "speaker": SPEAKER} if "deepgram" in MODEL else {"prompt": text, "lang": "en"}
    for label, acc, tok in accounts():
        req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{MODEL}",
                                     data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                ctype, data = r.headers.get("content-type", ""), r.read()
            if "json" in ctype:
                j = json.loads(data)
                audio = (j.get("result") or {}).get("audio")
                if not audio:
                    raise RuntimeError(str(j)[:200])
                data = base64.b64decode(audio)
            return label, data
        except urllib.error.HTTPError as e:
            print(f"  {label}: HTTP {e.code} {e.read()[:160]!r}")
    raise SystemExit("no account could make the voice")


meta = []
for i, (start, end, text) in enumerate(LINES):
    label, data = tts(text)
    raw = OUT / f"line-{i}.bin"
    raw.write_bytes(data)
    wav = OUT / f"line-{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "44100", "-ac", "1", str(wav)], check=True)
    raw.unlink()
    probe = lambda f: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                           capture_output=True, text=True).stdout)
    dur = probe(wav)
    if start + dur > end and dur / (end - start) <= 1.15:   # a touch faster to fit its beat, never more than 15%
        fast = OUT / f"line-{i}-fit.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-filter:a", f"atempo={dur / (end - start) + .01:.3f}", str(fast)], check=True)
        fast.replace(wav); dur = probe(wav)
    fits = start + dur <= end
    print(f"line {i}: {dur:.2f}s from {start:.2f} (window to {end:.2f}) {'ok' if fits else 'TOO LONG'} via account {label}")
    meta.append({"start": start, "end": end, "dur": dur, "text": text})
(OUT / "lines.json").write_text(json.dumps(meta, indent=1))
