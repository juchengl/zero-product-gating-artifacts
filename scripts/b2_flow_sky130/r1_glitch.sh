#!/bin/bash
# R1 glitch-true pipeline: SDF-annotated gate sim -> trim -> activity inject -> in-session power.
# ASCII-only paths (WSL vvp cannot $fopen non-ASCII paths).
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
RES="$FLOW/results/sky130hd"
P=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup
NL="$P/results_sky130/netlists"
MODEL="$HOME/b2_sky130/models_flat/sky130_delayed.v"
TB="$P/tb/tb_replay.sv"
SDFDIR="$HOME/b2_sky130/sdf"
WORK="$HOME/b2_sky130/r1"
mkdir -p "$WORK/vec" "$WORK/vcd" "$WORK/odo"
WLS="p00_random_s101_n1000 p30_random_s101_n1000 p60_random_s101_n1000 p90_random_s101_n1000"
for wl in $WLS; do cp "$P/data/gate_smoke/$wl.txt" "$WORK/vec/$wl.txt"; done
for n in 0 1 2 3 4; do
  iverilog -g2012 -gspecify -s tb_replay -DDUT=mac_b$n -o "$WORK/tb$n.vvp" "$NL/mac_b$n.v" "$MODEL" "$TB" 2> "$WORK/compile$n.log" || { echo "COMPILE-FAIL B$n"; tail -3 "$WORK/compile$n.log"; exit 1; }
done
for wl in $WLS; do
  for n in 0 1 2 3 4; do
    vvp "$WORK/tb$n.vvp" "+VECTORS=$WORK/vec/$wl.txt" "+PERIOD=20" "+SDF=$SDFDIR/mac_b$n.sdf" "+VCD=$WORK/vcd/${wl}_B$n.vcd" > "$WORK/vcd/${wl}_B$n.run.log" 2>&1
    grep -q 'PASS replay' "$WORK/vcd/${wl}_B$n.run.log" || echo "SIM-FAIL $wl B$n"
    python3 "$P/scripts/window_vcd.py" "$WORK/vcd/${wl}_B$n.vcd" "$WORK/vcd/${wl}_B$n.window.vcd" --start-tick 60000 --end-tick 20080000 > /dev/null 2>&1
  done
done
for wl in $WLS; do
  for n in 0 1 2 3 4; do
    python3 "$P/flow_sky130/build_activity_tcl.py" "$RES/mac_b$n/base/6_final.v" "$WORK/vcd/${wl}_B$n.window.vcd" "$WORK/odo/acts_${wl}_B$n.tcl" 20 20020 > /dev/null 2>&1
    rd="$WORK/odo/${wl}_B$n"; mkdir -p "$rd"
    cat > "$WORK/odo/run_${wl}_B$n.tcl" <<EOF
read_db $RES/mac_b$n/base/6_final.odb
read_liberty $LIB
read_sdc $RES/mac_b$n/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${wl}_B$n.tcl
report_power > $rd/power.txt
EOF
    openroad -exit "$WORK/odo/run_${wl}_B$n.tcl" > "$rd/session.log" 2>&1
    inj=$(grep -o 'injected [0-9]*' "$WORK/odo/acts_${wl}_B$n.tcl" | head -1)
    echo "done $wl B$n $(grep '^Total' "$rd/power.txt" 2>/dev/null)"
  done
done
echo "R1-COMPLETE"