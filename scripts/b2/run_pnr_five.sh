#!/bin/bash
# Five-variant sky130hd PnR, aligned binaries. Strips the 'signed' keyword from
# the synthesized netlist before floorplan: OpenROAD 2.0-17598's Verilog reader
# rejects 'signed' declarations, and post-synthesis the signedness is already
# baked into the mapped cells, so stripping is semantics-preserving.
# Detached-run under nohup.
YOSYS=/usr/local/bin/yosys
OPENROAD=/usr/bin/openroad
STA=/usr/bin/sta
cd ~/orfs-git/flow || exit 1
for n in 0 1 2 3 4; do
  cfg=./designs/sky130hd/mac_b$n/config.mk
  res=results/sky130hd/mac_b$n/base
  echo "=== $(date +%T) SYNTH mac_b$n ==="
  make YOSYS_EXE=$YOSYS OPENROAD_EXE=$OPENROAD OPENSTA_EXE=$STA DESIGN_CONFIG=$cfg "$res/1_synth.v"
  rc=$?
  echo "=== SYNTH mac_b$n rc=$rc ==="
  if [ $rc -ne 0 ]; then echo "SYNTH-FAILED mac_b$n"; continue; fi
  sed -i 's/signed //g' "$res/1_synth.v"
  echo "=== $(date +%T) PNR mac_b$n ==="
  make YOSYS_EXE=$YOSYS OPENROAD_EXE=$OPENROAD OPENSTA_EXE=$STA DESIGN_CONFIG=$cfg "$res/6_final.def"
  rc=$?
  echo "=== PNR mac_b$n rc=$rc ==="
  if [ -f "$res/6_final.v" ] && [ -f "$res/6_final.spef" ]; then
    echo "=== ARTIFACTS-OK mac_b$n ==="
  else
    echo "=== ARTIFACTS-MISSING mac_b$n ==="
  fi
done
echo "RUN-COMPLETE $(date +%T)"
ls results/sky130hd/mac_b*/base/6_final.v 2>/dev/null | wc -l
