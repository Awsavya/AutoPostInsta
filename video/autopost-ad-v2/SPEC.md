# SPEC v2: AWSAVYA Instagram auto-posting reel (with sound)

GOAL:    A busy shop owner feels the daily posting chore, sees the AutoPostInsta app make and schedule the post, and taps awsavya.in.
OUTPUT:  HyperFrames, 1080 x 1920, 30 fps, 16 s (480 frames), stereo AAC.
TIME:    120 BPM, 15 frames a beat, 60 frames a bar (2 s). Every scene is a whole number of beats; every cut lands on a beat.
PERSONALITY: Energetic, restrained by the brand. Enter expo.out 0.25-0.4 s; exit power3.in 0.2-0.3 s (40% shorter);
         pops back.out(1.7) on scale only; camera punches 3-6% on beats. One hero per frame.
LOOK:    unchanged brand system: paper #F5F4F8, ink #15131C, graphite #57536A, ONE accent #FFC83D. Archivo 800 display, Martian Mono labels.
         Real AutoPostInsta UI rebuilt at 1.6x; a real poster in the app's layout; a week of real-layout posters.
STORY (hook -> agitate -> payoff -> proof -> CTA, message-matched: "posting yourself" -> "on autopilot"):
  0.0-2.0   HOOK (bar 1). Yellow. "Still posting on Instagram yourself?" readable on frame 0. Beat 0.5: ink bar wipes behind
            "yourself?" (word turns yellow). Beat 1.0: punch-in. 1.5-2.0: the bar floods the frame. SOUND: near silence, a clock ticking each beat.
  2.0-6.0   AGITATE (bars 2-3). Ink. Four chore cards fall onto a pile, landing on 2.5, 3.0, 3.25, 3.5 (speeding up; thud each).
            "Every. Single. Day." slams on 4.0 / 4.5 / 5.0 with a camera punch each. 5.5-6.0 BREAK: total stillness and silence,
            then a whip up. SOUND: tick + soft kick, low drone rising; a riser 5.0-6.0 into the drop.
  6.0-8.0   PAYOFF (bar 4). THE DROP: full groove starts as the real Idea card lands. "Just type the idea." The idea types
            itself (key ticks); cursor clicks "Write it with AI" on beat 7.5 with a punch-in. Zoom through.
  8.0-10.0  PAYOFF (bar 5). The poster builds on the eighth notes; "Made by AI" sticker pops on beat 9.0 (pop).
  10.0-12.5 PROOF. Publish card; click on beat 10.5; "Scheduled for 28 Nov, 8:00 am." on 11.0; seven day posters land on
            the eighths 11.25-12.0, each checked (soft pops).
  12.5-16.0 CTA. Logo wipes in and settles on beat 13.0; "Your Instagram, on autopilot."; yellow "TALK TO US · AWSAVYA.IN"
            pops on 13.5 and holds 2.5 s. Music resolves to the tonic at 14.0 and fades over the last second.
SOUND:   all synthesized for this film (numpy): C-major/A-minor groove at 120 BPM (C-G-Am-F), kick, clap, hats, bass, pluck arp;
         layers enter one per bar after the drop; SFX from filtered noise (whoosh on cuts, thuds, key ticks, clicks, pops).
         No chimes or dings. Mix: music bed, SFX 3-6 dB over it; loudness -14 LUFS, true peak <= -1.5 dBTP.
BANNED:  as v1, plus: every scene entering the same way; stacked accents louder than +6 dB at a cut; text moving while read.
QA:      0.0, 0.9, 2.6, 4.6, 5.7, 6.5, 7.6, 9.3, 11.6, 14.5; sync-check on cuts; audio loudness.
