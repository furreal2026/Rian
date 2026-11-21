# Audio library

`library/` holds licensed recordings exported (unchanged) from the Kaomei Stickman Video Director audio library, with per-file source, licence, original SHA-256 and acquisition evidence:

- `library/audio-selection.json` — machine-readable list; episodes reference audio by `id`.
- `library/CREDITS.md` — required credit text. Renders write the credits actually used to `output/*/CREDITS.txt`.
- `library/licenses/`, `library/evidence/` — licence texts and source snapshots (inert `.html.txt`).

Current set (23): 2 music tracks (CC BY 4.0), whooshes, footsteps, paper/book, phone, drink, kitchen, door, boing, bubble pop, record scratch (CC BY 3.0), rimshot (CC BY 3.0), UI close, outdoor ambience loop, birds, a short jingle.

## Adding more

1. Prefer the upstream library (already rights-checked): clone the pinned upstream commit, then run its exporter into a scratch folder, e.g. `node scripts/audio-library.mjs search footstep` and `… export --ids <ids> --out /tmp/new-audio`.
2. Merge the new files/evidence into `library/` and append the entries to `audio-selection.json` and `CREDITS.md`. Never overwrite an existing file with different bytes.
3. External sources: record source URL, author, licence and date (see `third_party/kaomei-stickman-video-director/references/music-sourcing-and-license.md`). "Free" without a licence is not enough.

Project-original audio (narration, recorded Foley) lives with each episode (`episodes/<id>/audio/`), with a `.request.json` receipt for generated speech.
