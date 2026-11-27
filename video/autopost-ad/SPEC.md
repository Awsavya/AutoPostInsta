# SPEC: AWSAVYA Instagram auto-posting reel

GOAL:    A busy shop owner understands, in 15 s and muted, that AWSAVYA can build them an app that makes and posts their Instagram ad every day, and taps through to awsavya.in.
OUTPUT:  HyperFrames, 1080 x 1920 (Instagram Reel), 30 fps
TIME:    15 s x 30 = 450 frames. No music source on this machine: delivered silent (sound plan below for when a track is added).
LOOK:    The brand's own poster system, not a template.
         ground paper #F5F4F8; ink #15131C; graphite #57536A; card sheet #FCFBFE with 1 px #DEDCE5 border, radius 28 px;
         ONE accent, signal yellow #FFC83D: the hook ground, the highlighted word, labels and the CTA button only.
         Display: Archivo 800, 112 px hook (5.8% of height), -2% tracking; body Archivo 500 40-48 px; labels Martian Mono 600 26-30 px caps.
         Medium: the real AutoPostInsta app UI (its labels, fields and buttons rebuilt at 1.6x) and a real poster in the app's layout.
         Shadows: 0 24 px 60 px rgba(21,19,28,.18) on cards that float; no grain, no glow.
OBJECTS: The app's "01 Idea" card (label "What should this post be about?", textarea, buttons "Give me an idea" / "Write it with AI");
         the poster (FOR BAKERIES label, headline, croissant photo, offer line, logo, yellow button); the Publish card
         (Schedule / Post now / Add to queue / Buffer draft, Publish button, status "Scheduled for 28 Nov, 8:00 am.");
         a cursor arrow at 84 px; a week of seven poster thumbnails with check marks.
MOTION:  enter expo.out / power4.out 0.3-0.5 s; camera and floods power2.inOut 0.4-0.65 s; exits power3.in, 40% shorter than entrances;
         words stagger 0.08 s; list items 0.12 s; chips land with back.out(1.6) on scale only.
SHOTS:   0.0-2.4  HOOK. Yellow ground, "Still posting on Instagram yourself?" fully on screen at frame 0 (thumbnail). 0.8 s: an ink bar wipes
                  behind "yourself?" and the word turns yellow. 1.9 s: the ink bar grows past the frame (object becomes the world).
         2.4-5.0  TENSION. Ink ground. Four chore cards drop into a loose pile, 0.35 s apart: "Think of an idea", "Make the image",
                  "Write the caption", "Post it on time". 3.8 s: "Every. Single. Day." slams in word by word in yellow. 4.7 s: whip up.
         5.0-7.6  REVEAL. Paper ground, line "Just type the idea." The real Idea card at 1.6x: the textarea types
                  "Fresh croissants for my bakery", the cursor enters, clicks "Write it with AI" (button presses, label "Writing…").
         7.6-10.0 PAYOFF. The poster assembles in the app's layout: label pops, headline per word, photo wipes in, offer line, button pops,
                  then a yellow "Made by AI" sticker.
         10.0-12.6 PROOF. The Publish card: Schedule selected, cursor clicks Publish, status turns green "Scheduled for 28 Nov, 8:00 am.",
                  then seven day thumbnails fill with check marks under "Posted on time. Every day."
         12.6-15.0 CLAIM + END. Paper ground. Logo wipes in centred at 300 px, "Your Instagram, on autopilot." per word,
                  the yellow "TALK TO US · AWSAVYA.IN" button lands at 13.6 s and holds to the end (1.4 s+).
         Every word and the product stay inside x 120-888, y 288-1248 (Reels safe zone).
SOUND:   (when a track exists) a bright minimal pulse ~120 bpm entering at 2.4 s; near-silence on the hook; key ticks on the typing;
         one click per cursor click; pop on each chip; riser into the end-card button.
BANNED:  dark void with floating elements; glow; purple/blue gradients; three cards in a row; a title over a dimmed screenshot;
         logo docked in a corner; invented dashboards (every UI piece is the app's real label set); every element fading up;
         titles drifting after they land; invented clients, numbers or results.
QA:      0.0 (thumbnail reads), 1.2, 2.6, 4.3, 6.4, 7.2, 9.4, 11.0, 12.2, 14.5.
