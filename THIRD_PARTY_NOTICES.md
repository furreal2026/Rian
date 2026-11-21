# Third-party notices

Every third-party component in this repository keeps its own licence. Project-original files are not covered by these licences.

| Component | Location | Licence | Attribution required in published videos? |
|---|---|---|---|
| Kaomei Stickman Video Director — selected reference documents (unmodified copies) and `gemini-media.mjs` | `third_party/kaomei-stickman-video-director/` | MIT (`third_party/kaomei-stickman-video-director/LICENSE`) | No (keep the licence file with the copies) |
| Adapted Gemini adapter | `pipeline/src/lib/gemini.mjs` | MIT (derived from the file above; header notes the changes) | No |
| A4 Cozy Storytelling drawing grammar | reimplemented in `characters/stick_figure/` and `pipeline/src/lib/character.mjs` | Original code; style direction from the MIT-licensed upstream reference | No |
| Nunito font (static weight 900 instance) | `assets/fonts/Nunito.ttf` | SIL Open Font License 1.1 (`assets/fonts/OFL-Nunito.txt`) | No |
| Music: "Morning", "Carefree" — Kevin MacLeod (incompetech.com) | `assets/audio/library/audio/music/` | CC BY 4.0 | **Yes** — use the generated `CREDITS.txt` in each render's output folder |
| SFX: Kenney, artisticdude, Owlish Media, isaiah658, Kresiek, rubberduck, Aeva, Kenney jingles | `assets/audio/library/audio/` | CC0 1.0 | No (credit optional) |
| SFX: "Scratch Speed" — Racche; "bah-dum" — Kevin | `assets/audio/library/audio/` | CC BY 3.0 | **Yes** (included in `CREDITS.txt` when used) |

Per-file sources, original hashes, licence texts and acquisition evidence: `assets/audio/library/CREDITS.md`, `audio-selection.json`, `evidence/`, `licenses/`.

Not redistributed: Kaomei's showcase videos/GIFs, B-style example art, the remaining ~750 audio files and other fonts. Fetch them from the upstream repository (pinned commit in `third_party/kaomei-stickman-video-director/UPSTREAM_COMMIT`) if ever needed.

npm dependency: `@napi-rs/canvas` 0.1.100 (MIT), installed via `pipeline/package-lock.json`, not vendored.
