#!/bin/bash
# Run the full 25-combination in-session power matrix (5 workloads x 5 variants).
set -x
WL="p00_random_s101_n1000 p10_random_s101_n1000 p30_random_s101_n1000 p60_random_s101_n1000 p90_random_s101_n1000"
for wl in $WL; do
  for n in 0 1 2 3 4; do
    ~/run_insession_power.sh "$wl" "$n" >> ~/matrix.log 2>&1
    echo "MATRIX done $wl B$n rc=$? $(grep -o 'injected [0-9]* driver pins' /home/research/b2_sky130/odo/acts_${wl}_B${n}.tcl.res 2>/dev/null || true)" >> ~/matrix_done.log
  done
done
echo "MATRIX-COMPLETE $(date +%T)" >> ~/matrix_done.log
grep '^Total' ~/b2_sky130/odo/*_power.txt | wc -l >> ~/matrix_done.log