#!/bin/bash
set -x
cd ~ || exit 1
rm -rf sky130_fd_sc_hd_lib
for i in 1 2 3 4 5 6; do
  git -c http.version=HTTP/1.1 -c http.lowSpeedLimit=2000 -c http.lowSpeedTime=40 clone --depth 1 https://github.com/google/skywater-pdk-libs-sky130_fd_sc_hd.git sky130_fd_sc_hd_lib && { echo CLONE-OK; break; }
  echo "retry $i"; sleep 8; rm -rf sky130_fd_sc_hd_lib
done
test -d sky130_fd_sc_hd_lib/cells && echo LIB-OK || exit 1
find sky130_fd_sc_hd_lib -name '*.v' | wc -l
du -sh sky130_fd_sc_hd_lib
