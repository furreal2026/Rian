# Courtyard — plate layer (Pilot 01)

Status: **menunggu plate final** (`manifest.json` → `"status": "awaiting_plates"`).
Folder ini sengaja **tidak** berisi environment pengganti. Tanpa plate, render final ditolak dengan pesan `BLOCKED`.

## File yang dibutuhkan

| File | Layer | Parallax | Isi | Ukuran minimum (px) | Posisi kiri-atas (world) |
|---|---|---|---|---|---|
| `courtyard_bg_far.png` | Layer 4 — far background | 0.15 | langit dan skyline jauh (opaque penuh) | 2389 × 1372 | (-1226, -1167) |
| `courtyard_bg.png` | Layer 3 — background | 0.35 | atap, menara, pepohonan di belakang dinding, taman di balik gerbang | 2846 × 1587 | (-1495, -1353) |
| `courtyard_mid.png` | Layer 2 — midground / bidang aksi | 1.0 | dinding belakang, gerbang besi tempa, pintu lengkung (dinding kiri), bangku batu, air mancur, pot, lantai cobblestone; langit di atas dinding, celah jeruji, dan bukaan lengkung gerbang transparan | 4383 × 2304 | (-2386, -1957) |
| `courtyard_fg.png` | Layer 1 — foreground | 1.5 | bingkai tepi saja | 5620 × 2879 | (-3086, -2422) |
| `fx/leaf_wipe.png` | Efek transisi | — | satu daun utuh untuk object wipe S03→S04 | sumbu panjang ≥ 2500 (tampil ±2.3× tinggi frame) | — |

Ukuran dan posisi dihitung dari gerakan kamera pilot (termasuk tilt, pull back, dan offset whip pan) dengan:

```bash
python -m tools.render plate-spec --config pilot/PILOT_01_STOP_TIME/config/pilot_01_stop_time.json
```

Jalankan ulang perintah itu setiap kali storyboard/kamera berubah, lalu perbarui `position` dan `min_size_px` di manifest.

## Pembagian layer dan tata letak master (keputusan pemilik proyek)

Acuan: `source/courtyard_master_ref.png` (1672×941). Dinding, gerbang, bangku, air mancur, dan lantai berada di **Layer 2 yang sama**, supaya sambungan dinding–lantai tidak terbelah oleh parallax saat kamera bergerak. Kalau dinding ditaruh di L3 dan lantai di L2, sambungannya terbelah sampai 604 px pada frame 0 (tilt S01).

Posisi pada kamera referensi (persentase frame 1920×1080):

| Elemen | Posisi |
|---|---|
| Kamera | eye level, horizon 50% tinggi |
| Dasar dinding belakang = tepi lantai | ±64% tinggi |
| Gerbang besi tempa (tengah) | ±39% lebar |
| Pintu lengkung | dinding kiri |
| Bangku batu (satu) | 55–68% lebar, menempel dinding belakang |
| Air mancur | 78–98% lebar, dasar ±64% tinggi |
| Lantai cobblestone terbuka | 64–100% tinggi, selebar frame |
| Pita aksi karakter (harus bersih) | 66–92% tinggi |

Format masukan: L3, L2, L1, dan daun dikirim di atas latar magenta datar (mendekati #FF00FF, bukan nilai persis) sebagai pengganti alpha; L4 opaque. Konversi ke RGBA dilakukan dengan `python -m tools.render ingest-plates` (arsip asli di `source/`, hasil di `keyed/`, preview di `qc/`).

## Status plate (2026-11-22)

Plate yang dikirim berbingkai persis seperti frame master (1672×941, tanpa overscan). Pemilik proyek menerima aset apa adanya untuk tes 10 detik (opsi A: gerakan kamera tetap di dalam bingkai).

| Layer | Status keying | Catatan |
|---|---|---|
| L4 `courtyard_bg_far.png` | PASS | opaque, tidak di-key |
| L3 `courtyard_bg.png` | BLOCKED (diterima apa adanya) | fringe/bintik magenta di tepi dedaunan; pita taman berhenti di 65% tinggi |
| L2 `courtyard_mid.png` | BLOCKED (diterima apa adanya) | gerbang bersih (wilayah `key_regions.json`); bintik magenta di puncak ivy |
| L1 `courtyard_fg.png` | BLOCKED (diterima apa adanya) | fringe magenta di daun; rasio 1,87 → crop tengah 100 px horizontal |
| `fx/leaf_wipe.png` | PASS | diperbesar Lanczos ke 2500×1250 |

Cara pemasangan (manifest tidak diubah): tiap plate diskalakan Lanczos (alpha premultiplied) ke tampilan kamera referensi pada layernya (1920×1080 unit world), lalu ditempel di posisi tampilan itu di kanvas transparan seukuran `min_size_px`. Lihat `qc/fit_report.json`. Karena tidak ada gambar di luar bingkai master, config yang memakai plate ini harus menjaga kamera di dalam bingkai: `config/pilot_01_courtyard_test_10s.json`. Config teknis `pilot_01_stop_time.json` (dipakai tes otomatis) akan memperlihatkan area kosong bila dirender dengan plate ini.

Perbaikan yang disarankan: buat ulang L3, L2, L1 sebagai PNG transparan atau di atas latar warna rata yang mirip langit (bukan magenta).

## Format

- PNG RGBA 8-bit, sRGB. Penamaan huruf kecil snake_case (Environment Guide §9).
- Layer 4 boleh opaque penuh. Layer 3, 2, 1: area kosong **transparan** agar layer di belakangnya terlihat.
- Semua layer dilukis sebagai satu komposisi yang tersusun rapi saat kamera berada di `reference_camera` (x 0, y -420, zoom 1). Satuan world: 1 unit = 1 px pada frame 1920 lebar, zoom 1. Sumbu y ke bawah.
- **Garis tanah (y = 0)**: kaki karakter berada di y = 0 pada bidang Layer 2. Pada plate `courtyard_mid.png` posisi y = 0 adalah baris piksel `0 - (-1957) = 1957` dari atas (dengan posisi default di atas).
- Skala karakter: tinggi 430 unit world (kepala ≈ 154 unit). Gunakan ini untuk skala bangku, pintu, pohon di Layer 2.
- Plate boleh lebih besar dari ukuran minimum. Jika demikian, ubah `position` agar titik world yang sama tetap di tempatnya, atau ubah `world_units_per_pixel` (global atau per layer) untuk plate resolusi tinggi (mis. 0.5 untuk plate 2×).
- Daun `fx/leaf_wipe.png`: satu daun utuh, latar transparan, sumbu panjang horizontal, isi opaque (bagian yang menyapu frame harus opaque agar wipe bersih).

## Jika plate datang sebagai satu gambar

Pipeline butuh layer terpisah agar parallax bekerja. Jika plate courtyard yang disetujui hanya satu gambar datar, pemisahan layer (masking per kedalaman + pengisian area yang tertutup) harus dikerjakan dan disetujui dulu; pipeline tidak melakukan pemisahan otomatis.

## Memasukkan plate

1. Salin keempat PNG (dan `fx/leaf_wipe.png`) ke folder ini dengan nama persis di atas.
2. Ubah `"status"` di manifest menjadi `"plates_delivered"` (opsional, informatif).
3. Render: `python tools/render/render.py` (Windows: `tools\render\render_pilot.bat`).
4. Baca `pilot/PILOT_01_STOP_TIME/output/pilot_01_stop_time.render.json` → `frames_with_plate_holes` harus kosong. Jika ada frame berlubang, plate kurang lebar/tinggi untuk gerakan kamera pada frame itu.
