# Curious Mind Code Engine

Layered 2.5D renderer for Curious Mind Shorts in the A4 Cozy Storytelling look. Design and workflow: [`docs/CURIOUS_MIND_VIDEO_PIPELINE.md`](../docs/CURIOUS_MIND_VIDEO_PIPELINE.md).

## Requirements
- Node.js 20+ (tested on 22)
- FFmpeg + FFprobe with libx264 (tested on 6.1)
- Optional: `GEMINI_API_KEY` for image/TTS generation; `espeak-ng` only for test fixtures

```bash
cd pipeline && npm ci && cd ..
node pipeline/src/cli.mjs doctor
cd pipeline && npm test
```

## Modules (`src/lib/`)
| Module | Role |
|---|---|
| `episode.mjs` | Load/validate manifests; resolve auto scene durations from measured narration; place voice, captions, SFX |
| `scene.mjs` | Compose a frame: environment layers, items, actors with held props, lighting, screen overlays |
| `camera.mjs` | 2.5D camera: pan/tilt/zoom/dolly/roll, presets, follow, handheld shake |
| `character.mjs` | Stick-figure rig: FK, pose blending, procedural walk/run/wave…, expressions, blinks |
| `shapes.mjs` | Declarative vector shapes (the editable asset source format) |
| `lighting.mjs` | Grade, light shafts, dust motes, vignette |
| `transitions.mjs` | whip pan, smash cut, snap zoom, push-through, push, object wipe, iris, dip |
| `captions.mjs` | Semantic cue chunking, 2-line wrap, emphasis, SRT/VTT |
| `audio.mjs` | FFmpeg mix: VO, sidechain-ducked music, ambience, SFX, loudness normalisation |
| `render.mjs` | Frame loop → H.264, mux, contact sheet, decode check, report |
| `gemini.mjs` | One-shot Gemini image/TTS requests with receipts (adapted from Kaomei, MIT) |
| `registry.mjs` | Asset registry scan/check/approve with SHA-256 freeze for approved assets |

Performance (cloud container, 1 CPU-ish): final 1080×1920@30 renders at roughly 5–6 frames/s; `--draft` (540×960@15) is about 8× faster.
