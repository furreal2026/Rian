# CURIOUS MIND — VIDEO PRODUCTION PIPELINE (Code Engine · A4 Cozy Storytelling)

Version: 0.1 (draft untuk persetujuan)
Dibuat: 2026-11-21
Status: Pipeline teknis sudah diuji (render lokal). Arah visual A4 disetujui pemilik proyek; desain karakter master, aset, dan nilai spesifikasi di bawah masih **usulan**.

Dokumen ini tunduk pada `CURIOUS_MIND_MASTER_GUIDE.md`. Jika bertentangan, Master Guide yang berlaku dan konflik dicatat di `docs/decisions/CHANGELOG.md`.

---

## 1. Ringkasan keputusan arsitektur

**Masalah.** A4 Cozy Storytelling di repo Kaomei adalah gaya **Model Engine**: setiap klip dibuat oleh model video (Google Flow / Veo) dari prompt. Hasilnya indah, tetapi (menurut laporan uji Kaomei sendiri, `tests/reports/style-4.md`) identitas karakter, kepemilikan properti, dan sambungan antarklip tidak dijamin, setiap regenerasi berbayar, dan hampir tidak ada yang bisa dipakai ulang.

**Keputusan.** Curious Mind mengadaptasi **bahasa visual** A4 ke **Code Engine** sendiri:

| Unsur A4 | Implementasi di Curious Mind |
|---|---|
| Karakter minimalis ekspresif (kepala putih bulat, torso putih ramping, tungkai garis gelap) | Rig vektor berbasis data: `characters/stick_figure/` (proporsi, 19 ekspresi, 27 pose, aksi prosedural jalan/lari/lambai/dll.). Identitas tidak bisa “drift”. |
| Lingkungan sehari-hari penuh warna | Environment berlapis (JSON vektor atau PNG hasil generate) dengan `depth` per layer untuk parallax 2.5D. |
| Cahaya hangat sinematik | Preset pencahayaan layar (`assets/presets/lighting.json`): grade, sinar cahaya, debu cahaya, vignette. |
| Close-up emosional & wide shot sinematik | Kamera virtual 2.5D: zoom lensa, dolly (skala per kedalaman), pan/tilt, follow/tracking, crane, aerial, orbit semu, handheld. |
| Interaksi alami | Pose blending, properti dipegang di tangan (phone, mug…), item beranimasi, ekspresi berwaktu, kedip otomatis. |
| Setiap segmen pindah lokasi | Satu scene = satu environment; transisi cepat (whip, smash, snap zoom, push-through, object wipe). |

**Model Engine tetap dipakai, tetapi hanya untuk membuat aset sekali**: plate latar/foreground (image model) dan suara narasi (TTS), masing-masing dengan *receipt* (prompt, model, waktu, hash). Setelah aset disetujui, aset dipakai ulang tanpa regenerasi.

**Kenapa tidak memakai renderer B Kaomei langsung?** Renderer B1–B4 Kaomei terikat pada gerbang review dan sampel gaya mereka sendiri, tidak punya objek kamera (gerakan kamera penuh-frame bahkan tidak dihitung sebagai gerak), dan tidak punya rig karakter. Kami memakai **kontrak produksi** Kaomei (alur sampel → persetujuan → render penuh, narasi tidak di-stretch, lisensi audio per aset, receipt generasi), bukan kodenya.

> Ilusi 2.5D dari layer 2D tidak boleh disebut 3D penuh (Master §9, Camera §11).

## 2. Struktur

```text
.claude/skills/curious-mind-video/SKILL.md   # skill proyek (otomatis dikenali Claude Code di repo ini)
pipeline/                                    # Code Engine (Node 20+, @napi-rs/canvas, FFmpeg)
  src/cli.mjs                                # perintah: doctor, validate, stills, render, voice, image, key, sheets, registry
  src/lib/                                   # camera, character, scene, shapes, lighting, transitions, captions, audio, episode, render, gemini, registry
  tests/                                     # npm test (unit + integrasi render)
characters/stick_figure/                     # rig, poses, expressions, reference/*.png
environments/<kategori>/<nama>/              # environment.json (+ layers/*.png, source/), reference/preview.png
assets/
  props/<nama>/prop.json                     # properti & ikon metafora (vektor)
  presets/                                   # camera, transitions, lighting, captions, formats
  audio/library/                             # musik & SFX berlisensi + bukti lisensi + CREDITS.md
  fonts/                                     # Nunito (OFL)
  registry.json                              # registri mesin: status + SHA-256 setiap aset
  ASSET_REGISTRY.md                          # registri untuk manusia
episodes/<id>/                               # episode.json, audio/vo/*.wav (+receipt), output/ (diabaikan git)
third_party/kaomei-stickman-video-director/  # subset referensi upstream, LICENSE (MIT), commit yang dipin
```

## 3. Alur produksi per episode (memetakan Master §11)

| Fase | Langkah | Alat |
|---|---|---|
| A–C Ide, riset, naskah | Naskah dengan HOOK → PREMISE → … (Master §6–7). Narasi ditulis per baris, satu gagasan per baris. | — |
| D Storyboard & aset | Isi `docs/templates/STORYBOARD_TEMPLATE.md`, lalu terjemahkan ke `episodes/<id>/episode.json`. Cek `assets/registry.json` dulu; hanya minta aset baru bila belum ada (catat di `ASSET_REGISTRY.md` → “dibutuhkan”). | `registry list` |
| D′ Aset baru | Vektor: tulis JSON. Raster: buat file request → `image --allow-network` (setelah izin biaya) → `key` (chroma) → daftarkan. | `image`, `key`, `registry scan` |
| E Voice | Narasi final: `voice --engine gemini --model … --voice … --allow-network` (atau impor WAV dari layanan lain). File yang sudah ada **tidak pernah** dibuat ulang. | `voice` |
| E Blocking | `validate` lalu `stills --times …` untuk cek komposisi, lalu `render --draft --seconds 20`. | `validate`, `stills`, `render --draft` |
| Persetujuan | Pemilik menonton sampel ~20 detik (gambar + suara). | manusia |
| F Final | `render` → MP4 1080×1920, SRT/VTT, contact sheet, CREDITS.txt, report.json (hash, loudness, decode check). | `render` |
| G Review | Tonton di ponsel, dengarkan mix, isi QC Master §12. Report **tidak** menggantikan review manusia. | manusia |

## 4. Format episode (ringkas)

Lihat contoh lengkap: `episodes/ep000_pipeline_smoke_test/episode.json`.

- `scenes[]`: `id`, `duration` (detik atau `"auto"` = mengikuti narasi scene + `pad`), `environment`, `lighting`, `camera`, `actors`, `items`, `transition_out`, `caption_slot` (opsional: `low|high|mid`).
- `camera`: `{preset, at, zoom, amount, start, end}` atau `{keys:[{t,x,y,zoom,dolly,roll,ease}]}`; `follow: {actor, axis, lag, offset}` untuk tracking; `shake` untuk handheld.
- `actors[]`: `path` (posisi berwaktu), `pose` (blend antar-pose), `action` (walk/run/wave/bounce/nod/shake_head/nervous/gesture/idle), `expression`, `gaze`, `facing`, `talk`, `props` (dipegang di tangan `l|r`, dengan `state`).
- `items[]`: properti/ikon di dunia (`depth`, `z: back|front`) atau di layar (`screen: true`), dengan `keys` (x, y, scale, angle, alpha) dan `from/to`.
- `voice.lines[]`: `{id, scene, offset, path, text, captions?}` — memindah scene ikut memindah narasi, subtitle dan SFX. Alternatif: `voice.track` (satu file kontinu + caption hasil alignment).
- `music`, `ambience[]`, `sfx[]`: berdasarkan ID di `assets/audio/library/audio-selection.json` atau `path` lokal; SFX bisa ditambatkan ke scene (`scene` + `at`).

Subtitle: Nunito 900, maks. 2 baris, `*kata*` = sorotan kuning. Posisi dipilih otomatis agar tidak menutupi karakter dan tidak masuk zona UI Shorts.

## 5. Kebijakan aset

1. **Cek dulu, buat belakangan** (Master §4). `node pipeline/src/cli.mjs registry list`.
2. Setiap aset punya **sumber yang bisa diedit** (JSON vektor) atau **receipt generasi** (`*.request.json`: prompt lengkap, model, waktu, hash).
3. Status: `needed → in_progress → draft → (candidate_master) → approved → archived`. Hanya pemilik proyek yang menyetujui: `registry approve <id> --by "<nama>"`.
4. Aset `approved` dibekukan: `registry check` gagal bila file berubah. Perubahan = ID/versi baru (`_v02`), bukan menimpa.
5. Generator menolak menimpa file atau receipt yang sudah ada, dan menolak membuat aset untuk ID yang sudah `approved`.
6. Aset pihak ketiga membawa lisensinya sendiri; lihat `THIRD_PARTY_NOTICES.md`. Musik CC BY wajib dikredit di deskripsi video (`output/*/CREDITS.txt` dibuat otomatis).

### Membuat plate raster dengan model gambar (opsional)

Request file contoh (`environments/<kat>/<nama>/source/<layer>.request.json`):

```json
{
  "id": "environment/home/kitchen_morning:background",
  "registry_id": "environment/home/kitchen_morning",
  "output": "../layers/background.png",
  "model": "<model gambar yang tersedia>",
  "prompt": "Full-color 2D cartoon story environment, cozy kitchen in warm morning light, clean cartoon contours, gentle cinematic lighting, depth, vertical 9:16 composition. Empty scene: no people, no characters, no text, no letters, no labels."
}
```

Untuk layer foreground/midground, minta objek di atas latar hijau polos `#00FF00`, lalu `key in.png out.png`. Gunakan bahasa gaya dari `third_party/.../references/cozy-storytelling.md`; jangan masukkan kode warna (hex) ke prompt (aturan Kaomei).

## 6. Status uji (2026-11-21, sesi cloud)

| Komponen | Status | Bukti |
|---|---|---|
| Render video lokal (canvas → FFmpeg H.264) | **Teruji** | `ep000_pipeline_smoke_test`: 19,6 s, 1080×1920@30, decode penuh lulus |
| Mix audio (VO + musik ducking + ambience + SFX, loudnorm) | **Teruji secara teknis** | ≈ −14,7 LUFS, TP ≈ −1,3 dBTP. Belum didengar manusia. |
| Subtitle burn-in + SRT/VTT | **Teruji** | lihat output smoke test |
| Kamera, transisi, rig, environment | **Teruji** (visual dicek lewat stills/contact sheet) | — |
| `npm test` (8 unit + 1 integrasi render) | **Lulus** | `pipeline/tests/` |
| Generasi gambar (Gemini) | **Belum terverifikasi** | Kunci yang tersimpan di environment ditolak Google (`API_KEY_INVALID`). Tidak ada gambar yang dibuat. |
| Generasi suara (Gemini TTS) | **Belum terverifikasi** | Sama. Smoke test memakai suara robot `espeak-ng` sebagai *fixture* teknis — **jangan dipublikasikan**. |
| Format 16:9 long-form | Kerangka saja, belum diuji | `formats.json` |

## 7. Yang masih perlu keputusan pemilik

Lihat `docs/decisions/CHANGELOG.md` (entri 2026-11-21) — desain karakter master, palet, spesifikasi ekspor, subtitle, suara narator, musik default, dan penyelarasan teks Master Guide dengan A4.
