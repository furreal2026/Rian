# Courtyard — plate layer (Pilot 01)

Status: **menunggu plate final** (`manifest.json` → `"status": "awaiting_plates"`).
Folder ini sengaja **tidak** berisi environment pengganti. Tanpa plate, render final ditolak dengan pesan `BLOCKED`.

## File yang dibutuhkan

| File | Layer | Parallax | Isi | Ukuran minimum (px) | Posisi kiri-atas (world) |
|---|---|---|---|---|---|
| `courtyard_bg_far.png` | Layer 4 — far background | 0.15 | langit, skyline jauh | 2389 × 1372 | (-1226, -1167) |
| `courtyard_bg.png` | Layer 3 — background | 0.35 | dinding courtyard, pohon jauh | 2846 × 1587 | (-1495, -1353) |
| `courtyard_mid.png` | Layer 2 — midground / bidang aksi | 1.0 | lantai/tanah tempat karakter berdiri, bangku, pot | 4383 × 2304 | (-2386, -1957) |
| `courtyard_fg.png` | Layer 1 — foreground | 1.5 | daun, pagar, elemen pembingkai dekat kamera | 5620 × 2879 | (-3086, -2422) |
| `fx/leaf_wipe.png` | Efek transisi | — | satu daun untuk object wipe S03→S04 | sumbu panjang ≥ 2500 (tampil ±2.3× tinggi frame) | — |

Ukuran dan posisi dihitung dari gerakan kamera pilot (termasuk tilt, pull back, dan offset whip pan) dengan:

```bash
python -m tools.render plate-spec --config pilot/PILOT_01_STOP_TIME/config/pilot_01_stop_time.json
```

Jalankan ulang perintah itu setiap kali storyboard/kamera berubah, lalu perbarui `position` dan `min_size_px` di manifest.

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
