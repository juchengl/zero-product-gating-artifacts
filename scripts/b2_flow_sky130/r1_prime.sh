#!/bin/bash
# R1-prime: re-run paper 1's glitch experiment with a SDF that ACTUALLY binds.
#
# Why: OpenROAD's write_sdf emits every delay as "(min::max)", leaving the min:typ:max
# *typ* slot empty. Icarus parses that spelling without complaint and then annotates
# nothing (sdf_iopath_delays() skips undefined typ values and vpi_put_delays() writes the
# existing delays back). So the Sept-18 R1 run was not SDF-annotated: the only delays it
# carried came from models_flat/sky130_delayed.v, whose specify blocks are a uniform
# "(A => Y) = (0.01, 0.01)" -- i.e. 10 ps per gate on every path, independent of
# fanout/wire load. This script changes ONLY the SDF text (typ slot filled); netlists,
# TB, vectors, period, window, activity injection and the OpenROAD session are identical
# to r1_glitch.sh, so the numbers are directly comparable to r1_glitch_compare.json.
#
# Usage: r1_prime.sh <sim|power|both>     (ASCII-only paths: vvp cannot $fopen non-ASCII)
set -u
PHASE=${1:-both}
P=/mnt/e/科研/B2_MAC_Followup
FLOW=$HOME/orfs-git/flow
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
RES="$FLOW/results/sky130hd"
NL="$P/results_sky130/netlists"
MODEL="$HOME/b2_sky130/models_flat/sky130_delayed.v"
TB="$P/tb/tb_replay.sv"
SDFDIR="$HOME/b2_sky130/sdf"
WORK="$HOME/b2_sky130/r1p"
FILL=/mnt/e/科研/B3_CHIP_IHP/scripts/sdf_fill_typ.py
mkdir -p "$WORK/vec" "$WORK/vcd" "$WORK/odo" "$WORK/sdf"

WLS="p00_random_s101_n1000 p30_random_s101_n1000 p60_random_s101_n1000 p90_random_s101_n1000"
for wl in $WLS; do cp "$P/data/gate_smoke/$wl.txt" "$WORK/vec/$wl.txt"; done

for n in 0 1 2 3 4; do
  [ -s "$SDFDIR/mac_b$n.sdf" ] || { echo "FATAL: missing $SDFDIR/mac_b$n.sdf"; exit 1; }
  python3 "$FILL" "$SDFDIR/mac_b$n.sdf" "$WORK/sdf/mac_b$n.sdf" --fill max || exit 1
done

if [ "$PHASE" = "sim" ] || [ "$PHASE" = "both" ]; then
  for n in 0 1 2 3 4; do
    iverilog -g2012 -gspecify -s tb_replay -DDUT=mac_b$n -o "$WORK/tb$n.vvp" \
        "$NL/mac_b$n.v" "$MODEL" "$TB" 2> "$WORK/compile$n.log" \
      || { echo "COMPILE-FAIL B$n"; tail -3 "$WORK/compile$n.log"; exit 1; }
  done
  for wl in $WLS; do
    for n in 0 1 2 3 4; do
      t0=$(date +%s)
      vvp "$WORK/tb$n.vvp" "+VECTORS=$WORK/vec/$wl.txt" "+PERIOD=20" \
          "+SDF=$WORK/sdf/mac_b$n.sdf" "+VCD=$WORK/vcd/${wl}_B$n.vcd" \
          > "$WORK/vcd/${wl}_B$n.run.log" 2>&1
      rc=$?; t1=$(date +%s)
      grep -q 'PASS replay' "$WORK/vcd/${wl}_B$n.run.log" || echo "SIM-FAIL $wl B$n rc=$rc"
      nwarn=$(grep -c 'SDF WARNING' "$WORK/vcd/${wl}_B$n.run.log")
      nerr=$(grep -c 'SDF ERROR' "$WORK/vcd/${wl}_B$n.run.log")
      python3 "$P/scripts/window_vcd.py" "$WORK/vcd/${wl}_B$n.vcd" \
              "$WORK/vcd/${wl}_B$n.window.vcd" --start-tick 60000 --end-tick 20080000 >/dev/null 2>&1
      # binding proof: a zero-delay run collapses onto a handful of timestamps, and the
      # old uniform-10 ps model puts every edge on a 10 ps grid; per-net SDF delays do not.
      stats=$(awk '
        /^#/{t=substr($0,2)+0; n[t]++; if (t % 10 != 0) off10++; tot++}
        END{printf "edges=%d distinct_t=%d off_10ps=%d", tot+0, length(n), off10+0}' \
              "$WORK/vcd/${wl}_B$n.window.vcd" 2>/dev/null)
      old=$(awk '/^#/{t=substr($0,2)+0; n[t]++; if (t % 10 != 0) off10++; tot++}
        END{printf "edges=%d distinct_t=%d off_10ps=%d", tot+0, length(n), off10+0}' \
              "$HOME/b2_sky130/r1/vcd/${wl}_B$n.window.vcd" 2>/dev/null)
      python3 "$P/flow_sky130/build_activity_tcl.py" "$RES/mac_b$n/base/6_final.v" \
              "$WORK/vcd/${wl}_B$n.window.vcd" "$WORK/odo/acts_${wl}_B$n.tcl" 20 20020 \
              > "$WORK/odo/acts_${wl}_B$n.log" 2>&1
      inj=$(tail -1 "$WORK/odo/acts_${wl}_B$n.log")
      echo "SIM $wl B$n rc=$rc elapsed=$((t1-t0))s SDFerr=$nerr SDFwarn=$nwarn | new[$stats] | old[$old] | $inj"
    done
  done
  echo "R1PRIME-SIM-COMPLETE"
fi

if [ "$PHASE" = "power" ] || [ "$PHASE" = "both" ]; then
  for wl in $WLS; do
    for n in 0 1 2 3 4; do
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
      echo "POW $wl B$n rc=$? $(grep '^Total' "$rd/power.txt" 2>/dev/null)"
    done
  done
  echo "R1PRIME-POWER-COMPLETE"
fi
