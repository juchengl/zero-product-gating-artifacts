#!/bin/bash
# R2: layout-perturbation robustness. CORE_UTILIZATION 38/42 (base=40) x 5 variants,
# p90 workload, zero-delay pipeline. Compares hold-vs-force gap across layouts.
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
P=/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup
MODEL="$HOME/b2_sky130/models_flat/sky130_fd_sc_hd_selfcontained.v"
TB="$P/tb/tb_replay.sv"
WORK="$HOME/b2_sky130/r2"
mkdir -p "$WORK/vcd" "$WORK/odo"
cd "$FLOW" || exit 1
WL=p90_random_s101_n1000
for U in 38 42; do
  FV="u$U"
  for n in 0 1 2 3 4; do
    cfg="./designs/sky130hd/mac_b$n/config.mk"
    res="results/sky130hd/mac_b$n/$FV"
    make YOSYS_EXE=/usr/local/bin/yosys OPENROAD_EXE=/usr/bin/openroad OPENSTA_EXE=/usr/bin/sta \
         FLOW_VARIANT=$FV CORE_UTILIZATION=$U EQUIVALENCE_CHECK=0 DESIGN_CONFIG=$cfg "$res/1_synth.v" > /dev/null 2>&1 || { echo "SYNTH-FAIL u$U B$n"; continue; }
    sed -i 's/signed //g' "$res/1_synth.v"
    make YOSYS_EXE=/usr/local/bin/yosys OPENROAD_EXE=/usr/bin/openroad OPENSTA_EXE=/usr/bin/sta \
         FLOW_VARIANT=$FV CORE_UTILIZATION=$U EQUIVALENCE_CHECK=0 DESIGN_CONFIG=$cfg "$res/6_final.def" > /dev/null 2>&1 || { echo "PNR-FAIL u$U B$n"; continue; }
    # stripped netlist copy for simulation
    sed 's/\\core\./\\/g' "$res/6_final.v" > "$HOME/b2_sky130/r2/mac_b${n}_u$U.v"
    # gate replay (zero-delay) on p90
    iverilog -g2012 -gspecify -s tb_replay -DDUT=mac_b$n -o "$WORK/tb${n}_u$U.vvp" \
        "$HOME/b2_sky130/r2/mac_b${n}_u$U.v" "$MODEL" "$TB" 2>> "$WORK/compile.log" || { echo "IC-FAIL u$U B$n"; continue; }
    vvp "$WORK/tb${n}_u$U.vvp" "+VECTORS=$HOME/b2_sky130/r1/vec/$WL.txt" "+PERIOD=20" \
        "+VCD=$WORK/vcd/${WL}_B${n}_u$U.vcd" > /dev/null 2>&1
    grep -q 'PASS replay' "$WORK/vcd/${WL}_B${n}_u$U.run.log" 2>/dev/null || true
    python3 "$P/scripts/window_vcd.py" "$WORK/vcd/${WL}_B${n}_u$U.vcd" "$WORK/vcd/${WL}_B${n}_u$U.window.vcd" \
        --start-tick 60000 --end-tick 20080000 > /dev/null 2>&1
    # activity inject + in-session power
    python3 "$P/flow_sky130/build_activity_tcl.py" "$res/6_final.v" "$WORK/vcd/${WL}_B${n}_u$U.window.vcd" \
        "$WORK/odo/acts_${WL}_B${n}_u$U.tcl" 20 20020 > /dev/null 2>&1
    rd="$WORK/odo/${WL}_B${n}_u$U"; mkdir -p "$rd"
    cat > "$WORK/odo/run_${WL}_B${n}_u$U.tcl" <<EOF
read_db $res/6_final.odb
read_liberty $LIB
read_sdc $res/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/odo/acts_${WL}_B${n}_u$U.tcl
report_power > $rd/power.txt
EOF
    openroad -exit "$WORK/odo/run_${WL}_B${n}_u$U.tcl" > "$rd/session.log" 2>&1
    echo "R2 done u$U B$n $(grep '^Total' "$rd/power.txt" 2>/dev/null)"
  done
done
echo "R2-COMPLETE $(date +%T)"