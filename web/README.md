# AutoPostInsta web app

A private page for making an AWSAVYA Instagram ad and posting it through Buffer:
idea → AI copy → AI image (or your own photo) → poster preview with checks → post now, schedule, queue or Buffer draft.

It runs free on **Cloudflare Workers**:
- The page and API are one worker (`src/worker.js`, `public/`), behind a password.
- The poster (scene, copy line, real logo, CTA) is drawn in the browser on a canvas, in the brand fonts.
- Finished images go into **Workers KV** and are served publicly at `/img/<id>.jpg` so Buffer can fetch them.
- Buffer does the scheduling, so nothing has to run on a timer.
- AI copy (Llama 3.3 70B) and images (Flux 2 Dev) come from Workers AI, with the backup account used when the first one's free allowance runs out.

## Run locally
```
python web/scripts/make_dev_vars.py      # writes web/.dev.vars from your env file (git-ignored)
npx wrangler@4.166.0 dev --config web/wrangler.jsonc --local
```
Open http://localhost:8787. Publishing only works on the live site, because Buffer can't fetch images from your computer.

## Deploy (first time and every update)
```
npx wrangler@4.166.0 login               # once: approve in the browser with your own Cloudflare account
python web/scripts/deploy.py             # creates KV once, deploys, uploads secrets from your env file
```
The script prints the live `*.workers.dev` address. The password is `AUTOPOST_APP_PASSWORD` in your env file.

## Free-plan limits that matter
- Workers: 100,000 requests a day. KV: 1,000 writes a day (one per published image) and 1 GB.
- Workers AI: 10,000 units a day per account, which is a handful of Flux 2 Dev images.
- Buffer free plan: 10 queued posts, 5 hashtags per Instagram post.
