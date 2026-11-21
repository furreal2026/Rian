# CURIOUS MIND — TECHNICAL SPECIFICATIONS

Version: 0.1 (draft)
Dibuat: 2026-11-22
Status: Sebagian besar TBD

Aturan dokumen ini: hanya nilai yang **sudah tertulis** di dokumen standar yang dimasukkan sebagai nilai tetap, lengkap dengan sumbernya. Semua yang belum diputuskan ditandai **TBD** dan tidak boleh diisi dengan asumsi. Isi TBD hanya setelah ada keputusan pemilik proyek, lalu catat di `docs/decisions/CHANGELOG.md`.

## 1. Rasio dan format

| Item | Nilai | Sumber |
|---|---|---|
| Short-form (Shorts/Reels/TikTok) | 9:16 vertikal | Master §5, Environment §7 |
| Long-form (YouTube) | 16:9 horizontal | Master §5, Environment §7 |
| Aturan rasio | Ikuti brief episode, jangan diasumsikan | Environment §7 |
| Durasi | Ditentukan kebutuhan cerita, bukan angka tetap | Master §5 |

## 2. Spesifikasi ekspor video

Master §11 Phase F menyebut "export sesuai rasio dan spesifikasi platform", tetapi angkanya tidak ditulis.

| Item | Nilai |
|---|---|
| Resolusi 9:16 | TBD |
| Resolusi 16:9 | TBD |
| Frame rate | TBD |
| Codec / container | TBD |
| Bitrate | TBD |
| Color space | TBD |
| Safe area (UI platform) | TBD |

## 3. Aset gambar

| Item | Nilai | Sumber |
|---|---|---|
| Format aset reusable | PNG dengan latar transparan | Environment §5 |
| Isi per gambar | Satu aset utama, objek utuh, tidak terpotong | Environment §5 |
| Penamaan file | huruf kecil, snake_case, deskriptif | Environment §9 |
| Suffix versi | `_v01`, `_v02`, hanya jika ada beberapa versi | Environment §9 |
| Resolusi aset | TBD |
| Ukuran kanvas environment | TBD |
| Format sumber/editable (mis. SVG, layer file) | TBD |

## 4. Layer 2.5D

Urutan layer: Background, Midground, Foreground, Character, Effects (Master §4, Environment §6). Layer harus memungkinkan parallax. Aturan teknis parallax (rasio kecepatan antar-layer): TBD.

## 5. Tempo kamera dan transisi

Nilai awal dari Camera §6 (panduan awal, boleh disesuaikan dengan ritme narasi):

| Jenis | Durasi |
|---|---|
| Transisi sangat cepat | 0.15–0.35 detik |
| Transisi cepat standar | 0.30–0.50 detik |
| Transisi dramatis | 0.50–0.80 detik |

## 6. Desain karakter master

Master §3 mengacu ke "desain master yang sudah disetujui", tetapi detailnya belum didokumentasikan di repository.

| Item | Nilai |
|---|---|
| Lokasi file desain master | TBD (folder `characters/stick_figure/` masih kosong) |
| Proporsi kepala dan tubuh | TBD |
| Ketebalan garis | TBD |
| Warna karakter | TBD |
| Daftar ekspresi dan pose dasar | TBD |
| Karakter pendukung | TBD |
| Lokasi referensi desain Milo lama (yang tidak boleh dipakai kembali) | TBD |

## 7. Palet warna dan gaya garis

Dokumen standar hanya menyebut "warna cerah", "outline tegas", dan "bentuk membulat".

| Item | Nilai |
|---|---|
| Palet warna utama | TBD |
| Palet per kategori environment | TBD |
| Ketebalan outline environment | TBD |

## 8. Subtitle

Master §11 dan §12 mewajibkan subtitle terbaca, tanpa spesifikasi.

| Item | Nilai |
|---|---|
| Font | TBD |
| Ukuran dan posisi | TBD |
| Warna / outline | TBD |
| Bahasa | TBD |

## 9. Audio

| Item | Nilai |
|---|---|
| Standar loudness | TBD |
| Sumber dan lisensi SFX | TBD |
| Sumber dan lisensi musik | TBD |
| Standar voice-over / narator | TBD |

## 10. Tooling

README menyebut Remotion, HyperFrames, dan Lemo-Opuscar (repo terpisah).

| Item | Nilai |
|---|---|
| Peran masing-masing tool dalam pipeline Curious Mind | TBD |
| Versi yang dipakai | TBD |
| Struktur project render | TBD |
| Lokasi hasil render per episode | TBD |

## 11. Penamaan di luar aset environment

Hanya penamaan aset environment yang sudah diatur (Environment §9).

| Item | Nilai |
|---|---|
| Penamaan folder dan file episode | TBD |
| Penamaan shot | TBD (contoh di template storyboard memakai `01-01`, belum disetujui) |
| Penamaan file karakter | TBD |

## 12. Riset dan sumber

Master §11 Phase B meminta sumber tepercaya dan pemisahan fakta, asumsi, fiksi, tetapi belum ada format pencatatan sumber. Format log riset: TBD.
