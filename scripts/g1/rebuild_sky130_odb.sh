#!/bin/bash
# Rebuild sky130hd/b3_chip 6_final.odb from the surviving 6_final.def.
# run_g1.sh stages sdf/pow do `read_db 6_final.odb`; the odb was removed by the
# 2026-09-21 cleanup while def/v/spef/gds were kept, so reconstruct it here.
set -u
FLOW=$HOME/orfs-git/flow
PLAT=$FLOW/platforms/sky130hd
BASE=$FLOW/results/sky130hd/b3_chip/base
WORK=$HOME/b3_ihp/repair

mkdir -p $WORK
cat > $WORK/rebuild_odb.tcl <<EOF
read_lef $PLAT/lef/sky130_fd_sc_hd.tlef
read_lef $PLAT/lef/sky130_fd_sc_hd_merged.lef
read_liberty $PLAT/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_def $BASE/6_final.def
read_sdc $BASE/6_1_fill.sdc
write_db $BASE/6_final.odb
EOF

cd $FLOW && openroad -exit $WORK/rebuild_odb.tcl > $WORK/rebuild_odb.log 2>&1
rc=$?
echo "rebuild exit=$rc"
tail -15 $WORK/rebuild_odb.log
ls -la $BASE/6_final.odb 2>&1
exit $rc
