# AutoPostInsta: AWSAVYA Instagram ads

The goal is to have AI make an AWSAVYA advertising image and caption every day and post it to Instagram automatically, on free tools.

## What's here
| Path | What it is |
|---|---|
| `awsavya_ads.py` | Makes the ads. Cloudflare Flux 2 Dev draws the scene and headline. Code then adds the copy line, the real AWSAVYA logo and the call to action "START A BRIEF · AWSAVYA.IN" in the site's fonts. |
| `brand/` | Logos (`awsavya-logo.png` for light ads, `awsavya-logo-light.png` for dark ads) and fonts (Archivo, Martian Mono; both OFL) copied from the awsavya.in site. |
| `ads/` | The first six finished ads (`ad-*.jpg`, 1080×1350), their raw AI scenes (`*-scene.jpg`) and `AWSAVYA-ad-copy.md` (captions and hashtags). |

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
```
Use Workers AI-only tokens. The script never prints the values.

## Decisions so far
- **Image model:** Cloudflare Workers AI **Flux 2 Dev**. In testing it beat Flux 1 Schnell, Leonardo Lucid Origin, Leonardo Phoenix and Pollinations, which gave watermarks, garbled text and broken objects.
- **Text the AI draws:** the headline only. The brand name, copy line and CTA are always added by code, because the AI misspelled "AWSAVYA".
- **Free limit:** 10,000 units per account per day, reset at 00:00 UTC (5:30 AM IST). Flux 2 Dev uses a large share per image, so it's fine for about one ad a day plus retries.
- **Brand rules (from the awsavya.in project):** a white/silver/ink palette and **no purple or violet**. The four portfolio items (TripSplit, Build2Buzz, Har Apparels, QuicklyCart) are the founders' own built projects, never client work. Never invent clients, metrics, prices, testimonials or partner logos. Ad copy must only claim what awsavya.in says.

## Next steps
1. Instagram setup (done by the owner): a Professional account, a Meta developer app and an access token.
2. Posting script: Instagram Graph API, `POST /{ig-user-id}/media` (needs a public `image_url`), then `/media_publish`.
3. Hosting the images at a public URL (for example GitHub Pages).
4. Daily captions from AI (for example the Gemini free tier), with a check that blocks invented claims.
5. Scheduling with GitHub Actions on a daily cron, with approval mode on for the first weeks.
