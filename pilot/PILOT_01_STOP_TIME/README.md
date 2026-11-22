# Pilot 01 — What If You Could Stop Time?

Pipeline animasi 2D Curious Mind: Python + FFmpeg. Tanpa Blender, tanpa layanan berbayar.

| Target | Nilai |
|---|---|
| Durasi | 10 detik (240 frame) |
| Resolusi | 1920 × 1080 (16:9) |
| FPS | 24 (konstan) |
| Format | MP4, H.264 High, yuv420p, `+faststart` |

> **Status:** pipeline teknis selesai dan teruji dengan **plate UJI**. Render final menunggu plate courtyard dan aset daun (lihat `assets/environment/courtyard/README.md` di folder ini).
>
> **Catatan storyboard:** brief pilot (`PILOT_01_STOP_TIME_BRIEF.md`) tidak ada di repository. Daftar shot di `config/pilot_01_stop_time.json` adalah **layout teknis** yang memakai semua gerakan kamera dan transisi yang diminta; timing, framing, dan akting harus disesuaikan dengan brief/storyboard resmi saat tersedia (cukup edit JSON, tanpa mengubah kode). Lokasi yang disiapkan untuk dokumen produksi: `docs/production/`.

## Struktur direktori

```text
Rian/
├── requirements.txt                    # numpy, Pillow
├── docs/production/                    # dokumen produksi episode (brief, storyboard)
├── tools/render/                       # mesin render, tidak bergantung episode
│   ├── render.py          SATU perintah: render + QC (default: Pilot 01)
│   ├── render_pilot.bat   pembungkus Windows untuk Pilot 01
│   ├── cli.py             perintah: render, stills, test-assets, plate-spec, qc
│   ├── encode.py          FFmpeg pipe, ffprobe, ekstraksi frame
│   ├── raster.py          sprite/plate mip-map, blit affine, kanvas unit
│   ├── mathx.py           matriks, easing, keyframe track
│   └── testassets.py      aset UJI berlabel (bukan environment)
└── pilot/PILOT_01_STOP_TIME/
    ├── README.md                       # dokumen ini
    ├── config/pilot_01_stop_time.json  # storyboard pilot: shot, kamera, akting, transisi
    ├── rig/
    │   ├── rig.py                      rig cut-out modular (FK, pose, walk cycle)
    │   ├── character_art.py            gambar prosedural bagian rig (master character V2)
    │   ├── stick_figure_rig.json       hierarki, pivot sendi, z-order, palet, ekspresi
    │   └── poses.json                  pustaka pose
    ├── camera/camera.py                # kamera per-frame (keys + drift + tracking), proyeksi parallax
    ├── compositor/
    │   ├── compositor.py               pembacaan config + compositing per frame
    │   └── environment.py              loader plate berlapis dari manifest
    ├── transitions/transitions.py      # cut on action, leaf wipe, whip pan
    ├── tests/                          # unittest: rig, kamera, parallax, compositor, transisi, ekspor
    ├── assets/environment/courtyard/
    │   ├── README.md                   spesifikasi plate yang dibutuhkan
    │   ├── manifest.json               manifest layer (parallax 1.5 / 1.0 / 0.35 / 0.15)
    │   └── fx/                         aset efek (leaf_wipe.png)
    └── output/                         # hasil render & aset uji (di-.gitignore)
```

## Instalasi (Windows 10)

1. **Python 3.10+** (diuji dengan 3.13) dari python.org. Centang *Add python.exe to PATH*.
2. **FFmpeg** (gratis), salah satu:
   - `winget install Gyan.FFmpeg`, atau
   - unduh build "release essentials" dari gyan.dev, ekstrak, lalu tambahkan folder `bin\` ke PATH, atau
   - set variabel `FFMPEG_BIN` (dan opsional `FFPROBE_BIN`) ke path lengkap `ffmpeg.exe`.
3. Dependency Python, dijalankan dari folder repository:

```bat
python -m pip install -r requirements.txt
ffmpeg -version
```

Diuji dengan FFmpeg 6.1, numpy 2.5, Pillow 12.3. Minimum: Pillow 10.1 (untuk font label aset uji), numpy 1.24.

## Menjalankan render

Dari folder repository:

```bat
REM Uji pipeline sekarang (plate UJI berlabel, bukan final)
tools\render\render_pilot.bat --test-plates

REM Render final (setelah plate courtyard dimasukkan)
tools\render\render_pilot.bat
```

Setara di semua OS: `python tools/render/render.py --test-plates` atau `python tools/render/render.py pilot/PILOT_01_STOP_TIME --test-plates`.

Opsi: `--scale 0.5` (preview cepat, QC dilewati), `--workers N` (default: jumlah core − 1), `--out PATH`, `--no-qc`.

Hasil:

| Mode | Video | Laporan |
|---|---|---|
| Uji | `output/test/pilot_01_stop_time_TEST.mp4` | `…_TEST.render.json`, `…_TEST_qc/` |
| Final | `output/pilot_01_stop_time.mp4` | `….render.json`, `…_qc/` |

Tanpa plate, render final berhenti dengan `BLOCKED: Courtyard plate(s) not available yet` (exit code 2) dan tidak membuat file video.

Perintah lain:

```bat
python -m tools.render stills --config pilot\PILOT_01_STOP_TIME\config\pilot_01_stop_time.json --test-plates --frames 0,70,126,187,239 --out-dir pilot\PILOT_01_STOP_TIME\output\stills
python -m tools.render plate-spec --config pilot\PILOT_01_STOP_TIME\config\pilot_01_stop_time.json
python -m tools.render qc --config pilot\PILOT_01_STOP_TIME\config\pilot_01_stop_time.json --video pilot\PILOT_01_STOP_TIME\output\pilot_01_stop_time.mp4
```

## Memeriksa hasil

`render.py` otomatis menjalankan QC setelah render:

- **ffprobe** (frame dihitung ulang dengan `-count_frames`): resolusi, fps, jumlah frame, durasi, codec, pix_fmt, container, dan rasio 16:9. Hasilnya di `…_qc/qc_report.json`; exit code 1 jika ada yang gagal.
- **Frame diekstrak dari MP4** (awal/akhir tiap shot, sebelum/sesudah tiap cut, awal/tengah/akhir tiap transisi) ke `…_qc/frames/`, plus `…_qc/contact_sheet.png`.
- **Coverage plate** per frame di `….render.json` → `frames_with_plate_holes` (harus kosong).

Pengujian otomatis (dari folder repository):

```bat
python -m unittest discover -s pilot\PILOT_01_STOP_TIME\tests -t . -v
REM tambahan: render penuh 240 frame + QC
set CM_FULL_RENDER=1
python -m unittest pilot.PILOT_01_STOP_TIME.tests.test_render -v
```

## Memasukkan plate courtyard

Lihat `assets/environment/courtyard/README.md` di folder ini (nama file, ukuran minimum, posisi, format, garis tanah, skala karakter). Ringkasnya: salin `courtyard_bg_far.png`, `courtyard_bg.png`, `courtyard_mid.png`, `courtyard_fg.png`, dan `fx/leaf_wipe.png` ke folder itu, lalu jalankan `tools\render\render_pilot.bat`. Tidak ada kode yang perlu diubah.

## Cara kerja

**Rig** (`rig/stick_figure_rig.json`). Bagian terpisah: kepala, torso (kaus merah), lengan atas (dengan lengan kaus), lengan bawah, tangan, paha, betis, dan kaki, kiri dan kanan. Tiap bagian punya pivot di sendinya (leher/dagu, bahu, siku, pergelangan, pinggul, lutut, pergelangan kaki) dan diputar lewat parameter (`head`, `shoulder_r`, `elbow_r`, …). Ada dua view: `front` dan `side` (menghadap kanan; `flip: true` untuk menghadap kiri). Ekspresi: `deadpan`, `deadpan_up`, `skeptical`, `shocked`, `smug`. Gambar bagian rig dibuat prosedural dari geometri & palet master character draft V2. Bagian PNG yang disetujui dapat menggantikannya tanpa mengubah rig (`rig/parts/<sprite>.png` + `rig/parts/parts.json` berisi `pivot_px` dan `px_per_unit`).

**Kamera** (per shot, `camera.keys` + `camera.modifiers`). Field key: `t, x, y, zoom, rot, ease`. Gerakan:
- *tilt* = key `y`; *pan* = key `x`; *push/pull back* = key `zoom`; *roll* = `rot`.
- *drift* = modifier `{"type":"drift","amp_x","amp_y","amp_rot","freq","seed"}`.
- *tracking* = modifier `{"type":"track","axis":"x","lag","offset","strength"}`.
- *cut* = batas shot.

Ini kamera 2.5D dari layer 2D, bukan 3D penuh.

**Parallax**. Layer dengan faktor p melihat perpindahan kamera × p dan zoom^p, relatif terhadap `reference_camera`. Layer 1 = 1.5, Layer 2 = 1.0 (bidang karakter), Layer 3 = 0.35, Layer 4 = 0.15. Rasio ini diukur pada piksel hasil render oleh `tests/test_parallax.py`.

**Transisi** (`transitions[]`, antar shot berurutan):

| Tipe | Parameter | Perilaku |
|---|---|---|
| `cut_on_action` | `event`, `offset` | Batas shot dipindah tepat ke frame event karakter (mis. `snap`) |
| `whip_pan` | `duration`, `direction`, `distance`, `samples`, `shutter` | Kamera keluar berakselerasi, kamera masuk melambat dari sisi berlawanan; motion blur sub-frame + streak |
| `leaf_wipe` | `duration`, `asset`, `direction`, `length_frac`, `rotation`, `arc_frac`, `ease` | Daun melintas; area yang sudah disapu daun memperlihatkan shot berikutnya |
| `cut` | — | Cut biasa (default jika tidak ditulis) |

**Compositor**. Untuk setiap frame: hitung waktu → tentukan shot/transisi aktif → kamera → gambar layer dari belakang ke depan, dengan karakter disisipkan pada `character_z` manifest → (transisi) → ratakan ke RGB → kirim ke FFmpeg lewat pipe. Animasi karakter memakai satu timeline adegan, sehingga posisi dan skala karakter kontinu antar shot.

## Episode berikutnya

1. Salin folder `pilot/PILOT_01_STOP_TIME/` menjadi folder episode baru (tanpa `output/`). Nama folder harus berupa identifier Python yang valid (huruf, angka, underscore; tidak diawali angka), mis. `EPISODE_02_GRAVITY`. Kode rig/kamera/compositor/transisi ikut tersalin. `tools/render/` dipakai bersama tanpa disalin.
2. Ganti `config/*.json`: `output`, `character.keys`, `shots`, `transitions`.
3. Ganti `assets/environment/<lokasi>/manifest.json` dan arahkan `environment.manifest` ke sana.
4. Tambah pose ke `rig/poses.json` bila perlu.
5. `python -m tools.render plate-spec --config <episode>/config/<x>.json` → ukuran plate yang dibutuhkan.
6. `python tools/render/render.py <episode> --test-plates` untuk blocking, lalu render final setelah plate disetujui.

Untuk 9:16 cukup ubah `output.width/height` (mis. 1080 × 1920) dan `frame_world_width`.
