# Laporan Sistem Kamera Sinematik — Proyek RIAN

Repo: furreal2026/Rian. Status: belum ada commit atau push (menunggu izin).
Semua video bersifat TEST: 1920×1080, 16:9, 24 FPS, MP4 (H.264).

## 1. Modul kamera yang ditemukan

Folder `pilot/PILOT_01_STOP_TIME/`.

Sudah ada (tidak dibuat ulang):
- `camera/camera.py`: dolly/zoom, tracking horizontal dan vertikal, center shift, drift, easing
- Parallax Foreground : Near : Mid : Far = 1.5 : 1.0 : 0.35 : 0.15
- `compositor/` dan `transitions/`: cut, cut_on_action, whip_pan, leaf_wipe

Belum ada, ditambahkan: yaw/pitch (tetap TIDAK ada), shake, lens zoom, preset framing, blur transition, match cut, push-through, clamp area plate.

## 2. Status tiap fitur

| Fitur | Status | Catatan |
|---|---|---|
| Wide, medium, close-up, extreme close-up, establishing | PASS | Preset framing |
| High-angle, low-angle | PARTIAL | Hanya framing (posisi + zoom). Tidak ada pitch, perspektif tembok tidak berubah |
| Over-the-shoulder | BLOCKED | Butuh aktor atau prop kedua. Preset menolak dengan pesan jelas |
| Push-in/dolly-in, pull-back, zoom lensa | PASS | |
| Tracking horizontal dan vertikal | PASS | Vertikal mengikuti lompatan Rian |
| Tilt, pan, drift, center shift | PASS | |
| Camera shake (intensitas terkontrol) | PASS | Diuji numerik dan lewat still, belum ditonton sebagai gerak video |
| Parallax empat kedalaman | PASS | Rasio terverifikasi pada piksel render oleh test lama |
| Yaw/pitch | Tidak ada | Tidak diklaim |
| Hard cut, cut_on_action | PASS | Cut jatuh pada snap (2,92 s) |
| Match cut | PASS | Ditolak otomatis bila posisi atau skala subjek tidak cocok |
| Whip pan | PASS | Setelah perbaikan |
| Blur transition | PASS | |
| Camera-driven (push-through) | PARTIAL | Jejak bertahap di wajah pada 1–2 frame puncak zoom 2,4× |
| Foreground wipe | PARTIAL | Memakai leaf wipe, aset ivy khusus belum ada |

## 3. Perbaikan yang dilakukan

- Whip pan: pita kosong di tepi kiri (frame 181–182). Clamp kini dijalankan setelah offset transisi.
- Tepi plate: kamera high-angle menempel di tepi lunak plate. Ditambah opsi `clamp_margin` per shot (default 0, shot lama tidak berubah).
- Push-through: demo memakai 15 sampel, bukan 7.

## 4. Hasil uji visual

- Demo 10 skenario: 14 shot, 586 frame, tanpa lubang plate.
- Kehalusan kamera: tidak ada lompatan pada gerakan biasa. Akselerasi maksimum sekitar 3 unit dunia per frame². Hanya shake intensitas 1,6 yang besar, memang disengaja.
- Pilot rencana kamera: 10 s, 240 frame, tanpa lubang plate.
- Catatan: close-up memotong kaki Rian (memang framing close-up) dan agak lembut karena plate di-upscale.

Rencana kamera pilot (disetujui):
- 0–3 s: tilt-down + drift
- 3–6 s: tracking lateral
- 6–8,75 s: cut-in dengan blur
- 8,75–10 s: high-angle wide
- Cut-on-action pada snap dan leaf wipe di 8,75 s

## 5. Lokasi file

Diubah:
- `tools/render/mathx.py`
- `pilot/PILOT_01_STOP_TIME/camera/camera.py`
- `pilot/PILOT_01_STOP_TIME/compositor/compositor.py`
- `pilot/PILOT_01_STOP_TIME/compositor/environment.py`
- `pilot/PILOT_01_STOP_TIME/transitions/transitions.py`

Baru:
- `pilot/PILOT_01_STOP_TIME/camera/presets.py`
- `pilot/PILOT_01_STOP_TIME/tests/test_camera_system.py`
- `pilot/PILOT_01_STOP_TIME/config/camera_demo_10_scenarios.json`
- `pilot/PILOT_01_STOP_TIME/config/pilot_01_camera_plan_test_10s.json`
- `output/camera_demo/TEST_camera_demo_10_scenarios.mp4`
- `output/pilot_camera_plan/TEST_pilot_camera_plan_10s.mp4`

Config yang sudah disetujui tidak disentuh.

## 6. Yang benar-benar berfungsi

Suite penuh: 62 test lolos (45 lama + 17 baru, 1 dilewati seperti sebelumnya). Semua fitur PASS dan PARTIAL di atas sudah dirender pada courtyard asli dengan rig Rian.

## 7. Sisa blocker

- Over-the-shoulder butuh aset aktor atau bahu foreground.
- Pitch sungguhan tidak mungkin dengan plate datar. High/low angle tetap framing.
- Aset ivy wipe belum ada.
- Plate hanya dilukis di area master 1920×1080 tanpa overscan, jadi gerakan dibatasi oleh zoom dan close-up agak lembut sampai ada plate beresolusi lebih tinggi.
