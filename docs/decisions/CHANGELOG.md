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
