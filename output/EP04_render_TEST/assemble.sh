#!/bin/sh
# Assemble EP004: frames (24 fps) + VO -> MP4 (clean) and MP4 with burned-in subtitles, then QC.
set -e
cd "$(dirname "$0")"
VO=vo_expr/ep04_vo_expressive.wav  # expressive VO (Chatterbox, am_puck timbre), tight cut
N=$(ls frames/f*.png | wc -l)
echo "frames: $N"
# 1. picture + VO (clean, no subtitles)
ffmpeg -y -loglevel error -framerate 24 -i frames/f%05d.png -i "$VO" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  ep04_what_if_read_minds_16x9_clean.mp4
# 2. burned-in subtitles (Inter 46 px, text box 70 % of the width)
ffmpeg -y -loglevel error -i ep04_what_if_read_minds_16x9_clean.mp4 -vf "subtitles=ep04_subtitles.ass" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  ep04_what_if_read_minds_16x9_subtitled.mp4
# 3. QC
mkdir -p qc
for f in ep04_what_if_read_minds_16x9_clean.mp4 ep04_what_if_read_minds_16x9_subtitled.mp4; do
  echo "== $f"
  ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels -show_entries format=duration,size -of default=nw=1 "$f"
done
ffmpeg -nostats -i ep04_what_if_read_minds_16x9_subtitled.mp4 -vf blackdetect=d=0.5:pix_th=0.06 -af ebur128=peak=true -f null - 2>&1 | grep -E 'blackdetect|I:|Peak:' | tail -8
for t in 3 9 13 22 33 38 56 75 104 120 147 170 195 222 245 253; do
  ffmpeg -y -loglevel error -ss $t -i ep04_what_if_read_minds_16x9_subtitled.mp4 -frames:v 1 -vf scale=960:-1 qc/qc_$t.png
done
echo "qc frames in qc/"
