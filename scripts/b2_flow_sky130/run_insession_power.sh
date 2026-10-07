#!/bin/bash
# Fix-2 pilot: in-session OpenROAD power with ODB-named VCD activity + real
# in-session extraction. Args: <workload> <variant_index>
set -x
WL=$1
n=$2
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
base="$FLOW/results/sky130hd/mac_b$n/base"
WORK="$HOME/b2_sky130"
PROJ="/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup"
WINDIR="$PROJ/results/replay_gate_gate_smoke"
mkdir -p "$WORK/odo"
python3 "$PROJ/flow_sky130/build_activity_tcl.py" "$base/6_final.v" "$WINDIR/${WL}_B${n}.window.vcd" "$WORK/odo/acts_${WL}_B${n}.tcl" 20 20020
cat > "$WORK/odo/run_${WL}_B${n}.tcl" <<EOF
read_liberty $LIB
read_db $base/6_final.odb
read_sdc $base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${WL}_B${n}.tcl
report_power > $WORK/odo/${WL}_B${n}_power.txt
EOF
cd "$FLOW" && openroad -exit "$WORK/odo/run_${WL}_B${n}.tcl" > "$WORK/odo/${WL}_B${n}_session.log" 2>&1
echo "EXIT:$?"
tail -1 "$WORK/odo/acts_${WL}_B${n}.tcl" 2>/dev/null
grep '^Total' "$WORK/odo/${WL}_B${n}_power.txt"