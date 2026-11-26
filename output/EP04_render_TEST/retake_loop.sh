#!/bin/sh
# Re-take expressive VO lines with new seeds until Whisper hears the script text (max 4 tries per round).
# usage: sh retake_loop.sh s11 s37 ...
P=/home/user/lemo-opuscar/.venv/bin/python; T=/home/user/tts-venv/bin/python
ids="$*"; seed=${SEED0:-3000}
for try in 1 2 3 4; do
  [ -z "$ids" ] && break
  echo "try $try seed $seed: $ids"
  (cd ../EP04_vo_expressive_TEST && SEED=$seed $T gen_expressive.py $ids > /dev/null 2>&1)
  $P build_vo_expr.py place > /dev/null
  $P -c "import json,sys; L=json.load(open('vo_expr/lines.json')); json.dump([l for l in L if l['id'] in sys.argv[1:]], open('vo_expr/_sub.json','w'))" $ids
  ids=$($P /home/user/lemo-opuscar/core/tts/asr_check.py vo_expr/_sub.json vo_expr/wav --lang en 2>/dev/null | awk '/^DIFF/{print $2}' | tr '\n' ' ')
  seed=$((seed + 1000))
done
echo "still failing: ${ids:-none}"
