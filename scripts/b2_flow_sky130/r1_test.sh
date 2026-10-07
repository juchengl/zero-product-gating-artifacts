#!/bin/bash
# R1 test: compile netlist + delayed model + tb, annotate SDF, run one workload.
set -x
cd ~/orfs-git/flow 2>/dev/null; cd ~
M=~/b2_sky130/models_flat/sky130_delayed.v
NL=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/netlists
TB=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/tb/tb_replay.sv
SDF=~/b2_sky130/sdf/mac_b3.sdf
VEC=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/data/gate_smoke
OUT=~/b2_sky130/r1test
mkdir -p "$OUT"
# find a vector file for p90_random_s101
VFILE=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/data/gate_smoke/p90_random_s101_n1000.txt
echo "VFILE=$VFILE"
iverilog -g2012 -gspecify -s tb_replay -DDUT=mac_b3 -o "$OUT/tb3.vvp" "$NL/mac_b3.v" "$M" "$TB" 2> "$OUT/compile.log"
echo "COMPILE_EXIT=$?"; tail -5 "$OUT/compile.log"
vvp "$OUT/tb3.vvp" "+VECTORS=$VFILE" "+PERIOD=20" "+SDF=$SDF" "+VCD=$OUT/p90_B3_sdf.vcd" > "$OUT/run.log" 2>&1
echo "RUN_EXIT=$?"; grep -c 'PASS replay' "$OUT/run.log"; grep -ci 'sdf\|cannot\|warning' "$OUT/run.log" | head; tail -3 "$OUT/run.log"
ls -la "$OUT/p90_B3_sdf.vcd" 2>/dev/null