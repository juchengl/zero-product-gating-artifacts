#!/bin/bash
# R3: corner sweep. 3 corners (tt/ff/ss from the same volare build) x 5 variants, p90.
# Reuses existing activity injection files. Extraction is geometry-based (same caps).
set -x
FLOW="$HOME/orfs-git/flow"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
RES="$FLOW/results/sky130hd"
PDK="$HOME/b2_sky130/pdk_hd/sky130B/libs.ref/sky130_fd_sc_hd/lib"
WORK="$HOME/b2_sky130"
P=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup
WL=p90_random_s101_n1000
CORNERS="tt_025C_1v80 ff_100C_1v95 ss_100C_1v60"
for C in $CORNERS; do
  LIB="$PDK/sky130_fd_sc_hd__$C.lib"
  [ -f "$LIB" ] || { echo "MISSING LIB $C"; continue; }
  for n in 0 1 2 3 4; do
    rd="$WORK/odo/corner_${C}_B${n}"; mkdir -p "$rd"
    cat > "$WORK/odo/run_corner_${C}_B${n}.tcl" <<EOF
read_db $RES/mac_b$n/base/6_final.odb
read_liberty $LIB
read_sdc $RES/mac_b$n/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${WL}_B${n}.tcl
report_power -digits 6 > $rd/power.txt
EOF
    openroad -exit "$WORK/odo/run_corner_${C}_B${n}.tcl" > "$rd/session.log" 2>&1
    echo "R3 done $C B$n $(grep '^Total' "$rd/power.txt" 2>/dev/null | awk '{print $5}')"
  done
done
echo "R3-COMPLETE $(date +%T)"