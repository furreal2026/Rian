# Episodes

One folder per episode: `episodes/epNNN_<slug>/`

```text
episode.json          # scenes, camera, actors, voice lines, music/SFX (schema curious-mind/episode@1)
script.md             # approved script (Master §7 template) — optional but recommended
audio/vo/*.wav        # narration lines + *.request.json receipts (never regenerated automatically)
output/               # renders, captions, reports (git-ignored)
```

Start a new episode by copying `ep000_pipeline_smoke_test/episode.json`, then follow `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` §3.
