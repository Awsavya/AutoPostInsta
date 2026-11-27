"""Natural voice with ElevenLabs (ELEVENLABS_API_KEY in the env file; never printed).
eleven_tts(text, out_wav, voice_id, model) writes a 44.1 kHz mono WAV.
For an exact pronunciation, wrap the word: <phoneme alphabet="ipa" ph="...">AWSAVYA</phoneme> (works on the
eleven_flash_v2 / eleven_turbo_v2 English models).
"""
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"D:\Projects\AutoPostInsta")
from post_instagram import DEFAULT_ENV, read_env  # noqa: E402

KEY = read_env(DEFAULT_ENV).get("ELEVENLABS_API_KEY", "")
# ElevenLabs' built-in voices (free plan), with their published descriptions
VOICES = {
    "Jessica": ("cgSgspJ2msm6clMCkdW9", "female, young, expressive, conversational"),
    "Laura": ("FGY2WhTYpPnrIDTdsKH5", "female, young, upbeat"),
    "Sarah": ("EXAVITQu4vr4xnSDxMaL", "female, young, soft and warm"),
    "Matilda": ("XrExE9yKIg1WjnnlVkGX", "female, warm, friendly"),
    "Will": ("bIHbv24MWmeRgasZH58o", "male, young, friendly"),
    "Chris": ("iP95p4xoKVk53GoZ742B", "male, casual, natural"),
    "Eric": ("cjVigY5qzO86Huf0OWal", "male, smooth, friendly"),
    "Liam": ("TX3LPaxmHKxFdv7VOQHJ", "male, young, articulate"),
}


def eleven_tts(text, out_wav, voice="Jessica", model="eleven_multilingual_v2", stability=.45, style=.35,
               speed=1.0, previous_text=None, next_text=None, seed=None):
    vid = VOICES.get(voice, (voice,))[0]
    body = {"text": text, "model_id": model,
            "voice_settings": {"stability": stability, "similarity_boost": .8, "style": style, "use_speaker_boost": True, "speed": speed}}
    # the neighbouring lines keep the delivery flowing like one take when lines are made separately
    if previous_text: body["previous_text"] = previous_text
    if next_text: body["next_text"] = next_text
    if seed is not None: body["seed"] = seed
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        mp3 = urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
    tmp = pathlib.Path(str(out_wav) + ".mp3")
    tmp.write_bytes(mp3)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "1", str(out_wav)], check=True)
    tmp.unlink()
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out_wav)],
                                capture_output=True, text=True).stdout)
