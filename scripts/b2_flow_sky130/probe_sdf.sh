#!/bin/bash
SDF=~/b2_sky130/sdf/mac_b0.sdf
echo "=== IOPATH sample (inv_1) ==="
grep -A8 'CELLTYPE "sky130_fd_sc_hd__inv_1"' "$SDF" | head -12
echo "=== distinct cell types ==="
grep -o 'CELLTYPE "sky130_fd_sc_hd__[a-z0-9_]*"' "$SDF" | sed 's/CELLTYPE //; s/"//g' | sort -u
echo "=== count ==="
grep -o 'CELLTYPE "sky130_fd_sc_hd__[a-z0-9_]*"' "$SDF" | sed 's/CELLTYPE //; s/"//g' | sort -u | wc -l