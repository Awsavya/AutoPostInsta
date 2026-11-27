"""Realistic voice clips with Chatterbox (Resemble AI, open source) on its free Hugging Face space.
Usage: python chatterbox_vo.py out.wav "text to say" [exaggeration] [seed]
Never prints secrets.
"""
import json
import subprocess
import sys
import urllib.request

sys.path.insert(0, r"D:\Projects\AutoPostInsta")
from post_instagram import DEFAULT_ENV, read_env  # noqa: E402

out, text = sys.argv[1], sys.argv[2]
exaggeration = float(sys.argv[3]) if len(sys.argv) > 3 else 0.55
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
env = read_env(DEFAULT_ENV)
H = {"user-agent": "AutoPostInsta/1.0", "Authorization": f"Bearer {env['HF_TOKEN']}", "Content-Type": "application/json"}
base = "https://resembleai-chatterbox.hf.space/gradio_api/call/generate_tts_audio"
# no reference clip: the model's own default voice (we don't clone anyone's voice)
data = json.dumps({"data": [text, None, exaggeration, 0.8, seed, 0.5, False]}).encode()
ev = json.loads(urllib.request.urlopen(urllib.request.Request(base, data=data, headers=H), timeout=60).read())["event_id"]
stream = urllib.request.urlopen(urllib.request.Request(f"{base}/{ev}", headers=H), timeout=300).read().decode(errors="replace")
done = next((b for b in stream.split("\n\n") if "event: complete" in b), None)
if not done:
    err = next((b for b in stream.split("\n\n") if "event: error" in b), stream[-300:])
    sys.exit("failed: " + err.split("data:", 1)[-1].strip()[:300])
res = json.loads(done.split("data:", 1)[1].strip())[0]
url = res.get("url") if isinstance(res, dict) else None
raw = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120).read()
tmp = out + ".src"
open(tmp, "wb").write(raw)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ar", "44100", "-ac", "1", out], check=True)
subprocess.run(["cmd", "/c", "del", tmp.replace("/", "\\")], capture_output=True)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print(f"{out}: {dur}s")
