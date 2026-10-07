#!/bin/bash
set -x
mkdir -p ~/b2_sky130/pdk_hd
cd ~/b2_sky130/pdk_hd || exit 1
tar --zstd -xf /mnt/c/Users/Administrator/dl_lib/sky130_fd_sc_hd.tar.zst 2>&1 | tail -2
find . -name "*.lib" -path "*lib*" | head -20
echo "=== corner list ==="
find . -name "sky130_fd_sc_hd__tt*.lib" -o -name "sky130_fd_sc_hd__ff*.lib" -o -name "sky130_fd_sc_hd__ss*.lib" | sed 's/.*\///' | sort -u | head -20