# SPEC v3: "8:00 AM. Every Day." (AWSAVYA daily-Instagram-ad service)

The full, authoritative shot plan is `final-plan.json` in this folder (shots S1-S9 with exact timings, text, motion,
transitions, presets, voiceover, captions, sound). This file is the shared contract every scene builder follows.

OUTPUT: HyperFrames, 1080 x 1920, 30 fps, 18.0 s. 120 BPM: a beat every 0.5 s, cuts land on beats.

SCENES (one sub-composition each; a scene's clock starts at 0 at its host's data-start):
| host / file                      | abs start-end | shots  |
|----------------------------------|---------------|--------|
| hook     compositions/hook.html  | 0.0 - 2.0     | S1     |
| who      compositions/who.html   | 2.0 - 3.5     | S2 (painted plate assets/riya-cut.mp4 + "For your [trade]" strip) |
| dive     compositions/dive.html  | 3.5 - 5.0     | S3     |
| app      compositions/app.html   | 5.0 - 13.0    | S4 S5 S6 S7 (one continuous camera through the real app) |
| everyday compositions/everyday.html | 13.0 - 15.0 | S8    |
| endcard  compositions/endcard.html | 15.0 - 18.0  | S9     |
Scene-local time = abs time - scene start (e.g. S6 8.5 s abs = app.html local 3.5 s).

TOKENS: paper #F5F4F8, ink #15131C, graphite #57536A, ONE accent signal yellow #FFC83D. Yellow is always a FILLED shape
with ink on it (never yellow text on paper). No purple anywhere: if a preset uses --brand / --accent / --accent-2 or a
violet fallback (#c5a3ff), set them to #FFC83D or ink. Fonts (local only, never Google/Inter):
  @font-face { font-family: "Archivo"; src: url("assets/fonts/archivo.woff2") format("woff2"); font-weight: 100 900; }
  @font-face { font-family: "Martian Mono"; src: url("assets/fonts/martian-mono.woff2") format("woff2"); font-weight: 100 800; }
Archivo 800 display (tracking -0.025em, left-aligned on x = 65), Martian Mono for chips/labels (never under 42 px).
Grain: grain-overlay at ~0.06 is applied once over the whole film by the root (index.html) - do NOT add it per scene.

SAFE ZONE (Instagram Reels): every word, the product and the CTA inside x 65-1015, y 270-1248. Below 1248 only
texture/background. Nothing important in the top 270 px.

REAL APP STRINGS (exact; never invent UI): "01 Idea", "What should this post be about?", "Give me an idea",
"Write it with AI", "02 Words", "Who it's for", "Headline", "Offer line", "03 Image", "04 Preview", "05 Publish",
"Schedule", "Post now", "Add to queue", "Buffer draft", "Date and time", "Add Instagram's \"AI info\" label",
"Publish", "Scheduled for 28 Nov, 8:00 am.". Poster: yellow chip "FOR BAKERIES", headline "Fresh bakes. Posted before
you open.", offer line "We build you an app that makes and posts a fresh Instagram ad every morning.", logo, yellow
button "TALK TO US · AWSAVYA.IN". Assets: assets/poster-bakery.jpg (full poster), assets/poster-photo.jpg (its photo),
assets/day-1..7.jpg (example posters, small; make_poster.py re-exports bigger ones), assets/awsavya-logo.png (pixel
wordmark, dark on light), assets/awsavya-logo-light.png.

TRUTH: never invent clients, numbers, results; the stack in S8 is labelled "EXAMPLE WEEK"; Riya never uses the app.

MOTION: springs/expo.out arrivals, power3.in exits (40% shorter), one hero per frame, titles land then hold still,
every scene enters/exits per the plan's transitions (no fades to black between scenes). Seek-safe GSAP only; register
window.__timelines["<id>"]; no Date.now/Math.random/timers/repeat:-1.

AUDIO is mixed by the root (voice, music, SFX) - scenes contain NO <audio>.
