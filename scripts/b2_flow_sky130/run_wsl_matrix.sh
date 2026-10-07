#!/bin/bash
# Full matrix step 3: injection + in-session power for all 240 combos
set -x
cd ~
WL=$(python3 -c "import json; print(' '.join(r['name'] for r in json.load(open('/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/data/gate_smoke/manifest.json'))))")
for wl in $WL; do
  for n in 0 1 2 3 4; do
    out="/home/research/b2_sky130/odo/${wl}_B${n}_power.txt"
    [ -s "$out" ] && { echo "SKIP ${wl}_B${n} (exists)"; continue; }
    ~/run_insession_power.sh "$wl" "$n" >> /mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/matrix_full_odo.log 2>&1
  done
done
echo "FULL-MATRIX-DONE $(date +%T)" >> /mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/matrix_full_odo.log