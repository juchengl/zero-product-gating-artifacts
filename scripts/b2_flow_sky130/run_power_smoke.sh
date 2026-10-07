#!/bin/bash
# D3 phase-1: OpenSTA post-route power for 5 workloads x 5 variants.
# Netlist: ORFS 6_final.v copied with the "core." flat-name prefix stripped.
# VCD: window-trimmed RTL replay VCD reshaped by vcd_reshape.py (flat names,
# vector vars expanded). Evidence: activity-propagated post-route estimate;
# NOT SDF gate-level simulation. Label accordingly downstream.
set -x
PROJ="/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup"
LIB="$HOME/orfs-git/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RES="$HOME/orfs-git/flow/results/sky130hd"
VCD_DIR="$PROJ/results/replay_rtl_gate_smoke"
OUT="$PROJ/results_sky130/power_smoke"
WORK="$HOME/b2_sky130"
WL="p00_random_s101_n1000 p10_random_s101_n1000 p30_random_s101_n1000 p60_random_s101_n1000 p90_random_s101_n1000"
PY3=python3

mkdir -p "$OUT"
# Prepare per-variant netlist copies with the flat "core." prefix stripped.
for n in 0 1 2 3 4; do
  sed 's/\\core\./\\/g' "$RES/mac_b$n/base/6_final.v" > "$WORK/mac_b${n}_pnr.v"
done
# Reshape the trimmed VCDs once per variant/workload.
for wl in $WL; do
  for n in 0 1 2 3 4; do
    $PY3 "$PROJ/flow_sky130/vcd_reshape.py" "$VCD_DIR/${wl}_B${n}.window.vcd" "$WORK/${wl}_B${n}.rsvcd"
  done
done

for wl in $WL; do
  for n in 0 1 2 3 4; do
    rd="$OUT/${wl}_B${n}"
    mkdir -p "$rd"
    LIBERTY_FILES="$LIB" \
    NETLIST="$WORK/mac_b${n}_pnr.v" \
    TOP="mac_b$n" \
    SDC="$RES/mac_b$n/base/6_1_fill.sdc" \
    SPEF="$RES/mac_b$n/base/6_final.spef" \
    VCD="$WORK/${wl}_B${n}.rsvcd" \
    REPORT_DIR="$rd" \
    sta -exit "$PROJ/flow/power.tcl" > "$rd.log" 2>&1
    ann=$(grep -o 'Annotated [0-9]* pin activities' "$rd.log" | head -1)
    echo "done $wl B$n rc=$? $ann"
  done
done
echo "POWER-RUNS-COMPLETE"
ls "$OUT"/*/power.txt 2>/dev/null | wc -l
