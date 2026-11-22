# AutoPostInsta: AWSAVYA Instagram ads

The goal is to have AI make an AWSAVYA advertising image and caption every day and post it to Instagram automatically, on free tools.

## What's here
| Path | What it is |
|---|---|
| `awsavya_ads.py` | Makes the ads. Cloudflare Flux 2 Dev draws the scene and headline. Code then adds the copy line, the real AWSAVYA logo and the call to action "START A BRIEF · AWSAVYA.IN" in the site's fonts. |
| `brand/` | Logos (`awsavya-logo.png` for light ads, `awsavya-logo-light.png` for dark ads) and fonts (Archivo, Martian Mono; both OFL) copied from the awsavya.in site. |
| `ads/` | The first six finished ads (`ad-*.jpg`, 1080×1350), their raw AI scenes (`*-scene.jpg`), `captions.json` (caption and alt text per ad) and `AWSAVYA-ad-copy.md` (the same copy, for reading). Served publicly at `https://awsavya.github.io/AutoPostInsta/ads/` through GitHub Pages. |
| `post_buffer.py` | **The posting route in use.** Sends an ad to Buffer, which publishes it to Instagram. No Facebook needed. Setup: [SETUP-BUFFER.md](SETUP-BUFFER.md). |
| `post_instagram.py` | Alternative route straight through Meta's Instagram API. Needs a Facebook login to register as a Meta developer. Setup: [SETUP-INSTAGRAM.md](SETUP-INSTAGRAM.md). |

## Running it
```
python awsavya_ads.py "%USERPROFILE%\OneDrive\Documents\.env" ads [ad_key ...]
```
- If an ad's `*-scene.jpg` already exists in the output folder, the script reuses it and only redoes the layout, which uses no Cloudflare allowance. Delete the scene file to get a new image.
- Ad keys: `messy`, `people`, `website`, `offline`, `milestones`, `ai`. The copy for each is in the `ADS` dictionary in the script.

## Secrets
They stay in a local env file outside this folder (`%USERPROFILE%\OneDrive\Documents\.env`) and are never committed:
```
CF_ACCOUNT_ID=...      # own Cloudflare account, used first
CF_API_TOKEN=...
CF_ACCOUNT_ID_2=...    # optional backup account, used only after account 1's daily allowance runs out
CF_API_TOKEN_2=...
IMAGE_BASE_URL=https://awsavya.github.io/AutoPostInsta/ads
BUFFER_API_KEY=...     # Buffer > Settings > API > Personal Access, 1-year expiry
BUFFER_CHANNEL_ID=...  # optional; printed by `python post_buffer.py channels`
```
Use Workers AI-only Cloudflare tokens. None of the scripts print secret values.

## Decisions so far
- **Image model:** Cloudflare Workers AI **Flux 2 Dev**. In testing it beat Flux 1 Schnell, Leonardo Lucid Origin, Leonardo Phoenix and Pollinations, which gave watermarks, garbled text and broken objects.
- **Text the AI draws:** the headline only. The brand name, copy line and CTA are always added by code, because the AI misspelled "AWSAVYA".
- **Free limit:** 10,000 units per account per day, reset at 00:00 UTC (5:30 AM IST). Flux 2 Dev uses a large share per image, so it's fine for about one ad a day plus retries.
- **Brand rules (from the awsavya.in project):** a white/silver/ink palette and **no purple or violet**. The four portfolio items (TripSplit, Build2Buzz, Har Apparels, QuicklyCart) are the founders' own built projects, never client work. Never invent clients, metrics, prices, testimonials or partner logos. Ad copy must only claim what awsavya.in says.

- **Posting:** through **Buffer's free API**, because registering as a Meta developer needs a Facebook login. Buffer's free plan holds 10 queued posts per channel and allows 5 hashtags per Instagram post. Posts carry Instagram's AI info label (`isAiGenerated`).
- **Hosting:** GitHub Pages on this public repo. Instagram and Buffer fetch images from public URLs, and nothing secret is in the repo.

## Next steps
1. Buffer setup (done by the owner): a Professional Instagram connected to Buffer, and an API key in the env file. Then `python post_buffer.py channels` and a first real post.
2. Daily captions from AI (for example the Gemini free tier), with a check that blocks invented claims and keeps to 5 hashtags.
3. Scheduling with GitHub Actions on a daily cron (secrets in GitHub Secrets), with approval mode on for the first weeks.
