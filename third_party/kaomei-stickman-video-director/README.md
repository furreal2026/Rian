# Kaomei Stickman Video Director — vendored subset

- Upstream: https://github.com/kaomei/stickman-video-director
- Pinned commit: `9431d3707bde52ba8eb17f31886b0892c763eeba` (2026-11, "Merge pull request #165")
- Licence: MIT (`LICENSE`, copied unchanged)

## What is here and why

Only the parts Curious Mind uses as **production contracts and style reference** — unmodified copies, so updates can be diffed against upstream:

| File | Used for |
|---|---|
| `references/cozy-storytelling.md` | A4 visual identity, character anchor, scene/prop-state rules, acceptance checks |
| `references/a1-a5-direction.md`, `storyboard-template.md`, `omni-flash-prompt-contract.md`, `mode-execution-boundaries.md` | Model Engine prompt workflow (for generating raster plates or optional video inserts) |
| `references/a-production-and-review.md`, `a-audio-timeline-and-review.md`, `voice-continuity.md` | Review discipline, independent audio timeline, one frozen narrator voice per video |
| `references/autopilot-sound-system.md`, `music-sourcing-and-license.md` | Story-led sound design; per-asset licence verification and credits |
| `scripts/gemini-media.mjs` | Original adapter; the adapted version lives in `pipeline/src/lib/gemini.mjs` |
| `UPSTREAM_SKILL.md` | The upstream SKILL.md, for reference only (it links to files not copied here) |

## What is deliberately NOT copied

B1–B7 renderers and their sample-review gates, showcase media (~826 MB repo), A6–A8 styles, most of the 890-item audio library (23 curated items were exported with licence evidence into `assets/audio/library/`). Curious Mind's own renderer is in `pipeline/`; see `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` §1 for the reasoning.

## Optional: installing the full upstream skill

For A-mode prompt packages in other styles, the full skill can be installed into a personal Claude Code skills folder:

```bash
git clone https://github.com/kaomei/stickman-video-director.git /tmp/svd
git -C /tmp/svd checkout 9431d3707bde52ba8eb17f31886b0892c763eeba
mkdir -p ~/.claude/skills && cp -R /tmp/svd/skills/directing-stickman-videos ~/.claude/skills/
```

This is not required for the Curious Mind pipeline.
