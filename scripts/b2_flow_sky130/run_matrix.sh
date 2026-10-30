#!/bin/bash
# 5 variants x 4 sparsity: gate replay -> VCD truth -> propagated vs injected activity
set -u
STA=$HOME/opensta-part/OpenSTA-master/build/sta
LIB=/home/research/orfs-git/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
NL=/mnt/e/科研/B2_MAC_Followup/results_sky130/netlists
TB=/mnt/e/科研/B2_MAC_Followup/tb/tb_replay.sv
SDC=/mnt/e/科研/B2_MAC_Followup/flow_sky130/constraints.sdc
MODEL=$HOME/b2_sky130/models_flat/sky130_delayed.v
VEC=/mnt/e/科研/B2_MAC_Followup/data/gate_smoke
TRUTH=/mnt/e/科研/B2_MAC_Followup/flow_sky130/vcd_truth2.py
OUT=$HOME/act/matrix
mkdir -p "$OUT/vcd" "$OUT/run" "$OUT/log"

echo "=== compile ==="
for m in 0 1 2 3 4; do
  iverilog -g2012 -gspecify -s tb_replay -DDUT=mac_b$m -o "$OUT/tb$m.vvp" \
      "$NL/mac_b$m.v" "$MODEL" "$TB" 2> "$OUT/log/compile$m.log"
  echo "B$m compile=$?"
done

for m in 0 1 2 3 4; do
  for pct in 00 30 60 90; do
    tag=p${pct}_B${m}
    d="$OUT/run/$tag"
    mkdir -p "$d"
    cp "$VEC/p${pct}_random_s101_n1000.txt" "$OUT/vec_$tag.txt"
    vvp "$OUT/tb$m.vvp" +VECTORS="$OUT/vec_$tag.txt" +PERIOD=20 \
        +VCD="$OUT/vcd/$tag.vcd" > "$OUT/log/$tag.sim.log" 2>&1
    python3 "$TRUTH" "$NL/mac_b$m.v" "$OUT/vcd/$tag.vcd" 20020 20 "$d" \
        > "$OUT/log/$tag.truth.log" 2>&1

    for arm in prop inj; do
      if [ "$arm" = prop ]; then
        PRE="source $d/acts_reg.tcl"
      else
        PRE="source $d/acts_inj.tcl
source $d/acts_reg.tcl"
      fi
      cat > "$d/$arm.tcl" <<EOF
read_liberty $LIB
read_verilog $NL/mac_b$m.v
link_design mac_b$m
read_sdc $SDC
$PRE
foreach c [get_cells -hier *SDFFE*] {
  set full [get_full_name \$c]
  set short [string map {core. ""} \$full]
  if {[info exists ACT(\$short)]} {
    lassign \$ACT(\$short) a dd
    foreach p [get_pins -of_objects \$c] {
      if {[string match */Q [get_full_name \$p]]} { sta::set_power_pin_activity \$p \$a \$dd }
    }
  }
}
report_power -digits 6 > $d/power_$arm.txt
sta::report_activity_dump_cmd $d/dump_$arm.tsv
exit
EOF
      "$STA" -no_init -exit "$d/$arm.tcl" > "$OUT/log/$tag.$arm.log" 2>&1
    done
    echo "$tag $(grep -c 'user' $d/dump_inj.tsv 2>/dev/null) user_inj"
  done
done
echo "=== done ==="
