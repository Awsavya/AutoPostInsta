# Where v3 stopped (2026-11-27)

Paused at the owner's request, mid-build.

Done:
- Research + design workflow: plan in `final-plan.json` ("8:00 AM. Every Day.", 18 s, 9 shots, 24 registry presets);
  shared contract in `SPEC.md`.
- Project scaffold: `index.html` mounts six scenes (hook, who, dive, app, everyday, endcard); 24 presets installed.
- Voiceover: `make_vo.py` -> `assets/audio/vo-0..8.wav` + `vo.json` (ElevenLabs Sarah, AWSAVYA as phonemes ˈʌvsəvjɛ,
  natural pace, placed on the beats).
- Soundtrack: `make_audio.py -7.3` -> `assets/audio/soundtrack.wav` (-14 LUFS, music + 30 SFX + voice, ducked).

In progress when stopped:
- Build workflow (six scene builders -> independent review -> fix). Some scene files may be partly built; check each
  `compositions/<scene>.html` (stubs say "(to build)"). Resume with:
  Workflow({scriptPath: "C:/Users/vivek/.claude/projects/D--Projects-AutoPostInsta/68fe66cd-dfc2-44b4-89bb-8deb34abcbad/workflows/scripts/reel-v3-build-wf_895ccab5-b4a.js", resumeFromRunId: "wf_895ccab5-b4a"})
  (finished agent calls replay from cache; unfinished ones run again).

Still to do after the build:
1. Root integration: grain-overlay at opacity 0.06 over everything; `<audio id="soundtrack" src="assets/audio/soundtrack.wav">`.
2. Adversarial whole-film review (ad clarity, craft, truth/brand, sync) -> fixes.
3. Render, loudness/sync check, send.
