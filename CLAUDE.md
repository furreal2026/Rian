# Rian — Curious Mind "What If?" project

## Trigger: "jalankan proyek What If"

When the owner says they want to run the What If project ("mau menjalankan proyek what if", "jalankan proyek What If", or similar), do this without asking again:

1. Update the repo: `git fetch origin main` and bring the working branch up to date with `origin/main` (merge, never reset or discard local work).
2. Load the production standards before working:
   - `docs/CURIOUS_MIND_MASTER_GUIDE.md` (source of truth), `docs/CURIOUS_MIND_CAMERA_TRANSITIONS.md`, `docs/CURIOUS_MIND_ENVIRONMENT.md`
   - `docs/decisions/CHANGELOG.md` (approved decisions), `docs/production/` (episode briefs/storyboards)
3. Use the established production setup below (character, camera, transitions, environment format) for every new shot or episode.

## Character: Rian

- Main character is **Rian**, the Curious Mind stick figure: round white head, red T-shirt, black outline, separate arms/hands/legs, no hair, no accessories, deadpan default expression. Never use Milo.
- Rig: `pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json` (views `front`, `side`; joint pivots; `character_name: Rian`), poses in `rig/poses.json`, expressions `deadpan`, `deadpan_up`, `skeptical`, `shocked`, `smug`, procedural walk cycle.
- Keep one character scale per scene (config `character.height`) and continuous position across shots.

## Camera style

- One main camera move per shot, motivated: tilt (`y` keys), pan (`x`), push / pull back (`zoom`), roll (`rot`), drift modifier, tracking modifier (lagged follow), cut = shot boundary.
- 2.5D layer parallax (never call it full 3D): Layer 1 foreground 1.5, Layer 2 action plane 1.0, Layer 3 background 0.35, Layer 4 far background 0.15.
- Keep the camera inside the painted plates (check with `python -m tools.render plate-spec` and the render report `frames_with_plate_holes`).

## Transitions

- `cut_on_action` (cut placed on a character event), `whip_pan` (sub-frame motion blur), `leaf_wipe` (object wipe with `fx/leaf_wipe.png`), plain `cut`. Tempo per Camera guide §6 (0.15–0.80 s). Avoid slow fades/dissolves.

## Environment format

- Per location: `assets/environment/<location>/manifest.json` + `README.md`; plates `<location>_bg_far.png` (L4), `<location>_bg.png` (L3), `<location>_mid.png` (L2), `<location>_fg.png` (L1), `fx/`.
- PNG RGBA 8-bit sRGB, lowercase snake_case. Originals go to `source/` unchanged; conversions are new files (`keyed/…_rgba.png`), QC previews in `qc/`.
- Plates on a flat key colour: `python -m tools.render ingest-plates --config … --inbox …` (sampled key, Lab Delta-E, border-connected only, graded edges, edge-only despill; declared regions in `key_regions.json`). Then `place-plates` and `stack-preview`.
- Courtyard decision: wall, gate, bench, fountain and floor share Layer 2 so the wall/floor seam (64% height) never splits.

## Render

- Episode code: `pilot/PILOT_01_STOP_TIME/` (template for new episodes); shared tools: `tools/render/`.
- `python tools/render/render.py <episode> [--config …] [--test-plates]` (Windows: `tools\render\render_pilot.bat`): 1920×1080, 24 fps, H.264 MP4, automatic ffprobe QC + frame extraction.
- Tests: `python -m unittest discover -s pilot/PILOT_01_STOP_TIME/tests -t .`

## Working rules

- No commit, push, PR or merge without the owner's explicit permission for that action.
- Do not change approved decisions; record new ones in `docs/decisions/CHANGELOG.md`. Report conflicts instead of resolving them silently.
- Do not create replacement environments or final assets that are not approved; generated test assets stay in `output/` and are labelled TEST.
- Report with evidence (ffprobe numbers, extracted frames); never claim a feature works without testing it.
- Reply to the owner in Indonesian.
