# EP04 storyboard frames — TEST

Satu gambar per shot untuk Curious Mind EP004 "What If You Could Read Everyone's Mind?", untuk persetujuan blocking dan framing **sebelum render**. Status: **TEST**, belum disetujui.

| Isi | Lokasi |
|---|---|
| 41 shot + intro (1920×1080); Shot 02 dipecah jadi 02A dan 02B | `frames/shot_01.png` … `shot_41.png`, `shot_02A.png`, `shot_02B.png`, intro `shot_06A.png` |
| Contact sheet v2 (6 frame per halaman: timecode, narasi, arahan kamera, **tempo**, **transisi keluar**) | `sheets/ep04_storyboard_page_01.png` … `_08.png` |
| Uji gerak scroll ponsel (02B → 03), 6,5 detik | `motion/ep04_motiontest_02B_03_scroll.mp4` (`node motion_scroll.mjs`) |

- **Milo:** rig resmi Milo v2 (`rig/`, salinan tanpa perubahan dari `curious-mind` commit `203bfc9`). Tanpa mulut, tanpa rambut, tanpa baju.
- **Figuran:** model dasar yang sama, tanpa wajah, dibedakan dengan warna baju dan aksesori (topi, apron, tas, kacamata, ID card, payung), sedikit blur.
- **Environment:** sketsa tinta dan cat air yang digambar dengan kode, bukan plate final. Satu master layout per lokasi (E01/E02 kamar, E03 jalan perumahan, E04 kafe, E05 plaza, E06 taman, E07 halaman). Setiap shot adalah kamera virtual pada master itu (zoom, posisi, roll, dan blur latar untuk kedalaman 2.5D).
- **Pikiran:** gelembung ikon sebagai overlay 2D (visualisasi fantasi).
- **Intro:** kartu judul setelah Shot 06, berisi logo Curious Mind (`episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/curious_mind_logo.png`), "EPISODE 004", dan judul episode. Durasinya 6 detik, dan semua shot setelahnya bergeser +6 detik.

## Render

```sh
node render.mjs            # semua frame + contact sheet (±1 menit)
node render.mjs 12 15      # shot tertentu
node render.mjs --sheets   # contact sheet saja
```

Butuh Node 22 dan Playwright + Chromium (sudah ada di mesin). Kode: `world.mjs` (filter, kamar, figuran), `locations.mjs` (E03–E07, kucing), `fx.mjs` (gelembung, ikon, sinyal, pose khusus, kartu intro), `shots.mjs` (komposisi per shot), `render.mjs`.

## Batasan yang diketahui

- Gerak kamera (dolly, orbit, tilt, rack focus) ditampilkan sebagai satu momen diam per shot. Gerakannya ada di keterangan contact sheet.
- Sudut "high angle" dan "rear tracking" (Shot 06, 37) diperkirakan dengan framing 2D, karena master layout tampak depan atau samping.
- Shot 24 (POV) tidak menampilkan tangan Milo.
- Duduk di bangku atau kasur digambar tampak samping supaya terbaca sebagai duduk (Milo hanya ±2,8 kepala).

## Versi 2 (2026-11-26): angle, transisi, tempo

- **Angle baru** (`views.mjs`): kamar dari kaki kasur (02A, 05, 06), insert layar ponsel yang di-scroll (02B), glitch dari sudut atas tiga perempat (03), jalan perspektif satu titik hilang (17, 37), kerumunan dari atas (23), close-up mata yang lebih rapat (25), dan kamera rendah setinggi kucing (28).
- **Tidak ada pose tidur telentang.** Saat rebahan, pingsan, atau bangun, Milo duduk dengan **punggung bersandar ke papan kayu kepala kasur** (`leanBoard`, `footMilo`): Shot 02A, 05, 06, 07, dan 41.
- **Transisi kuat dan tempo** untuk setiap shot ada di `plan.mjs` dan tampil di contact sheet: push-through, snap zoom, match cut, smash cut, crash zoom, whip pan, object wipe, leaf wipe, dan cut on action. Durasinya mengikuti Camera §6.
- **Gerak tidak lambat semua:** sebagian besar aksi diberi tempo cepat atau sangat cepat. Tempo lambat hanya dipakai bila ada alasannya (pingsan, refleksi di taman, penutup).
