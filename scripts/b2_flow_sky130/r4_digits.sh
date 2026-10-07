#!/bin/bash
# R4: re-run p90 base in-session power with report_power -digits 6 (higher resolution).
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
RES="$FLOW/results/sky130hd"
WORK="$HOME/b2_sky130"
WL=p90_random_s101_n1000
for n in 0 1 2 3 4; do
  rd="$WORK/odo/${WL}_B${n}_digits6"; mkdir -p "$rd"
  cat > "$WORK/odo/run_${WL}_B${n}_d6.tcl" <<EOF
read_db $RES/mac_b$n/base/6_final.odb
read_liberty $LIB
read_sdc $RES/mac_b$n/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${WL}_B${n}.tcl
report_power -digits 6 > $rd/power.txt
EOF
  openroad -exit "$WORK/odo/run_${WL}_B${n}_d6.tcl" > "$rd/session.log" 2>&1
  echo "R4 done B$n $(grep '^Total' "$rd/power.txt" 2>/dev/null)"
done
echo "R4-COMPLETE"