---
name: curious-mind-video
description: Produce Curious Mind "What If?" YouTube Shorts (9:16) in the approved A4 Cozy Storytelling look with the repository's Code Engine — stickman rig, layered 2.5D environments, dynamic camera, transitions, voice-over, subtitles, music and SFX. Use for writing episode manifests, planning shots, reusing or adding library assets (characters, environments, props, presets, audio), generating narration or raster plates, rendering drafts/finals, and asset approval/registry work in this repo.
---

# Curious Mind video production (Code Engine · A4 Cozy Storytelling)

Adapted from Kaomei Stickman Video Director (MIT; pinned subset in `third_party/kaomei-stickman-video-director/`). Curious Mind rules win on conflict.

## Read first
1. `docs/CURIOUS_MIND_MASTER_GUIDE.md` — brand, story structure, QC. Authoritative.
2. `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` — architecture, episode format, asset policy, test status.
3. `docs/CURIOUS_MIND_CAMERA_TRANSITIONS.md` — one main camera move per shot; transition tempo.
4. A4 style contract: `third_party/kaomei-stickman-video-director/references/cozy-storytelling.md`.
5. For sound: `.../references/autopilot-sound-system.md`; for licences: `.../music-sourcing-and-license.md`.

## Hard rules
- **Never change the master character design silently.** The rig `characters/stick_figure/` is `candidate_master` until the owner approves. Exactly two arms, two legs; expressions change facial marks only. No Milo traits.
- **Reuse before creating.** Run `node pipeline/src/cli.mjs registry list`. New assets go in as `draft`; only the owner approves (`registry approve <id> --by "<owner>"`). Never edit an `approved` file — make a `_v02`.
- **No silent regeneration.** Generators refuse to overwrite media or receipts. Paid generation (image/TTS) requires the owner's explicit authorisation per batch; pass `--allow-network` only then. Never ask for API keys in chat.
- **Narration is never time-stretched.** Fit pictures to speech (`"duration": "auto"`). One frozen narrator voice per video; no style/emotion instructions to TTS.
- **No text inside artwork.** Words appear only as subtitles. Metaphor icons are allowed on their timed beat only.
- **Do not overclaim.** A render report is technical evidence, not creative acceptance. Say what was not watched/listened to. The `espeak-ng` voice is a test fixture — never deliver it as narration.
- Say "2.5D parallax", never "3D", for layered camera moves.
- Every third-party audio file used must appear in the render's `CREDITS.txt`; CC BY items must be credited in the video description.

## Workflow
1. Story: script per Master §6–7 (hook in the first 2–3 s, one idea per line). Get approval.
2. Storyboard: `docs/templates/STORYBOARD_TEMPLATE.md`; A4 default = each new narrative segment gets a recognisable new setting; plan cuts (direction, prop, wipe, time jump).
3. Manifest: copy `episodes/ep000_pipeline_smoke_test/episode.json` to `episodes/epNNN_<slug>/episode.json`. Anchor voice lines and SFX to scenes.
4. Voice: `node pipeline/src/cli.mjs voice <ep> --engine gemini --model <tts-model> --voice <Name> --allow-network` (after authorisation) or import WAVs from the owner's chosen service into `audio/vo/` with a receipt.
5. Check: `validate <ep>` → `stills <ep> --times …` (look at them) → `render <ep> --draft --seconds 20`.
6. Owner reviews the ~20 s sample (picture + sound). Only then `render <ep>`.
7. Review `output/final/contact-sheet.png`, `report.json`, play the MP4; run Master §12 QC; deliver MP4 + SRT + CREDITS.txt.

## Shot vocabulary (presets)
- Camera (`assets/presets/camera.json`): `static, push_in, push_in_fast, emotional_close, pull_back, pull_back_reveal, snap_zoom_in/out, zoom_in_slow, pan_left/right, truck_left/right, tilt_up/down, tilt_reveal_down, dolly_in/out, aerial_descend/rise, crane_up/down, orbit_left/right, dutch_tilt, whip_out_left, handheld, push_in_handheld`; tracking = `camera.follow {actor, axis}`.
- Close-up: `zoom` 3–3.5 on head height (`y ≈ actor.y − 350·scale`). Wide: zoom 1 on the environment's `center`/`wide` anchor.
- Transitions (`assets/presets/transitions.json`): `whip_pan, smash_cut, snap_zoom, push_through, push, object_wipe, iris, match_cut, cut`; `dip` only for emotional beats/time jumps.
- Lighting: `warm_morning, golden_afternoon, cozy_lamp_evening, soft_overcast, night_window_glow, neutral_soft`.
- Poses/expressions: see `characters/stick_figure/reference/*.png`.

## Adding assets
- Environment (vector): `environments/<category>/<name>/environment.json` with `world`, `floor_y`, `anchors`, `layers[{id, depth, shapes}]` and one `{"slot":"actors"}`. Then `sheets environments` and `registry scan`.
- Environment (raster): request JSON → `image <request> --allow-network` → `key` for alpha layers → reference PNGs as `{"type":"image","path":"layers/x.png",…}` shapes. Keep the receipt next to the PNG.
- Prop: `assets/props/<name>/prop.json` (`size`, `anchor`, `grip`, `shapes`, optional `state` shapes).
- Audio: see `assets/audio/README.md`.

## Commands
`node pipeline/src/cli.mjs doctor | validate | stills | render | voice | image | key | sheets | registry` — run `cd pipeline && npm ci` once, `npm test` after code changes.
