# Rian

Character & Environment models untuk video animasi **Curious Mind**.

Curious Mind adalah kanal hiburan-edukasi berbasis pertanyaan "What If?". Repository ini menyimpan dokumen standar produksi, model karakter, environment, aset, dan referensi.

## Mulai dari sini

Acuan utama produksi: [`docs/CURIOUS_MIND_MASTER_GUIDE.md`](docs/CURIOUS_MIND_MASTER_GUIDE.md).

Dokumen teknis tidak boleh bertentangan dengan Master Guide. Jika ada konflik, tandai dan minta keputusan pemilik proyek (lihat Master Guide bagian 14).

## Struktur

```text
Rian/
├── README.md
├── docs/
│   ├── CURIOUS_MIND_MASTER_GUIDE.md          # acuan utama
│   ├── CURIOUS_MIND_ENVIRONMENT.md           # panduan environment & aset visual
│   ├── CURIOUS_MIND_CAMERA_TRANSITIONS.md    # panduan kamera & transisi
│   ├── templates/
│   │   └── STORYBOARD_TEMPLATE.md            # template storyboard gabungan
│   ├── specs/
│   │   └── TECHNICAL_SPECS.md                # spesifikasi teknis (banyak TBD)
│   ├── decisions/
│   │   └── CHANGELOG.md                      # catatan keputusan & revisi bertanggal
│   ├── production/                           # dokumen produksi episode (brief, storyboard)
│   └── archive/
│       └── curious_mind_production_guides.zip  # arsip lama, jangan dihapus
├── characters/
│   └── stick_figure/                         # model karakter utama
├── environments/
│   ├── home/  street/  public_places/
│   └── nature/  science_fantasy/  abstract/
├── assets/
│   └── ASSET_REGISTRY.md                     # registri aset tersedia & dibutuhkan
├── pilot/
│   └── PILOT_01_STOP_TIME/                   # Pilot 01: config, rig, camera, compositor, transitions, tests, assets (lihat README-nya)
├── tools/
│   └── render/                               # mesin render Python + FFmpeg (CLI, encode, QC)
├── references/                               # referensi visual dan moodboard
└── episodes/                                 # satu folder per episode (lihat TBD di bawah)
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

## Alur kerja

1. Konsep → demo / gambar awal (preview ringan, bukan render final)
2. Persetujuan dari pemilik proyek
3. Baru render final setelah disetujui

Alur produksi lengkap (Phase A–G) ada di Master Guide bagian 11.

## Tooling pendukung

Remotion, HyperFrames, Lemo-Opuscar (repo terpisah). Cara pemakaiannya untuk Curious Mind belum didokumentasikan (TBD, lihat `docs/specs/TECHNICAL_SPECS.md`).

## Catatan terbuka

- `EPISODE_PRODUCTION_TEMPLATE.md` disebut di README lama tetapi belum pernah ada di repository. Status: TBD, menunggu keputusan pemilik proyek.
- Detail lain yang belum diputuskan tercatat di `docs/decisions/CHANGELOG.md`.
