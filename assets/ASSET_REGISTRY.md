# CURIOUS MIND — ASSET REGISTRY

Dibuat: 2026-11-22
Status: Aset draft pertama terdaftar (2026-11-21). Sumber kebenaran mesin: `assets/registry.json` (status + SHA-256); tabel di bawah adalah ringkasannya.

Tujuan (dari Master §4 dan Environment §11): cari dan pakai aset yang sudah ada sebelum membuat yang baru, catat aset yang belum tersedia, dan jangan membuat variasi yang hampir sama jika aset lama sudah cukup.

## Aturan

- Penamaan: huruf kecil, snake_case, deskriptif; suffix `_v01`, `_v02` hanya jika ada beberapa versi (Environment §9).
- Aset reusable: PNG latar transparan, satu aset utama per gambar, objek utuh (Environment §5).
- Kategori environment: `home`, `street`, `public_places`, `nature`, `science_fantasy`, `abstract` (Environment §4). Kategori baru hanya jika benar-benar diperlukan.
- Jangan menghapus entri atau aset lama hanya karena tidak sedang dipakai (Master §14). Ubah status menjadi `archived`.
- Status yang dipakai: `available`, `needed`, `in_progress`, `archived`. Daftar status ini usulan dan belum disetujui (TBD).
- Pipeline video memakai status mesin: `needed`, `in_progress`, `draft`, `candidate_master`, `approved`, `archived` (lihat `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` §5). `approved` hanya diberikan pemilik proyek: `node pipeline/src/cli.mjs registry approve <id> --by "<nama>"`. Aset `approved` dibekukan oleh `registry check`.

## Aset tersedia

| Nama file | Kategori | Jenis (environment / prop / karakter / efek) | Lokasi | Versi | Status | Dipakai di episode | Catatan |
|---|---|---|---|---|---|---|---|
| `character/stick_figure` | — | karakter | `characters/stick_figure/stick_figure.rig.json` | — | candidate_master | ep000 (uji) |  |
| `environment/abstract/warm_idea_space` | abstract | environment | `environments/abstract/warm_idea_space/environment.json` | — | draft | ep000 (uji) | Warm glowing 'mind space' with floating bokeh at several depths — for explanations, metaphors, inserts and … |
| `environment/home/cozy_bedroom` | home | environment | `environments/home/cozy_bedroom/environment.json` | — | draft | ep000 (uji) | Warm morning bedroom: window with sky/rooftops (deep parallax), wallpapered wall with curtains/shelf/frame,… |
| `environment/street/sidewalk_morning` | street | environment | `environments/street/sidewalk_morning/environment.json` | — | draft | ep000 (uji) | Long morning sidewalk with colourful shopfronts, trees and lamps; wide world for tracking/truck shots and w… |
| `preset/camera` | — | preset | `assets/presets/camera.json` | — | draft | ep000 (uji) |  |
| `preset/captions` | — | preset | `assets/presets/captions.json` | — | draft | ep000 (uji) |  |
| `preset/formats` | — | preset | `assets/presets/formats.json` | — | draft | ep000 (uji) |  |
| `preset/lighting` | — | preset | `assets/presets/lighting.json` | — | draft | ep000 (uji) |  |
| `preset/transitions` | — | preset | `assets/presets/transitions.json` | — | draft | ep000 (uji) |  |
| `prop/alert_dot` | — | prop | `assets/props/alert_dot/prop.json` | — | draft | ep000 (uji) | Soft red anxiety dot (A4 metaphor graphic; only on its timed beat). |
| `prop/alert_triangle` | — | prop | `assets/props/alert_triangle/prop.json` | — | draft | ep000 (uji) | Outline red triangle anxiety icon. |
| `prop/desk_lamp` | — | prop | `assets/props/desk_lamp/prop.json` | — | draft | ep000 (uji) | Desk lamp; state 'on' adds warm glow. |
| `prop/heart` | — | prop | `assets/props/heart/prop.json` | — | draft | ep000 (uji) | Heart icon (warmth/affection metaphor). |
| `prop/lightbulb` | — | prop | `assets/props/lightbulb/prop.json` | — | draft | ep000 (uji) | Idea light bulb icon (metaphor graphic, screen overlay). |
| `prop/mug` | — | prop | `assets/props/mug/prop.json` | — | draft | ep000 (uji) | Mustard ceramic mug. state 'steam' adds rising steam. |
| `prop/notebook` | — | prop | `assets/props/notebook/prop.json` | — | draft | ep000 (uji) | Open notebook seen from above-front. state 'written' shows scribble strokes (no letters). |
| `prop/pen` | — | prop | `assets/props/pen/prop.json` | — | draft | ep000 (uji) | Ballpoint pen; anchor at the tip. |
| `prop/phone` | — | prop | `assets/props/phone/prop.json` | — | draft | ep000 (uji) | Smartphone. states: screen_on / notify (red badge) / screen_off / back (face-down). No readable UI text. |
| `prop/potted_plant` | — | prop | `assets/props/potted_plant/prop.json` | — | draft | ep000 (uji) | Potted plant with gently swaying leaves. |
| `prop/question_orb` | — | prop | `assets/props/question_orb/prop.json` | — | draft | ep000 (uji) | Curiosity orb with a drawn question-mark glyph (symbol, not caption text) — the 'What if?' motif. |

## Aset dibutuhkan (belum tersedia)

| Nama usulan | Kategori | Jenis | Dibutuhkan untuk (episode / shot) | Spesifikasi singkat | Status | Catatan |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Belum ada kebutuhan tercatat |

## Aset terkait karakter

| Item | Lokasi | Status |
|---|---|---|
| Desain master stick figure (kandidat) | `characters/stick_figure/stick_figure.rig.json` + `poses.json` + `expressions.json`; pratinjau di `characters/stick_figure/reference/` | `candidate_master` — menunggu persetujuan pemilik (Master §3) |

## Audio berlisensi (pihak ketiga)

23 rekaman di `assets/audio/library/` (lihat `CREDITS.md` dan `audio-selection.json` di folder itu). Musik: `bgm-morning`, `bgm-carefree` (Kevin MacLeod, CC BY 4.0 — kredit wajib). SFX: CC0, kecuali `record-scratch-…` dan `kevin-rimshot-bah-dum` (CC BY 3.0 — kredit wajib).

## Aset yang disarankan berikutnya (needed, belum dibuat)

| Nama usulan | Kategori | Jenis | Spesifikasi singkat | Status |
|---|---|---|---|---|
| `home/kitchen_morning` | home | environment | Dapur hangat, meja, jendela; untuk adegan sehari-hari | needed |
| `public_places/cafe_terrace` | public_places | environment | Teras kafe outdoor (padanan sampel A4 Kaomei) | needed |
| `public_places/metro_platform` | public_places | environment | Peron kereta, tiang foreground untuk object wipe | needed |
| `nature/park_path` | nature | environment | Jalur taman untuk adegan berjalan | needed |
| `science_fantasy/home_lab` | science_fantasy | environment | Laboratorium sederhana untuk eksperimen What If | needed |
