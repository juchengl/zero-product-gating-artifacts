#!/bin/bash
# C3/D1: map the five B2 MAC variants to sky130hd and run static timing.
# Run inside WSL: bash /mnt/c/.../flow_sky130/map_and_sta.sh
set -uo pipefail
PROJ="/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup"
ORFS="$HOME/orfs-git"
LIB="$ORFS/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
WORK="$HOME/b2_sky130"
OUT="$PROJ/results_sky130"
PERIOD_PS=20000

mkdir -p "$WORK" "$OUT"
cp "$PROJ/rtl/mac.sv" "$WORK/mac.sv"

for n in 0 1 2 3 4; do
  top="mac_b$n"
  echo "=== mapping $top ==="
  yosys -p "
    read_liberty -lib $LIB;
    read_verilog -sv $WORK/mac.sv;
    synth -top $top -flatten;
    dfflibmap -liberty $LIB;
    abc -liberty $LIB -D $PERIOD_PS;
    setundef -zero;
    opt_clean -purge;
    check -assert;
    tee -o $WORK/${top}_stat.json stat -json -liberty $LIB;
    write_verilog -noattr $WORK/${top}_netlist.v;" > "$WORK/${top}_yosys.log" 2>&1
  # OpenSTA's Verilog reader rejects the 'signed' keyword; post-mapping the
  # signedness is already baked into the cell structure, so stripping it is safe.
  sed -i 's/signed //g' "$WORK/${top}_netlist.v"
  if [ $? -ne 0 ]; then echo "YOSYS-FAILED $top"; tail -20 "$WORK/${top}_yosys.log"; exit 1; fi

  LIB="$LIB" NETLIST="$WORK/${top}_netlist.v" TOP="$top" SDC="$PROJ/flow_sky130/constraints.sdc" \
    sta -exit "$PROJ/flow_sky130/sta_checks.tcl" > "$WORK/${top}_sta.log" 2>&1
  if [ $? -ne 0 ]; then echo "STA-FAILED $top"; tail -20 "$WORK/${top}_sta.log"; exit 1; fi
  echo "=== done $top ==="
done

python3 "$PROJ/flow_sky130/collect_summary.py" "$WORK" "$OUT"
