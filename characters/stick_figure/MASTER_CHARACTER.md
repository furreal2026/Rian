# CURIOUS MIND — MASTER CHARACTER V1.0

Status: draft, menunggu persetujuan pemilik proyek. Belum ada aset final.
Draft visual V2 (terbaru, ilustrasi tinta): [`drafts/v2/stick_figure_master_sheet_draft_v2.png`](drafts/v2/stick_figure_master_sheet_draft_v2.png) · [`drafts/v2/expressions_sheet_draft_v2.png`](drafts/v2/expressions_sheet_draft_v2.png) · [`drafts/v2/face_study_draft_v2.png`](drafts/v2/face_study_draft_v2.png)
Draft visual V1 (geometris, disimpan untuk perbandingan): [`drafts/stick_figure_master_sheet_draft.png`](drafts/stick_figure_master_sheet_draft.png) · [`drafts/expressions_sheet_draft.png`](drafts/expressions_sheet_draft.png)
Referensi visual utama: [`references/curious_mind_reference_sheet.png`](references/curious_mind_reference_sheet.png)

![Reference sheet](references/curious_mind_reference_sheet.png)

## Character Identity

Karakter utama adalah stick figure bergaya kartun minimalis dengan kesan dewasa, datar, lelah, skeptis, dan seperti telah mengalami banyak kejadian aneh.

## Head and Face

- Kepala bulat putih.
- Tanpa rambut.
- Mata oval dengan bentuk half-lidded sebagai ekspresi default.
- Alis hitam tegas dan fleksibel.
- Mulut kecil dan minimalis.
- Wajah harus mampu menampilkan ekspresi emosional yang jelas.
- Ekspresi default: deadpan, bukan ceria.

## Body

- Tubuh stickman sederhana.
- Lengan dan kaki berupa garis hitam.
- Tangan sederhana.
- Tidak menggunakan celana.
- Tidak menggunakan sepatu.
- Tidak mengubah proporsi tubuh antar kostum.

## Clothing System

Pakaian hanya dikenakan pada bagian badan atas. Kostum dapat berubah sesuai peran cerita. Tujuh kostum resmi awal:

- Casual red shirt.
- Hoodie.
- Police uniform.
- Scientist coat.
- Jacket.
- Samurai outfit.
- Superhero costume.

Kostum lain yang khusus untuk cerita tertentu boleh ditambahkan sesuai kebutuhan.

Pakaian tidak boleh mengubah bentuk dasar kepala, wajah, lengan, atau kaki.

## Core Expressions

1. Neutral / Deadpan
2. Skeptical
3. Annoyed
4. Exhausted
5. Confused
6. Shocked
7. Angry
8. Disgusted
9. Worried
10. Smug

## Consistency Rules

- Selalu pertahankan bentuk kepala dan proporsi karakter.
- Jangan menambahkan rambut, celana, atau sepatu.
- Jangan menjadikan senyum sebagai ekspresi default.
- Kostum boleh berubah, identitas karakter tidak.
- Jangan mengubah desain master tanpa persetujuan.

## Asset Naming

Gunakan lowercase snake_case, mengikuti aturan `assets/ASSET_REGISTRY.md`: versi pertama **tanpa suffix**. Suffix `_v02`, `_v03`, dan seterusnya hanya untuk revisi berikutnya.

- `stick_figure_master.png`
- `expression_deadpan.png`
- `expression_skeptical.png`
- `outfit_police.png`
- `outfit_hoodie.png`
- Revisi: `expression_deadpan_v02.png`

File di `drafts/` memakai akhiran `_draft` dan bukan aset produksi.

## Folder Structure

```
characters/
└── stick_figure/
    ├── MASTER_CHARACTER.md   # dokumen ini
    ├── expressions/          # expression_<nama>.png
    ├── outfits/              # outfit_<nama>.png
    ├── poses/                # pose aksi (penamaan menyusul)
    ├── references/           # gambar acuan visual, bukan aset produksi
    └── drafts/               # draft visual untuk ditinjau, bukan aset produksi
        ├── src/              # generator draft V1 (geometris)
        └── v2/               # draft V2 (ilustrasi tinta)
            └── src/          # generator V2 (satu geometri untuk semua view & ekspresi)
```

## Metode Produksi Visual (Draft V2)

Image generation tidak tersedia di lingkungan produksi saat ini, jadi draft dibuat dengan workflow ilustrasi SVG berbasis kode:

- Setiap garis adalah **goresan tinta**: garis tengah melalui titik kunci, dihaluskan dengan spline Catmull-Rom, lalu diberi profil ketebalan (ujung meruncing, lebih tebal di sisi bayangan kanan bawah).
- Kepala berbentuk **kurva organik** (kranium sedikit penuh, rahang lebih lembut), bukan lingkaran sempurna.
- Mata dibangun dari **kurva kelopak atas** dan **kurva bawah**; pupil terpotong kelopak sehingga terlihat half-lidded. Kantung mata tipis abu-abu memberi kesan sedikit lelah.
- Kaos digambar dari **kerangka stickman** (leher, bahu, sudut lengan, pinggul), dengan bukaan lengan, lipatan, dan sisi bayangan.
- Alternatif ke depan: image generation (jika tersedia) atau ilustrasi vektor manual. Hasil apa pun wajib mengikuti geometri dan aturan di dokumen ini.

## Geometri Draft (acuan konsistensi)

Satuan: radius kepala = 100. Semua view dan ekspresi memakai geometri yang sama dari generator draft. Nilai di bawah berasal dari V1; V2 memakai proporsi yang sama dengan garis bervariasi (outline kepala ±6,4, kelopak 11, alis 9,5 meruncing, lengan/kaki 6,6) dan palet V2 di master sheet.

| Bagian | Nilai |
|---|---|
| Tinggi total | ≈ 2,8 diameter kepala (kepala ≈ 36% tinggi) |
| Garis outline, lengan, kaki | 7 |
| Kelopak atas (ciri utama half-lidded) | 11 |
| Alis | 10, terpisah di atas kelopak |
| Mata | oval, posisi tetap; ekspresi hanya mengubah kelopak, pupil, alis, mulut |
| Tangan | bulat putih dengan outline |
| Kaki | garis hitam pendek, tanpa sepatu |

| Warna | Hex |
|---|---|
| Outline / mata / alis | `#1A1A1A` |
| Kepala & tangan | `#FFFFFF` |
| Kaos merah (casual) | `#D64541` |
| Kerah / bayangan kaos | `#A8322F` |
| Dalam mulut | `#7A2323` |

Untuk membuat ulang draft V2: `python3 characters/stick_figure/drafts/v2/src/generate_v2.py characters/stick_figure/drafts/v2` (butuh `numpy` dan `rsvg-convert`). V1: `python3 characters/stick_figure/drafts/src/generate_drafts.py characters/stick_figure/drafts`.
