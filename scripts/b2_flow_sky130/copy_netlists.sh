#!/bin/bash
for n in 0 1 2 3 4; do
  cp "$HOME/b2_sky130/mac_b${n}_pnr.v" "/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/netlists/mac_b${n}.v"
done
ls -la "/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/netlists/"
