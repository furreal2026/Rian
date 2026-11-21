# Rian

Character & Environment models untuk video animasi **Curious Mind**.

Curious Mind adalah kanal hiburan-edukasi berbasis pertanyaan "What If?". Repository ini menyimpan dokumen standar produksi, model karakter, environment, aset, dan referensi.

## Mulai dari sini

Acuan utama produksi: [`docs/CURIOUS_MIND_MASTER_GUIDE.md`](docs/CURIOUS_MIND_MASTER_GUIDE.md).

Produksi video (Code Engine · arah visual A4 Cozy Storytelling): [`docs/CURIOUS_MIND_VIDEO_PIPELINE.md`](docs/CURIOUS_MIND_VIDEO_PIPELINE.md).

Dokumen teknis tidak boleh bertentangan dengan Master Guide. Jika ada konflik, tandai dan minta keputusan pemilik proyek (lihat Master Guide bagian 14).

## Struktur

```text
Rian/
├── README.md
├── THIRD_PARTY_NOTICES.md                    # lisensi & atribusi pihak ketiga
├── .claude/skills/curious-mind-video/        # skill proyek untuk Claude Code
├── pipeline/                                 # Code Engine: renderer, CLI, tes
├── third_party/kaomei-stickman-video-director/  # subset referensi upstream (MIT, commit dipin)
├── docs/
│   ├── CURIOUS_MIND_MASTER_GUIDE.md          # acuan utama
│   ├── CURIOUS_MIND_ENVIRONMENT.md           # panduan environment & aset visual
│   ├── CURIOUS_MIND_CAMERA_TRANSITIONS.md    # panduan kamera & transisi
│   ├── CURIOUS_MIND_VIDEO_PIPELINE.md        # arsitektur & alur produksi video
│   ├── templates/
│   │   └── STORYBOARD_TEMPLATE.md            # template storyboard gabungan
│   ├── specs/
│   │   └── TECHNICAL_SPECS.md                # spesifikasi teknis (banyak TBD)
│   ├── decisions/
│   │   └── CHANGELOG.md                      # catatan keputusan & revisi bertanggal
│   └── archive/
│       └── curious_mind_production_guides.zip  # arsip lama, jangan dihapus
├── characters/
│   └── stick_figure/                         # rig karakter (kandidat master), pose, ekspresi
├── environments/
│   ├── home/  street/  public_places/        # <kategori>/<nama>/environment.json
│   └── nature/  science_fantasy/  abstract/
├── assets/
│   ├── ASSET_REGISTRY.md                     # registri aset tersedia & dibutuhkan
│   ├── registry.json                         # registri mesin (status + SHA-256)
│   ├── props/  presets/  audio/  fonts/
├── references/                               # referensi visual dan moodboard
└── episodes/                                 # satu folder per episode (episode.json, audio/vo, output/)
```

Folder kosong ditandai dengan `.gitkeep`.

## Dokumen

| Dokumen | Fungsi |
|---|---|
| `docs/CURIOUS_MIND_MASTER_GUIDE.md` | Brand, prinsip editorial, aturan karakter, identitas visual, workflow, QC |
| `docs/CURIOUS_MIND_ENVIRONMENT.md` | Kategori environment, standar aset reusable, layering, penamaan file |
| `docs/CURIOUS_MIND_CAMERA_TRANSITIONS.md` | Ukuran shot, sudut, gerakan kamera, transisi, tempo |
| `docs/templates/STORYBOARD_TEMPLATE.md` | Format storyboard gabungan dari Master Guide dan Camera Guide |
| `docs/specs/TECHNICAL_SPECS.md` | Spesifikasi teknis; nilai yang belum diputuskan ditandai TBD |
| `docs/decisions/CHANGELOG.md` | Riwayat keputusan, revisi, dan konflik yang menunggu keputusan |
| `assets/ASSET_REGISTRY.md` | Daftar aset yang sudah ada dan yang belum tersedia |
| `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` | Arsitektur Code Engine, format episode, kebijakan aset, status uji |
| `THIRD_PARTY_NOTICES.md` | Lisensi dan kewajiban atribusi pihak ketiga |

## Alur kerja

1. Konsep → demo / gambar awal (preview ringan, bukan render final)
2. Persetujuan dari pemilik proyek
3. Baru render final setelah disetujui

Alur produksi lengkap (Phase A–G) ada di Master Guide bagian 11.

## Mulai cepat (render video)

```bash
cd pipeline && npm ci && cd ..                 # Node 20+, FFmpeg wajib
node pipeline/src/cli.mjs doctor
node pipeline/src/cli.mjs validate episodes/ep000_pipeline_smoke_test/episode.json
node pipeline/src/cli.mjs render episodes/ep000_pipeline_smoke_test/episode.json --draft
```

## Tooling pendukung

Code Engine Curious Mind (`pipeline/`) mengadaptasi Kaomei Stickman Video Director (A4 Cozy Storytelling). Remotion, HyperFrames, Lemo-Opuscar (repo terpisah) belum dipakai dalam pipeline ini (lihat `docs/specs/TECHNICAL_SPECS.md` §10 dan §13).

## Catatan terbuka

- `EPISODE_PRODUCTION_TEMPLATE.md` disebut di README lama tetapi belum pernah ada di repository. Status: TBD, menunggu keputusan pemilik proyek.
- Detail lain yang belum diputuskan tercatat di `docs/decisions/CHANGELOG.md`.
