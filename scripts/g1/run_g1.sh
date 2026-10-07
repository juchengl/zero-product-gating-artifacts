#!/bin/bash
# B3-S3.2 G1 net-benefit pipeline: one netlist, four mode_cfg configs.
#   stage sdf  : in-session SDF for the post-route netlist (once)
#   stage run  : per config -> gate-level sim -> activity tcl -> in-session power
# The per-config loop deletes each windowed VCD once its power report exists.
# A gate-level VCD is ~620 MB, so a 12-point grid would otherwise put ~7 GB on
# the WSL vhdx, which grows C: and never auto-shrinks.
# Usage: run_g1.sh <sdf|run> ; config list below.
set -u
B3=/mnt/e/科研/B3_CHIP_IHP
FLOW=$HOME/orfs-git/flow
BASE=$FLOW/results/sky130hd/b3_chip/base
PLAT=$FLOW/platforms/sky130hd
LIB=$PLAT/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
RULES=$PLAT/rcx_patterns.rules
WORK=$HOME/b3_ihp/g1
ARCH="/mnt/e/科研/WSL工作区/g1"
MODELS=$HOME/b2_sky130/models_flat/sky130_delayed.v
ACTB="$B3/scripts/build_activity_tcl.py"   # B3 copy: CELL_PREFIX param + <2% guard (default sky130)
RUN_CYC=600
DUMP_ON=100
DUMP_OFF=600
# TB clock: tb_chip_top.sv is `timescale 1ns/1ps` + `always #5 clk = ~clk`, i.e.
# 10 ns/cycle = 100 MHz, while every SDC here says create_clock -period 20.0.
# The 2026-09-21 grid therefore profiled the chip at 2x its constrained rate, and
# build_activity_tcl.py was handed the window's END time (12000 ns) as `window_ns`
# instead of its duration (5000 ns) -- both are quantified in docs/S3.2
# ("绝对功耗刻度更正") and by scripts/g1_window_rescale.py.
# Default now matches the SDC; TB_HALF_NS=5 reproduces the 2026-09-21 run exactly.
TB_HALF_NS=${TB_HALF_NS:-10}
NS_PER_CYCLE=$((2 * TB_HALF_NS))
STAGE=${1:-run}

# configs: name mode_cfg force_en T pat_p
# pat_p quantizes P(zero word) to pat_p/16 (chip_top pat_gen: make_zero =
# sample < pat_p, sample uniform over 0..15). Verified with pat_sparsity.py:
#   p30 -> 5 (31.02%)   p60 -> 10 (62.40%)   p90 -> 14 (87.47%)
# p30/T4 (all four variants) is already measured; this grid fills the gap the
# G1 decision rested on: whether ADAPTIVE beats static HOLD at long zero runs.
# b2 (sticky FORCE) is omitted -- it lost to B3 at p30 and is not on the
# criterion's critical path (auto must beat the best static, which was B3).
CONFIGS=(
  "p60T4_b0    1 0  4 10"
  "p60T4_b3    2 0  4 10"
  "p60T4_auto  0 1  4 10"
  "p60T16_b0   1 0 16 10"
  "p60T16_b3   2 0 16 10"
  "p60T16_auto 0 1 16 10"
  "p90T4_b0    1 0  4 14"
  "p90T4_b3    2 0  4 14"
  "p90T4_auto  0 1  4 14"
  "p90T16_b0   1 0 16 14"
  "p90T16_b3   2 0 16 14"
  "p90T16_auto 0 1 16 14"
)

mkdir -p $WORK $ARCH

if [ "$STAGE" = "sdf" ]; then
  cat > $WORK/gen_sdf.tcl <<EOF
read_db $BASE/6_final.odb
read_liberty $LIB
read_sdc $BASE/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
write_sdf $WORK/b3_chip.sdf
EOF
  cd $FLOW && openroad -exit $WORK/gen_sdf.tcl > $WORK/gen_sdf.log 2>&1
  echo "SDF exit=$? size=$(wc -c < $WORK/b3_chip.sdf 2>/dev/null)"
fi

if [ "$STAGE" = "run" ]; then
  sed -i 's/\r$//' $B3/tb/tb_chip_top.sv $B3/scripts/gen_g1_stim.py
  # gate netlist is flattened: drop the RTL parameter override in the TB and
  # rename the module to tb_replay (build_activity_tcl.py matches scope
  # tb_replay->dut, the B2 pipeline convention)
  sed -e 's/chip_top #(.N(8), .TW(8)) dut (/chip_top dut (/' \
      -e 's/module tb_chip_top;/module tb_replay;/' \
      -e "s/always #5 clk = ~clk;/always #${TB_HALF_NS} clk = ~clk;/" \
      $B3/tb/tb_chip_top.sv > $WORK/tb_gate_chip.sv
  # sed -i above rewrites the TB unconditionally, so mtimes are useless for
  # staleness; hash the actual compiler inputs instead. Recompiling costs ~3 min.
  sig=$(cat $WORK/tb_gate_chip.sv $BASE/6_final.v | md5sum | cut -d' ' -f1)
  if [ ! -f $WORK/sim_gate.vvp ] || [ "$(cat $WORK/sim_gate.sig 2>/dev/null)" != "$sig" ]; then
    echo "compiling sim_gate.vvp (sig=$sig) ..."
    iverilog -g2012 -gspecify -I $HOME/b2_sky130/models_flat \
      -o $WORK/sim_gate.vvp \
      $WORK/tb_gate_chip.sv $BASE/6_final.v $MODELS || exit 1
    echo "$sig" > $WORK/sim_gate.sig
  else
    echo "reusing sim_gate.vvp (inputs unchanged, sig=$sig)"
  fi

  # build_activity_tcl.py wants (period_ns, window_DURATION_ns); activity is
  # computed as transitions/window, so the second argument must be the dumped
  # duration, not the dump-off timestamp.
  ACT_T0=$((DUMP_ON * NS_PER_CYCLE))
  ACT_T1=$((DUMP_OFF * NS_PER_CYCLE))
  ACT_WINDOW=$((ACT_T1 - ACT_T0))
  echo "clock ${NS_PER_CYCLE} ns/cycle; activity window ${ACT_WINDOW} ns (${DUMP_ON}..${DUMP_OFF})"
  for c in "${CONFIGS[@]}"; do
    set -- $c
    name=$1; mc=$2; fe=$3; T=$4; p=$5
    echo "=== $name (mode_cfg=$mc force_en=$fe T=$T pat_p=$p) ==="

    python3 $B3/scripts/gen_g1_stim.py $mc $fe $T $p $RUN_CYC $WORK/stim_$name.txt
    vvp $WORK/sim_gate.vvp +STIM=$WORK/stim_$name.txt +OUT=$WORK/out_$name.txt \
        +VCD=$WORK/win_$name.vcd +DUMPON=$DUMP_ON +DUMPOFF=$DUMP_OFF \
        +SDF=$WORK/b3_chip.sdf > $WORK/sim_$name.log 2>&1
    echo "SIM $name exit=$? vcd=$(wc -c < $WORK/win_$name.vcd 2>/dev/null)"

    python3 "$ACTB" $BASE/6_final.v $WORK/win_$name.vcd \
      $WORK/acts_$name.tcl $NS_PER_CYCLE $ACT_WINDOW > $WORK/acts_$name.log 2>&1
    tail -1 $WORK/acts_$name.log

    cat > $WORK/pow_$name.tcl <<EOF
read_liberty $LIB
read_db $BASE/6_final.odb
read_sdc $BASE/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
source $WORK/acts_$name.tcl
report_power > $WORK/power_$name.txt
EOF
    cd $FLOW && openroad -exit $WORK/pow_$name.tcl > $WORK/pow_$name.log 2>&1
    rc=$?
    echo "POW $name exit=$rc total=$(grep '^Total' $WORK/power_$name.txt 2>/dev/null)"

    # keep the VCD if power failed, so the config can be retried without a
    # ~25 min re-simulation; archive the small durable outputs to E:
    if [ $rc -eq 0 ] && grep -q '^Total' $WORK/power_$name.txt; then
      rm -f $WORK/win_$name.vcd
      cp -f $WORK/power_$name.txt $WORK/acts_$name.log $WORK/sim_$name.log \
            $WORK/stim_$name.txt $WORK/out_$name.txt $ARCH/ 2>/dev/null
      echo "ARCH $name ok, vcd removed"
    else
      echo "ARCH $name FAILED, vcd retained for retry"
    fi
  done
  echo "GRID_DONE $(date)"
fi
