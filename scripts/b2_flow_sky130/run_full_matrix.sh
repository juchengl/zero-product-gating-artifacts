#!/bin/bash
# Full 48x5 matrix pipeline: gate replay (keep VCD) -> trim -> in-session power.
# Detached: survives session drops.
set -x
PROJ="/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup"
VCD_DIR="$PROJ/results/replay_gate_gate_smoke"
MANIFEST="$PROJ/data/gate_smoke/manifest.json"
NETLIST_DIR="$PROJ/results_sky130/netlists"
MODEL="$PROJ/results_sky130/models_flat/sky130_fd_sc_hd_selfcontained.v"
# Step 1: replay ALL 48 workloads x 5 variants, keep VCDs
cd "$PROJ" || exit 1
python scripts/replay.py --netlist-dir "$NETLIST_DIR" --cells "$MODEL" \
    --manifest "$MANIFEST" --keep-vcd >> "$PROJ/gate_replay_full.log" 2>&1
rc=$?
echo "GATE-REPLAY-EXIT:$rc" >> "$PROJ/gate_replay_full.log"
[ $rc -ne 0 ] && exit 1
# Step 2: trim all VCDs to measurement window
for f in "$VCD_DIR"/*_B?.vcd; do
  out="${f%.vcd}.window.vcd"
  python scripts/window_vcd.py "$f" "$out" --start-tick 60000 --end-tick 20080000 >> "$PROJ/trim.log" 2>&1
done
echo "TRIM-DONE" >> "$PROJ/trim.log"
# Step 3: injection + in-session power per (workload, variant)
WL_LIST=$(python3 -c "import json; ms=json.load(open('$MANIFEST')); print(' '.join(r['name'] for r in ms))")
for wl in $WL_LIST; do
  for n in 0 1 2 3 4; do
    ~/run_insession_power.sh "$wl" "$n" >> "$PROJ/matrix_full_odo.log" 2>&1
  done
done
echo "FULL-MATRIX-COMPLETE $(date +%T)" >> "$PROJ/matrix_full_odo.log"
# Step 4: collect into final table
python3 "$PROJ/flow_sky130/collect_phase2.py" ~/b2_sky130/odo "$PROJ/results_sky130" >> "$PROJ/collect_full.log" 2>&1
echo "COLLECT-DONE" >> "$PROJ/collect_full.log"