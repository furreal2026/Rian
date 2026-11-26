# EP04 VO — am_puck — TEST

Voice-over TTS untuk Curious Mind EP004 "What If You Could Read Everyone's Mind?". Status: **TEST**, belum disetujui.
Naskah: `episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/SCRIPT_VO.md`. Sumber: `episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/CURIOUS_MIND_EP004_FINAL_STORYBOARD.docx`.

| File | Isi |
|---|---|
| `ep04_vo_am_puck_timed.wav` | Track VO 7:50, setiap baris di slot shot-nya. 48 kHz mono, -16 LUFS, true peak -1,5 dBFS |
| `ep04_vo_am_puck_timed_preview.mp3` | Pratinjau MP3 192 kbps dari track yang sama |
| `ep04_vo_am_puck.srt` | Subtitle English, timecode sama dengan track |
| `wav/s01.wav … s41.wav` | Satu WAV per baris (24 kHz, tanpa efek pikiran), dan `dur.json` |
| `wav/words.json` | Timestamp per kata dari Whisper (untuk timing animasi) |
| `cues.json` | Posisi setiap baris di track (mulai, selesai, shot) |
| `shots.json` | Timecode dan narasi per shot, diambil dari storyboard |
| `lines.json` | Input TTS (suara, tempo, potongan untuk s06 dan s40b) |

## Membuat ulang

Dari folder ini, dengan voice tier Lemo-Opuscar terpasang (`sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice`):

```sh
LIB=/home/user/lemo-opuscar
pandoc ../../episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/CURIOUS_MIND_EP004_FINAL_STORYBOARD.docx -t gfm -o storyboard.md
python3 parse_storyboard.py storyboard.md shots.json
python3 make_lines.py                                   # lalu terapkan potongan s06/s40b dari lines.json
$LIB/.venv/bin/python $LIB/core/tts/tts.py lines.json wav
$LIB/.venv/bin/python $LIB/core/tts/asr_check.py lines.json wav --lang en
$LIB/.venv/bin/python build_timed_vo.py
```

`make_lines.py` menulis ulang `lines.json` tanpa potongan s06/s40b. Kedua baris itu dirakit dari beberapa klip (lihat field `parts` di `lines.json` dan catatan di SCRIPT_VO.md).
