#!/bin/bash
# R4c: full p00 digits6 set (9 workloads x B0/B1/B4) for a precise mean detection cost.
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
RES="$FLOW/results/sky130hd"
WORK="$HOME/b2_sky130"
P=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup
WL=$(python3 -c "import json; print(' '.join(r['name'] for r in json.load(open('$P/data/gate_smoke/manifest.json')) if r['name'].startswith('p00_')))")
for wl in $WL; do
  for n in 0 1 4; do
    rd="$WORK/odo/${wl}_B${n}_digits6"; mkdir -p "$rd"
    [ -s "$rd/power.txt" ] && continue
    cat > "$WORK/odo/run_${wl}_B${n}_d6.tcl" <<EOF
read_db $RES/mac_b$n/base/6_final.odb
read_liberty $LIB
read_sdc $RES/mac_b$n/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${wl}_B${n}.tcl
report_power -digits 6 > $rd/power.txt
EOF
    openroad -exit "$WORK/odo/run_${wl}_B${n}_d6.tcl" > "$rd/session.log" 2>&1
  done
done
echo "R4c-COMPLETE"