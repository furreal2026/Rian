# stick_figure — candidate master character

Status: **candidate_master** (awaiting owner approval; Master Guide §3, §14).

Code rig following the A4 Cozy Storytelling character anchor: white filled round head, small dark oval eyes, simple brows and mouth; slim white tapered torso; dark single-stroke arms and legs; small dark round hands and short rounded feet. No hair, clothes or Milo traits.

| File | Contents |
|---|---|
| `stick_figure.rig.json` | Proportions, line weights, colours, face layout (source of truth for identity) |
| `poses.json` | 27 named poses (joint angles); blendable |
| `expressions.json` | 19 expressions (facial marks only; head shape never changes) |
| `reference/*.png` | Previews rendered from the JSON (`node pipeline/src/cli.mjs sheets character`) |

Procedural actions layered on poses: `walk`, `run`, `walk_in_place`, `wave`, `gesture`, `bounce`, `nod`, `shake_head`, `nervous`, `idle` (breathing), `freeze`. Blinks are automatic.

Rules: exactly two arms and two legs; expressions change only facial marks; supporting characters must be planned and named per episode (A4 rule), e.g. by adding a new rig folder with different accent colours. Do not edit this rig after approval — create `stick_figure_v02` instead.
