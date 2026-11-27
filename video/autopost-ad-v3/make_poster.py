"""Draw posters exactly like the app's canvas (web/public/app.js draw()) for use inside the reel:
the hero bakery poster, its photo on its own (so the reel can assemble the poster piece by piece),
and a week of small posters with different photos and headlines."""
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
BRAND = HERE.parents[1] / "brand"
SRC = pathlib.Path(r"C:\Users\vivek\AppData\Local\Temp\claude\f034da723bfc707e\68fe66cd-dfc2-44b4-89bb-8deb34abcbad\scratchpad")
W, H, TOP, BOTTOM, PAD = 1080, 1350, 350, 1060, 64
PAPER, INK, ACCENT = "#F5F4F8", "#15131C", "#FFC83D"
SUB = "We build you an app that makes and posts a fresh Instagram ad every morning."
CTA = "TALK TO US · AWSAVYA.IN"


def font(name, size, weight):
    f = ImageFont.truetype(str(BRAND / name), size)
    f.set_variation_by_axes([weight if a["name"] == b"Weight" else a["default"] for a in f.get_variation_axes()])
    return f


def wrap(d, text, f, width):
    lines, line = [], ""
    for w in text.split():
        t = f"{line} {w}".strip()
        if d.textlength(t, font=f) > width and line:
            lines.append(line)
            line = w
        else:
            line = t
    return lines + [line]


def photo(path, y_frac, x_frac=0.0, w_frac=1.0):
    """A 1080x710 crop of the photo: w_frac of its width, starting x_frac across and y_frac down."""
    src = Image.open(path).convert("RGB")
    w = int(src.width * w_frac)
    h = int(w * (BOTTOM - TOP) / W)
    x, y = int(src.width * x_frac), int((src.height - h) * y_frac)
    return src.crop((x, y, x + w, y + h)).resize((W, BOTTOM - TOP), Image.LANCZOS)


def poster(pic, headline, audience="BAKERIES"):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    img.paste(pic, (0, TOP))
    mono = font("martian-mono.woff2", 22, 600)
    label = f"FOR {audience}"
    lw = d.textlength(label, font=mono) + 32
    d.rounded_rectangle((PAD, 52, PAD + lw, 96), 22, fill=ACCENT)
    d.text((PAD + 16, 74), label, font=mono, fill=INK, anchor="lm")
    for size in (86, 78, 70, 62):
        head = font("archivo.woff2", size, 800)
        lines = wrap(d, headline, head, W - PAD * 2)
        if len(lines) <= 2:
            break
    for i, line in enumerate(lines):
        d.text((PAD - 3, 122 + i * size * 1.04), line, font=head, fill=INK)
    sub = font("archivo.woff2", 32, 450)
    for i, line in enumerate(wrap(d, SUB, sub, W - PAD * 2)[:2]):
        d.text((PAD, BOTTOM + 36 + i * 43), line, font=sub, fill=INK)
    row = H - 48 - 60
    logo = Image.open(BRAND / "awsavya-logo.png").convert("RGBA")
    logo = logo.resize((int(logo.width * 40 / logo.height), 40), Image.LANCZOS)
    img.paste(logo, (PAD, row + 10), logo)
    cta = font("martian-mono.woff2", 22, 600)
    bw = d.textlength(CTA, font=cta) + 48
    d.rounded_rectangle((W - PAD - bw, row, W - PAD, row + 60), 30, fill=ACCENT)
    d.text((W - PAD - bw + 24, row + 31), CTA, font=cta, fill=INK, anchor="lm")
    return img


assets = HERE / "assets"
hero_pic = photo(SRC / "reel" / "1-problem.jpg", 0.0)
hero_pic.save(assets / "poster-photo.jpg", quality=92)
poster(hero_pic, "Fresh bakes. Posted before you open.").save(assets / "poster-bakery.jpg", quality=92)

WEEK = [
    (SRC / "reel" / "1-problem.jpg", (0.0, 0.0, 1.0), "Fresh bakes. Posted before you open."),
    (SRC / "bake-1.png", (0.5, 0.07, 0.85), "Warm loaves, ready by noon."),
    (SRC / "bake-2.png", (0.5, 0.0, 1.0), "Cake of the day is out."),
    (SRC / "bake-3.png", (0.5, 0.0, 1.0), "Butter croissants, just baked."),
    (SRC / "bake-4.png", (0.5, 0.0, 1.0), "Cinnamon rolls, still warm."),
    (SRC / "bake-5.png", (0.5, 0.0, 1.0), "Weekend cupcakes are here."),
    (SRC / "bake-3.png", (0.3, 0.15, 0.7), "Sunday bake. Come early."),
]
EVERYDAY = (1, 2, 3, 5)  # S8 "EXAMPLE WEEK" stack: hero, loaves, cake, cinnamon rolls (never day-6, purple frosting)
for i, (path, (y, x, w), head) in enumerate(WEEK, 1):
    full = poster(photo(path, y, x, w), head)
    full.resize((270, 338), Image.LANCZOS).save(assets / f"day-{i}.jpg", quality=88)
    if i in EVERYDAY:
        full.resize((720, 900), Image.LANCZOS).save(assets / f"everyday-day-{i}.jpg", quality=90)
print("posters written")
