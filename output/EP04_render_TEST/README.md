# EP04 render — TEST

Render pertama Curious Mind EP004 "What If You Could Read Everyone's Mind?". Status: **TEST**, belum disetujui.

| File | Isi |
|---|---|
| `ep04_what_if_read_minds_16x9_subtitled.mp4` | 1920×1080, 24 fps, H.264 + AAC, ±4:15 (potongan padat), VO `am_puck` 1,1×, subtitle burn-in |
| `ep04_what_if_read_minds_16x9_clean.mp4` | Sama, tanpa subtitle |
| `ep04_subtitles.ass` / `.srt` | Subtitle (73 kemunculan) |
| `qc/` | Frame QC dari video akhir |

## Cara membuat ulang

```sh
node retime.mjs                              # timeline padat: shot berakhir tak lama setelah narasi (VO 1,1×) -> retime.json
python build_vo_fast.py                      # VO 1,1× (atempo) di posisi baru -> vo_fast/ (perlu numpy + soundfile)
python3 make_subs.py                         # subtitle ASS + SRT dari cues dan timestamp kata VO
node render_frames.mjs 0 11424 frames        # semua frame (atau dibagi ke beberapa proses paralel)
sh assemble.sh                               # encode, gabung VO, burn subtitle, QC
```

## Isi

- **Gambar:** modul storyboard di `../EP04_storyboard_frames_TEST/` (rig Milo v2 dari `curious-mind` 203bfc9; environment digambar dengan kode).
- **Animasi** (`episode.mjs`):
  - Setiap shot punya satu gerak kamera utama (push, pull, pan, tilt, roll).
  - Aksi karakter: jalan dengan siklus jalan rig, kaget yang tersentak cepat, pingsan, scroll ponsel dengan gesekan cepat, melambai, tangan di kepala, gelembung pikiran pop-in, barang jatuh, kucing berjalan pergi.
  - Line boil gambar tangan berganti setiap 3 frame.
- **Transisi** dari `plan.mjs`: whip pan (motion blur horizontal), zoom (push-through, snap zoom, crash zoom, rack focus, crane up), crash zoom out, tilt down, smash cut (kilat putih), cut ke hitam (sebelum intro), leaf wipe dan object wipe, serta cut keras untuk cut on action dan smash cut ke sunyi.
- **Subtitle:**
  - Font Inter 46 px, putih dengan outline gelap tipis dan bayangan lembut.
  - Kotak teks dibatasi **70% lebar frame** (margin kiri dan kanan 288 px), maksimal 2 baris, margin bawah 62 px.
  - Pada subtitle terpanjang, lebar teks terukur 42,5% frame.
- **Potongan padat (revisi 2026-11-26):** setiap shot berakhir sekitar 0,3 detik setelah narasinya, ditambah setengah transisi; aksi berjalan 1,1× agar sinkron dengan VO; shot dengan aksi visual sesudah narasi mendapat waktu minimum (`MIN_OLD`). Skala kamera dihitung dengan 4 desimal sehingga zoom halus.
- **Audio:** hanya VO. Belum ada musik dan SFX.
