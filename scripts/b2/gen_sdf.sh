#!/bin/bash
# R1 step A: generate post-route SDF for each variant (in-session extraction).
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
OUT="$HOME/b2_sky130/sdf"
mkdir -p "$OUT"
cd "$FLOW" || exit 1
for n in 0 1 2 3 4; do
  base="$FLOW/results/sky130hd/mac_b$n/base"
  cat > "$OUT/gen_$n.tcl" <<EOF
read_db $base/6_final.odb
read_liberty $LIB
read_sdc $base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
write_sdf $OUT/mac_b$n.sdf
EOF
  openroad -exit "$OUT/gen_$n.tcl" > "$OUT/gen_$n.log" 2>&1
  echo "mac_b$n sdf exit=$? size=$(wc -c < $OUT/mac_b$n.sdf 2>/dev/null)"
done
head -20 "$OUT/mac_b0.sdf" 2>/dev/null