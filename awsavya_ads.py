"""AWSAVYA Instagram ads: Flux 2 Dev draws the scene and headline, code adds the copy band and real logo.

Usage: python -I awsavya_ads.py <env_file> <out_dir> [ad_key ...]
Reads CF_ACCOUNT_ID / CF_API_TOKEN (and optional backups CF_ACCOUNT_ID_2 / CF_API_TOKEN_2) from the
env file and never prints them. The backup is used only after the first account's daily allowance runs out.
"""
import base64
import io
import json
import pathlib
import sys
import textwrap
import urllib.error
import urllib.request
import uuid

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
BRAND = HERE / "brand"
MODEL = "@cf/black-forest-labs/flux-2-dev"
SIZE = 1080            # Instagram feed width; poster is 1080 x 1350 (4:5)
BAND = 1350 - SIZE     # copy band under the image
CTA = "START A BRIEF · AWSAVYA.IN"

GROUNDS = {
    "paper": {"bg": "#F5F4F8", "text": "#15131C", "muted": "#57536A", "rule": "#C9C6D2", "logo": "awsavya-logo.png"},
    "ink": {"bg": "#15131C", "text": "#F5F4F8", "muted": "#A19DAD", "rule": "#36323F", "logo": "awsavya-logo-light.png"},
}

STYLE = (
    "Monochrome palette of white, silver and near-black only, premium editorial advertising photography, "
    "sharp detail, generous negative space. The headline is the only text in the image: no other words, "
    "no logos, no brand marks, no people."
)

ADS = {
    "messy": {
        "ground": "paper",
        "headline": "Send us the messy version.",
        "scene": "Top-down view of a pale desk scattered with loose blank paper sheets, a pencil and a closed "
                 "silver laptop, soft daylight and long window shadows.",
        "type": "Large elegant black serif headline across the top",
        "sub": "The spreadsheet, the paper, the group chat. That's enough to start building the version that works.",
    },
    "people": {
        "ground": "ink",
        "headline": "Talk to the people who write the code.",
        "scene": "Two open laptops side by side on a dark minimal desk with two empty chairs, dramatic soft side "
                 "light, screens glowing plain white, near-black room.",
        "type": "Large clean white sans-serif headline across the top",
        "sub": "No account managers in between. Vivek and Yash scope, design and build your product themselves.",
    },
    "website": {
        "ground": "paper",
        "headline": "Your website has one job.",
        "scene": "A silver laptop on a white marble desk in soft morning light, its screen glowing plain white, "
                 "a small succulent beside it.",
        "type": "Large elegant black serif headline across the top",
        "sub": "Make clear what you do and get the right people in touch. We design and build websites that do exactly that.",
    },
    "offline": {
        "ground": "ink",
        "headline": "Built for where the signal drops.",
        "scene": "A smartphone resting on a rock beside a misty mountain road at dusk, its screen glowing plain "
                 "white, hills fading into fog, cinematic.",
        "type": "Large clean white sans-serif headline across the top",
        "sub": "Offline-first Android apps that keep working on the road or the factory floor, and sync when they're back online.",
    },
    "milestones": {
        "ground": "paper",
        "headline": "Working software. Every milestone.",
        "scene": "A smartphone, a tablet and a laptop standing on three white stone plinths of rising height like "
                 "steps, screens plain white, soft studio light, off-white background.",
        "type": "Large bold black sans-serif headline across the top",
        "sub": "Each milestone ends with software you can open and try. At the end, a documented handover of the code.",
    },
    "ai": {
        "ground": "ink",
        "headline": "AI that shows its sources.",
        "scene": "A polished chrome sphere on a black mirror surface with thin beams of white light linking it to "
                 "a few small glowing white cubes, dramatic studio lighting.",
        "type": "Large clean white sans-serif headline across the top",
        "sub": "We build AI that works from your own documents and data, and can show where each answer came from.",
    },
}


class AllAccountsUsedUp(Exception):
    pass


def load_accounts(path):
    """Accounts in order: CF_ACCOUNT_ID/CF_API_TOKEN first, then CF_ACCOUNT_ID_2/CF_API_TOKEN_2, and so on."""
    env = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    accounts, n = [], 1
    while True:
        suffix = "" if n == 1 else f"_{n}"
        acc_id, token = env.get(f"CF_ACCOUNT_ID{suffix}"), env.get(f"CF_API_TOKEN{suffix}")
        if not (acc_id and token):
            break
        accounts.append({"label": f"account {n}", "id": acc_id, "token": token, "used_up": False})
        n += 1
    if not accounts:
        sys.exit("No Cloudflare account in the env file (need CF_ACCOUNT_ID and CF_API_TOKEN).")
    return accounts


def call_model(acc, prompt):
    boundary = uuid.uuid4().hex
    fields = (("prompt", prompt), ("width", "1024"), ("height", "1024"))
    body = "".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n' for k, v in fields
    ) + f"--{boundary}--\r\n"
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acc['id']}/ai/run/{MODEL}",
        data=body.encode(),
        headers={"Authorization": f"Bearer {acc['token']}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    return Image.open(io.BytesIO(base64.b64decode(data["result"]["image"]))).convert("RGB")


def generate(accounts, prompt, retries=2):
    """Use the first account with allowance left; on a daily-limit 429 switch to the next one.
    Server errors (5xx) are retried on the same account."""
    for acc in accounts:
        if acc["used_up"]:
            continue
        for attempt in range(retries + 1):
            try:
                image = call_model(acc, prompt)
                return image, acc["label"]
            except urllib.error.HTTPError as err:
                detail = err.read().decode(errors="replace")
                if err.code == 429:
                    print(f"  {acc['label']}: daily free allowance used up, switching")
                    acc["used_up"] = True
                    break
                if err.code >= 500 and attempt < retries:
                    print(f"  {acc['label']}: server error {err.code}, retrying")
                    continue
                raise RuntimeError(f"{acc['label']}: HTTP {err.code} {detail[:200]}") from None
    raise AllAccountsUsedUp("Every account has used its daily free allowance. It resets at 00:00 UTC (5:30 AM IST).")


def font(name, size, weight=None):
    f = ImageFont.truetype(str(BRAND / name), size)
    if weight:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([weight if a["name"] == b"Weight" else a["default"] for a in axes])
    return f


def compose(scene, ad):
    g = GROUNDS[ad["ground"]]
    poster = Image.new("RGB", (SIZE, SIZE + BAND), g["bg"])
    poster.paste(scene.resize((SIZE, SIZE), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(poster)
    d.line((0, SIZE, SIZE, SIZE), fill=g["rule"], width=2)

    pad = 64
    sub_font = font("archivo.woff2", 31, weight=420)
    lines = textwrap.wrap(ad["sub"], width=60)
    assert len(lines) <= 2, f"sub line too long for the band: {ad['sub']!r}"
    y = SIZE + 38
    for line in lines:
        d.text((pad, y), line, font=sub_font, fill=g["text"])
        y += 42

    logo = Image.open(BRAND / g["logo"]).convert("RGBA")
    logo.thumbnail((260, 44))
    base_y = SIZE + BAND - 44 - logo.height
    poster.paste(logo, (pad, base_y), logo)

    cta_font = font("martian-mono.woff2", 20, weight=500)
    w = d.textlength(CTA, font=cta_font)
    d.text((SIZE - pad - w, base_y + (logo.height - 20) // 2 - 2), CTA, font=cta_font, fill=g["muted"])
    return poster


def main():
    accounts = load_accounts(sys.argv[1])
    print(f"{len(accounts)} Cloudflare account(s) found")
    out = pathlib.Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    keys = sys.argv[3:] or list(ADS)
    for key in keys:
        ad = ADS[key]
        scene_path = out / f"{key}-scene.jpg"
        used = "saved scene"
        if scene_path.exists():  # reuse a generated scene: re-laying out costs no Cloudflare allowance
            scene = Image.open(scene_path).convert("RGB")
        else:
            prompt = f'{ad["scene"]} {ad["type"]} reads "{ad["headline"]}". {STYLE}'
            try:
                scene, used = generate(accounts, prompt)
            except AllAccountsUsedUp as err:
                print(f"{key}: stopped. {err}")
                break
            except RuntimeError as err:
                print(f"{key}: failed. {err}")
                continue
            scene.save(scene_path, quality=92)
        compose(scene, ad).save(out / f"ad-{key}.jpg", quality=92)
        print(f"{key}: saved ad-{key}.jpg ({used})")


if __name__ == "__main__":
    main()
