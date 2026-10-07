#!/bin/bash
# Fix-1: in-session extraction + read_spef for one variant. Verifies that the
# anonymous (net-id) SPEF maps inside an ODB session (unlike standalone STA).
set -x
FLOW="$HOME/orfs-git/flow"
LIB="$FLOW/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
RULES="$FLOW/platforms/sky130hd/rcx_patterns.rules"
n=$1
base="$FLOW/results/sky130hd/mac_b$n/base"
mkdir -p "$HOME/b2_sky130/fix1"
cat > "$HOME/b2_sky130/fix1/run.tcl" <<EOF
read_db $base/6_final.odb
read_sdc $base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $RULES
write_spef $HOME/b2_sky130/fix1/mac_b${n}_named.spef
read_spef $HOME/b2_sky130/fix1/mac_b${n}_named.spef
report_parasitic_annotation -report_unannotated > $HOME/b2_sky130/fix1/mac_b${n}_parasitic_coverage.txt
report_power > $HOME/b2_sky130/fix1/mac_b${n}_power_novcd.txt
EOF
cd "$FLOW" && openroad -exit "$HOME/b2_sky130/fix1/run.tcl" > "$HOME/b2_sky130/fix1/mac_b${n}_openroad.log" 2>&1
echo "OPENROAD-EXIT:$?"
grep -m2 '^\*D_NET' "$HOME/b2_sky130/fix1/mac_b${n}_named.spef"
head -4 "$HOME/b2_sky130/fix1/mac_b${n}_parasitic_coverage.txt"