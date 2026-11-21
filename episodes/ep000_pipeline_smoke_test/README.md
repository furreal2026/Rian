# ep000 — pipeline smoke test

**Technical test only — do not publish.**

- Narration is a robotic `espeak-ng` fixture (see the `.request.json` receipts) used to test timing, captions and the mix.
- The story ("What if you could pause the world for one minute?") is a placeholder, not an approved script.
- It exercises: aerial descend, tracking follow, push-in, emotional close-up, pull-back reveal; whip pan, smash cut, snap zoom, push-through; held prop states, metaphor icons, auto caption placement, ducked music, ambience and SFX.

```bash
node pipeline/src/cli.mjs validate episodes/ep000_pipeline_smoke_test/episode.json
node pipeline/src/cli.mjs render episodes/ep000_pipeline_smoke_test/episode.json --draft
node pipeline/src/cli.mjs render episodes/ep000_pipeline_smoke_test/episode.json
```
