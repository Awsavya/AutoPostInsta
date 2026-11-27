"""Natural voice with Gemini TTS (Google AI Studio key in the env file as GEMINI_API_KEY; never printed).
gemini_tts(text, out_wav, voice, style) writes a 24 kHz mono WAV. Run directly to make the six AWSAVYA pronunciation clips:
  python gemini_vo.py samples [voice]
"""
import base64
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request
import wave

sys.path.insert(0, r"D:\Projects\AutoPostInsta")
from post_instagram import DEFAULT_ENV, read_env  # noqa: E402

HERE = pathlib.Path(__file__).parent
KEY = read_env(DEFAULT_ENV).get("GEMINI_API_KEY", "")
MODEL = "gemini-3.1-flash-tts-preview"  # follows the style direction without reading it aloud (3.8 reads it)
STYLE = "Say warmly and naturally, in an Indian English accent, like a real person talking to a friend"


def gemini_tts(text, out_wav, voice="Sulafat", style=STYLE, model=MODEL):
    body = {"contents": [{"parts": [{"text": f"{style}: {text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                 data=json.dumps(body).encode(), headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
    part = None
    for attempt in range(4):
        try:
            res = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            msg = e.read()[:300]
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(8 * (attempt + 1)); continue
            raise SystemExit(f"Gemini TTS HTTP {e.code}: {msg!r}")
        cand = (res.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        if parts and "inlineData" in parts[0]:
            part = parts[0]["inlineData"]; break
        time.sleep(3)   # an empty answer now and then (finishReason without audio): just ask again
    if part is None:
        raise SystemExit(f"Gemini TTS gave no audio (finishReason {cand.get('finishReason')})")
    pcm = base64.b64decode(part["data"])
    rate = int(part.get("mimeType", "rate=24000").split("rate=")[-1].split(";")[0]) if "rate=" in part.get("mimeType", "") else 24000
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    return len(pcm) / 2 / rate


if __name__ == "__main__" and sys.argv[1:2] == ["samples"]:
    voice = sys.argv[2] if len(sys.argv) > 2 else "Sulafat"
    out = HERE / "assets" / "pronounce"
    out.mkdir(parents=True, exist_ok=True)
    variants = ["अवसव्य", "अव्सव्य", "Avsavy", "Uv-suh-vy", "Avsuv-y", "Avsavyeh"]
    for i, name in enumerate(variants, 1):
        dur = gemini_tts(f"{name}. Built by {name}.", out / f"gemini-{i}.wav", voice)
        print(f"{i}: written as {name!r}  ({dur:.1f}s)")
