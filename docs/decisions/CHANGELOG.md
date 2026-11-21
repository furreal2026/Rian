# CURIOUS MIND — CHANGELOG & DECISION LOG

Sesuai Master Guide bagian 14: catat setiap keputusan baru beserta tanggal revisinya.

## 2026-11-21 — Integrasi Kaomei Stickman Video Director · A4 Cozy Storytelling (branch `claude/kaomei-stickman-integration-6qtlo3`)

Keputusan pemilik proyek (dari brief tugas):
- **A4 Cozy Storytelling disetujui sebagai arah visual baru**: lingkungan sehari-hari penuh warna, cahaya hangat sinematik lembut, karakter stickman minimalis ekspresif, close-up emosional, wide shot sinematik, interaksi alami.
- Kaomei Stickman Video Director menjadi dasar sistem produksi video utama.
- Format prioritas: YouTube Shorts 9:16.

Keputusan arsitektur (usulan implementasi, lihat `docs/CURIOUS_MIND_VIDEO_PIPELINE.md` §1):
- A4 (gaya Model Engine) diadaptasi ke **Code Engine** milik Curious Mind: rig karakter vektor + environment berlapis + kamera 2.5D. Model gambar/TTS hanya dipakai untuk membuat aset sekali, dengan receipt.
- Subset referensi Kaomei disalin ke `third_party/kaomei-stickman-video-director/` (MIT, commit `9431d3707bde52ba8eb17f31886b0892c763eeba`). Repo upstream (≈826 MB) **tidak** disalin utuh.
- 23 rekaman audio berlisensi (2 musik CC BY 4.0, SFX CC0/CC BY 3.0) diekspor dari pustaka audio Kaomei beserta bukti lisensinya ke `assets/audio/library/`.

Ditambahkan (tidak ada file lama yang ditimpa atau dihapus):
- `pipeline/` (renderer, CLI, tes), `.claude/skills/curious-mind-video/`, `docs/CURIOUS_MIND_VIDEO_PIPELINE.md`, `THIRD_PARTY_NOTICES.md`.
- Aset draft: rig `characters/stick_figure/` (status `candidate_master`), 3 environment, 11 props, preset kamera/transisi/cahaya/subtitle/format, `assets/registry.json`.
- Episode uji teknis `episodes/ep000_pipeline_smoke_test/` (suara fixture espeak — bukan untuk publikasi).
- `.gitignore` untuk `node_modules/` dan `episodes/*/output/`.

Diubah: `README.md` (struktur & mulai cepat), `assets/ASSET_REGISTRY.md` (daftar aset baru), `docs/specs/TECHNICAL_SPECS.md` (hanya menambah §13 usulan; nilai TBD tidak diisi).

### Konflik / keputusan yang menunggu pemilik (Master §14)

| # | Isu | Status |
|---|---|---|
| 7 | Master §4 & Environment §1 menyebut “energi komedi, outline tegas, warna cerah”; A4 menekankan kehangatan lembut dan cahaya sinematik. Tidak bertentangan langsung, tetapi teks Master Guide belum menyebut A4. | Teks Master Guide **tidak diubah**. Perlu keputusan: perbarui Master §4 atau tambahkan lampiran A4. |
| 8 | Camera Guide mengutamakan gerak cepat/snappy; referensi A4 lebih tenang. Brief meminta transisi cepat dan kamera dinamis. | Pipeline memakai visual A4 + tata bahasa kamera Curious Mind yang cepat (preset tersedia untuk keduanya). Perlu konfirmasi ritme default. |
| 9 | Desain karakter master masih TBD (Master §3). Rig `stick_figure` mengikuti anchor karakter A4 (kepala putih bulat, torso putih, tungkai gelap, tanpa ciri Milo). | Status `candidate_master` — **belum disetujui**. Setujui atau minta revisi lewat `characters/stick_figure/reference/*.png`. |
| 10 | Spesifikasi ekspor, subtitle, loudness (TECHNICAL_SPECS §2, §8, §9) masih TBD; pipeline butuh nilai default. | Dipakai sebagai **usulan** di `assets/presets/formats.json` & `captions.json` (1080×1920, 30 fps, H.264 CRF 18, AAC 192k, −14 LUFS, Nunito 900). TECHNICAL_SPECS tidak diisi. |
| 11 | Suara narator belum dipilih (provider, model, nama voice). Kaomei: satu suara tetap per video, tanpa instruksi gaya. | Menunggu pilihan pemilik + kunci API yang valid. |
| 12 | Kunci Gemini yang tersimpan di environment cloud ditolak Google (`API_KEY_INVALID`). | Generasi gambar/TTS belum bisa diuji. Perbarui secret di pengaturan environment. |
| 13 | Narasi bahasa apa? (Master tidak menyebut; subtitle TBD.) | Episode uji memakai bahasa Inggris. Perlu keputusan bahasa default (EN / ID / keduanya). |

## 2026-11-22 — Restrukturisasi repository (branch `restructure/curious-mind-docs`)

Disetujui oleh pemilik proyek. Isi standar produksi **tidak diubah**.

Perubahan:
- Tiga dokumen panduan dipindahkan dari root ke `docs/` dengan `git mv` (nama file dan isi tetap; riwayat git terjaga).
- `curious_mind_production_guides.zip` dipindahkan ke `docs/archive/` (tidak dihapus).
- README ditulis ulang agar sesuai struktur baru.
- Ditambahkan: `docs/templates/STORYBOARD_TEMPLATE.md`, `docs/specs/TECHNICAL_SPECS.md`, `assets/ASSET_REGISTRY.md`, dan dokumen ini.
- Ditambahkan folder kosong dengan `.gitkeep`: `characters/stick_figure/`, enam kategori di `environments/`, `assets/`, `episodes/`.

Temuan audit tentang kondisi sebelum restrukturisasi:
- Folder `docs/` tidak pernah ada. Satu file bernama `Docs` dibuat (`705f77e`) lalu dihapus (`ac2bcb7`); tiga dokumen panduan selalu berada di root.
- ZIP identik byte-per-byte dengan `CURIOUS_MIND_ENVIRONMENT.md` dan `CURIOUS_MIND_CAMERA_TRANSITIONS.md`; Master Guide tidak ada di dalam ZIP.
- README lama berisi beberapa versi teks yang ditempel berurutan dan menyebut `EPISODE_PRODUCTION_TEMPLATE.md` yang tidak pernah ada.

## Konflik dan keputusan yang menunggu pemilik proyek

Sesuai Master §14, konflik ditandai dan tidak diubah diam-diam.

| # | Isu | Lokasi | Status |
|---|---|---|---|
| 1 | Template storyboard ada dua versi dengan kolom berbeda | Master §8 vs Camera §8 | Digabung di `docs/templates/STORYBOARD_TEMPLATE.md` (draft); dokumen sumber tidak diubah. Menunggu persetujuan |
| 2 | Master §9 menyatakan "hindari slow fade dan dissolve panjang"; Camera §5 membolehkan fade/dissolve bila ada alasan emosional atau perubahan waktu. Tidak bertentangan, tetapi rumusannya berbeda | Master §9 vs Camera §5 | Terbuka, tidak diubah |
| 3 | Master §13 menyarankan struktur folder; sekarang sudah diterapkan, tetapi teks bagian itu tidak diedit | Master §13 | Selesai secara struktur; teks dokumen tidak diubah |
| 4 | `EPISODE_PRODUCTION_TEMPLATE.md` disebut README lama, belum ada | README lama | TBD, perlu keputusan apakah dibuat dan isinya |
| 5 | Ketiga dokumen hanya bertuliskan "Version 1.0" tanpa tanggal | Semua dokumen panduan | Terbuka, tidak diubah |
| 6 | Layer, rasio, checklist QC, dan aturan "satu gerakan kamera per shot" muncul di lebih dari satu dokumen | Master / Environment / Camera | Dibiarkan; dokumen tidak diubah |

## Informasi yang masih TBD

Lihat `docs/specs/TECHNICAL_SPECS.md` (ekspor video, desain karakter master, palet, subtitle, audio, tooling, penamaan non-environment, log riset) dan `assets/ASSET_REGISTRY.md`.
