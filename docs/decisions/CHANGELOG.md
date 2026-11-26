# CURIOUS MIND — CHANGELOG & DECISION LOG

Sesuai Master Guide bagian 14: catat setiap keputusan baru beserta tanggal revisinya.

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

## 2026-11-22 — Pilot 01: pipeline, nama karakter, plate courtyard

Disetujui oleh pemilik proyek.

- Nama karakter utama: **Rian** (stick figure Curious Mind). Dicatat di `pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json` (`character_name`).
- Pipeline animasi Python + FFmpeg untuk Pilot 01 ditambahkan (`tools/render/`, `pilot/PILOT_01_STOP_TIME/`).
- Brief storyboard Pilot 01 disimpan di `docs/production/PILOT_01_STOP_TIME_BRIEF.md`.
- Pembagian layer courtyard: L4 langit/skyline; L3 atap, menara, pepohonan di belakang dinding, taman di balik gerbang; L2 dinding, gerbang, pintu lengkung, bangku, air mancur, pot, lantai (satu layer supaya sambungan dinding–lantai di 64% tidak terbelah parallax); L1 bingkai tepi saja.
- Plate courtyard diterima apa adanya untuk tes 10 detik, termasuk L3/L2/L1 yang keying-nya BLOCKED (fringe magenta tersisa). Perbaikan yang disarankan: buat ulang sebagai PNG transparan atau di atas latar warna langit.
- Plate dikirim berbingkai persis frame master (tanpa overscan) → opsi A: gerakan kamera dijaga di dalam bingkai; manifest tidak diubah.
- Tes 10 detik memakai beat Brief Scene 02 "Stop!" di courtyard (`config/pilot_01_courtyard_test_10s.json`); courtyard bukan lokasi trotoar Scene 01, jadi ini tes pipeline, bukan potongan episode.

## 2026-11-22 — Desain karakter Rian v2 (wajah, ekspresi, leher)

Disetujui oleh pemilik proyek (expression sheet v2 "Sudah bagus", lalu "Ya buat desain rig nya").

- Referensi persetujuan: `output/character_revision_v2_TEST/rian_expression_sheet_v2_TEST.png` (dan `.svg`).
- Wajah digambar ulang di `pilot/PILOT_01_STOP_TIME/rig/character_art.py`: garis tinta lancip yang bersih, kelopak atas tebal menutup ±½ mata, pupil tertahan di bawah kelopak, alis lebih tipis dekat kelopak, mulut garis pendek. Outline kepala lingkaran konstan 6,4. Kepala samping memakai bahasa visual yang sama.
- Ekspresi dasar/identitas: **Neutral = `deadpan`** (alias `neutral`).
- Set ekspresi di `stick_figure_rig.json` (skema v2): `deadpan`, `deadpan_up` (dipertahankan untuk config yang ada), `skeptical`, `annoyed`, `exhausted`, `confused` (tanda "?"), `shocked` (tanda "!!"), `angry`, `disgusted`, `worried`, `smug`. Nama lama tetap berlaku, jadi config episode tidak perlu diubah.
- Kantung mata abu hanya pada `exhausted` (sebelumnya di semua ekspresi dengan kelopak turun).
- **Leher pendek 8 unit** terlihat di antara kerah dan kepala (bagian dari sprite kepala, ikut berputar dengan `head`). Sendi rig tidak berubah; `units_height` 560 → 568 sehingga `character.height` di config tetap berarti tinggi total karakter (badan tampil ±1,4% lebih kecil pada tinggi config yang sama).
- Badan, kaus, lengan, kaki, pose, dan walk cycle tidak diubah.
- Tes: `test_rig.py` diperbarui (H = 568) dan ditambah tes set ekspresi v2 serta leher. Bukti render: `output/rig_v2_qc_TEST/`.
- Outfit Polisi/Hoodie (`output/character_revision_v2_TEST/rian_outfits_v2_TEST.png`) masih referensi TEST, belum masuk rig.

## 2026-11-22 — Rig full-body Rian v3 (bahu, lengan, kaki, IK, locomotion)

Diminta pemilik proyek (tugas "Full-body character rig revision"). **Disetujui pemilik** ("Sudah bagus. Bikin rig nya"); rig v3 menjadi rig produksi Rian, termasuk lebar leher 8,6.

- Identitas Rian tetap: kepala, wajah, 11 ekspresi, kaus merah, torso, palet, dan gaya ilustrasi tidak diubah.
- Proporsi: lengan 6,6 → 13 unit (lengan bawah meruncing ke pergelangan), kaki 6,6 → 14,8 unit (betis meruncing ke ankle), telapak kaki lebih tebal, tangan r 11,5 → 14. Leher 6,6 → 8,6 unit supaya serasi dengan anggota tubuh yang lebih tebal (panjang leher v2 tetap 8 unit).
- Sambungan: setiap segmen berakhir dengan ujung bulat di pivot sendi dan lebar ujungnya sama dengan awal segmen berikutnya, sehingga siku/lutut tidak bercelah di sudut berapa pun (diuji `test_joints_stay_closed_at_any_bend`).
- Bahu: part baru `clavicle_r/l` (front: rotasi; side: angkat) membawa lengan atas dan "shoulder cap" kaus. Driver otomatis mengangkat bahu saat lengan naik melewati 25° (front) / 35° (side), maks 24°/22°; arah lengan yang di-pose tidak berubah (kompensasi). Bahu juga bisa digerakkan manual (`clavicle_r/l`, mis. shrug).
- Batas sendi (side): siku menekuk ke depan, lutut ke belakang. Lengan dekat di view side digambar di depan kepala.
- Tangan: bentuk `open` (default), `point`, `grip` per key (`hand_r`/`hand_l`); `z` override per key (mis. tangan di depan wajah).
- IK dua tulang (`Rig.ik_two_bone`) untuk lengan dan kaki; key `plant` mengunci kaki di lantai (posisi dunia saat penguncian dimulai), key `reach` untuk target tangan.
- Locomotion baru (`rig/locomotion.py`): `walk` dan `run` berbasis jarak + IK, heel-strike/toe-off, hip bob, ayunan lengan dengan overlap; kaki yang menapak terkunci (pergeseran 0,000 px di uji dan render). `walk_legacy` mempertahankan walk lama. Config yang sudah ada tetap jalan tanpa diubah.
- Follow-through/overlap: secondary motion pegas (stateless) bahu→siku, siku→pergelangan, torso→kepala, pinggul→torso; default aktif, `"secondary": false` untuk mematikan. Easing baru `inBack` (antisipasi), `inOutBack`.
- Pustaka pose: 9 → 51 pose (gestur, tunjuk, silang tangan, sentuh/garuk kepala, pegang objek, bicara, shrug, pindah berat, jongkok/lompat/mendarat, angkat/silang kaki, duduk di kursi/menggantung/bersila/lantai, berbaring, bangun). Pose kontak dihitung dengan IK lalu disimpan sebagai sudut (`output/rig_v3_motion_TEST/author_poses.py`).
- Batasan desain yang tercatat: lengan Rian (128 unit) tidak mencapai puncak kepala (diameter 200), jadi "garuk kepala" menyentuh sisi/belakang kepala. Berbaring telentang: kepala besar bertumpu di lantai dan torso sedikit miring.
- Bukti: `output/rig_v3_motion_TEST/` (perbandingan proporsi, video sebelum/sesudah, motion test 14 segmen, pustaka pose, render courtyard QC PASS). Tes: 59 dijalankan, OK (1 skip opsional).

## 2026-11-25 — EP 04 "What If Bisa Mendengar Pikiran?" memakai Milo v2

Instruksi pemilik proyek: "Milo v2 pakai untuk cerita ini."

- Karakter EP 04: **Milo v2** sesuai `curious-mind/character/MILO_CHARACTER_BIBLE.md` versi 2.1 dan `references/v2/milo_v2_1_reference_sheet.png` (badan krem, tanpa rambut, tanpa baju, tanpa mulut, sekitar 2,8 kepala).
- Konflik: `CLAUDE.md` Rian menulis "Never use Milo"; Master §3 dan Environment §2 membolehkan Milo jika diminta eksplisit. Instruksi pemilik untuk EP 04 eksplisit. `CLAUDE.md` tidak diubah, dan Rian tetap karakter utama Pilot 01.
- Storyboard: `episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/STORYBOARD.md` v0.2 (draft, belum disetujui).

## 2026-11-26 — EP 04: storyboard final pemilik, naskah VO, VO TEST `am_puck`

- Storyboard final dari pemilik menggantikan storyboard v0.2 buatan asisten: `episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/CURIOUS_MIND_EP004_FINAL_STORYBOARD.docx` ("What If You Could Read Everyone's Mind?", 41 shot, 7:50, narasi English, satu narator, Milo v2). Tambahan visual: `source/CURIOUS_MIND_EP004_STORYBOARD_DENGAN_REFERENSI_VISUAL.docx` dan `source/visual_refs/`.
- Naskah VO: `episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/SCRIPT_VO.md`. Teks narasi diambil persis dari tabel shot.
- VO TEST dengan Kokoro `am_puck` (permintaan pemilik): `output/EP04_vo_am_puck_TEST/`. Belum disetujui.
- Teks di dalam gambar referensi berbeda dari tabel shot; mengikuti catatan dokumen itu sendiri, tabel shot yang mengikat.

## 2026-11-26 — EP 04: intro dengan logo, frame storyboard TEST

- **Intro baru** (permintaan pemilik): kartu judul setelah Shot 06 (Milo pingsan), 6 detik, dengan logo Curious Mind (`episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/curious_mind_logo.png`), "EPISODE 004", dan judul episode. Total durasi 7:50 → 7:56; semua shot mulai 07 bergeser +6 detik. Track VO TEST diperbarui, narasi tidak berubah.
- **Frame storyboard TEST** (permintaan pemilik, sebelum render): `output/EP04_storyboard_frames_TEST/`, 41 shot + intro. Milo dari rig v2 resmi (`curious-mind` 203bfc9); environment berupa sketsa kode, bukan plate final.

## 2026-11-26 — EP 04 storyboard v2: angle beragam, transisi kuat, tanpa pose telentang

Permintaan pemilik: berbagai angle 3D/2D dengan transisi yang kuat, insert ponsel yang layarnya bergulir, gerakan karakter tidak lambat semua, dan pose bersandar dengan punggung menyentuh papan kayu kasur. Pose tidur telentang **tidak dipakai**.

- Frame v2 di `output/EP04_storyboard_frames_TEST/` (43 frame: Shot 02 dipecah menjadi 02A kamar dari kaki kasur dan 02B insert layar scroll) dan uji gerak scroll `motion/ep04_motiontest_02B_03_scroll.mp4` (6,5 detik, TEST).
- Rencana transisi dan tempo per shot: `output/EP04_storyboard_frames_TEST/plan.mjs`.
- **Konflik yang dicatat:** `CLAUDE.md` Rian hanya mencantumkan empat transisi (`cut_on_action`, `whip_pan`, `leaf_wipe`, `cut`). Rencana EP 04 memakai juga snap zoom, match cut, smash cut, push-through, crash zoom, dan object wipe, yang diizinkan Master §9 dan Camera §5, atas permintaan eksplisit pemilik. `CLAUDE.md` tidak diubah. Transisi tambahan ini belum ada di pipeline render Rian.

## 2026-11-26 — EP 04 render: potongan padat, VO 1,1×, zoom halus

Permintaan pemilik setelah render TEST pertama (7:56): jeda sesudah narasi terlalu panjang, adegan harus langsung pindah, VO dipercepat 1,1×, dan zoom in/out patah-patah.

- **VO 1,1×.** Klip `am_puck` dipercepat dengan `atempo` (nada tetap). Hasilnya di `output/EP04_render_TEST/vo_fast/`.
- **Potongan padat.** Setiap shot berakhir 0,35 detik (waktu lama) setelah narasinya selesai, ditambah setengah durasi transisi keluarnya. Aksi di dalam shot berjalan 1,1× supaya tetap sinkron dengan VO.
  - Shot yang punya aksi visual sesudah narasi mendapat waktu minimum (`MIN_OLD` di `episode.mjs`): 02B, intro, 22, 23, 31, 40, dan 41.
  - Intro dipendekkan menjadi 2,7 detik.
  - Durasi episode menjadi sekitar 4:15. Ini di bawah target awal "6 menit lebih"; perubahan ini mengikuti permintaan pemilik.
- **Zoom halus.** Penyebab zoom patah-patah: nilai skala kamera dibulatkan ke 2 desimal, sehingga zoom 1,00→1,14 hanya punya 14 langkah. Sekarang dibulatkan ke 4 desimal. Gerak kamera dihitung dari waktu baru shot, jadi selesai mulus di dalam shot yang lebih pendek.

## 2026-11-26 — EP 04: VO ekspresif (TEST)

Permintaan pemilik: suara narator tidak berekspresi dan harus diberi ekspresi.

- **Mesin baru.** Kokoro tidak punya kontrol emosi, jadi VO dibuat ulang dengan Chatterbox (open source, kontrol `exaggeration`). Timbre `am_puck` yang sudah disetujui ditiru dari klip Kokoro `ref_am_puck.wav`. Teks naskah tidak berubah.
- **Level ekspresi per baris** (`output/EP04_vo_expressive_TEST/gen_expressive.py`):
  - narasi biasa 0,62;
  - punchline komedi 0,75;
  - suara pikiran 0,8;
  - bagian reflektif (s32–s36) 0,5.
- **Tempo** dikunci di 1,09× (atempo). Ini menyamakan panjang total VO dengan VO Kokoro di 1,1×.
- **Cek Whisper `base.en`: 42 dari 42 baris lolos.**
  - Baris yang salah ucap dibuat ulang dengan seed lain.
  - s40b dibuat dalam dua bagian, dengan jeda setelah "Tomorrow…".
  - "Milo sighed" terdengar sebagai "Milo's side" (homofon), jadi ditulis di field `asr`.
- Durasi episode menjadi 4:05.
- Pratinjau detik 00–15 dikirim ke pemilik sebelum render penuh.

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
