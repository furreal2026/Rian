# CURIOUS MIND — ASSET REGISTRY

Dibuat: 2026-11-22
Status: Kosong, belum ada aset yang terdaftar.

Tujuan (dari Master §4 dan Environment §11): cari dan pakai aset yang sudah ada sebelum membuat yang baru, catat aset yang belum tersedia, dan jangan membuat variasi yang hampir sama jika aset lama sudah cukup.

## Aturan

- Penamaan: huruf kecil, snake_case, deskriptif; suffix `_v01`, `_v02` hanya jika ada beberapa versi (Environment §9).
- Aset reusable: PNG latar transparan, satu aset utama per gambar, objek utuh (Environment §5).
- Kategori environment: `home`, `street`, `public_places`, `nature`, `science_fantasy`, `abstract` (Environment §4). Kategori baru hanya jika benar-benar diperlukan.
- Jangan menghapus entri atau aset lama hanya karena tidak sedang dipakai (Master §14). Ubah status menjadi `archived`.
- Status yang dipakai: `available`, `needed`, `in_progress`, `archived`. Daftar status ini usulan dan belum disetujui (TBD).

## Aset tersedia

| Nama file | Kategori | Jenis (environment / prop / karakter / efek) | Lokasi | Versi | Status | Dipakai di episode | Catatan |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | Belum ada aset terdaftar |

## Aset dibutuhkan (belum tersedia)

| Nama usulan | Kategori | Jenis | Dibutuhkan untuk (episode / shot) | Spesifikasi singkat | Status | Catatan |
|---|---|---|---|---|---|---|
| `courtyard_bg_far.png` | public_places (courtyard) | environment (Layer 4, parallax 0.15) | pilot_01_stop_time / semua shot | PNG RGBA ≥ 2389×1372, lihat `pilot/PILOT_01_STOP_TIME/assets/environment/courtyard/README.md` | needed | Plate final belum tersedia; render final BLOCKED |
| `courtyard_bg.png` | public_places (courtyard) | environment (Layer 3, parallax 0.35) | pilot_01_stop_time / semua shot | PNG RGBA ≥ 2846×1587 | needed | idem |
| `courtyard_mid.png` | public_places (courtyard) | environment (Layer 2, parallax 1.0, bidang karakter) | pilot_01_stop_time / semua shot | PNG RGBA ≥ 4383×2304, garis tanah y=0 | needed | idem |
| `courtyard_fg.png` | public_places (courtyard) | environment (Layer 1, parallax 1.5) | pilot_01_stop_time / semua shot | PNG RGBA ≥ 5620×2879, area kosong transparan | needed | idem |
| `fx/leaf_wipe.png` | public_places (courtyard) | efek (object wipe) | pilot_01_stop_time / transisi S03→S04 | PNG RGBA satu daun, sumbu panjang ≥ 2500 px | needed | Leaf wipe hanya teruji dengan daun UJI |

## Aset terkait karakter

| Item | Lokasi | Status |
|---|---|---|
| Desain master stick figure | TBD | TBD (folder `characters/stick_figure/` masih kosong) |
