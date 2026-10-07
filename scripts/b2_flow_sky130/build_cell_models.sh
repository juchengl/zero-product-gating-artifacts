#!/bin/bash
# Flatten sky130_fd_sc_hd library .v files into one directory, then build a
# consolidated sim file there so `include directives resolve.
set -x
SRC=~/sky130_fd_sc_hd_lib
FLAT=~/b2_sky130/models_flat
rm -rf "$FLAT"; mkdir -p "$FLAT"
# all library .v files flat (unique names per cell); excludes nothing - the
# consolidated file's ifdefs pick functional vs behavioral at compile time
find "$SRC/models" "$SRC/cells" -name '*.v' -exec cp {} "$FLAT/" \; 2>/dev/null
ls "$FLAT" | wc -l
cd "$FLAT" || exit 1
find "$SRC/models" -name 'sky130_fd_sc_hd__udp_*.v' ! -name '*.tb.v' ! -name '*.blackbox.v' ! -name '*.symbol.v' | sort > /tmp/udp.txt
find "$SRC/cells" -maxdepth 2 -name 'sky130_fd_sc_hd__*.v' | grep -E 'sky130_fd_sc_hd__[a-z0-9_]+(_[0-9]+)?\.v$' | sort > /tmp/cells.txt
wc -l /tmp/udp.txt /tmp/cells.txt
{
  echo '// consolidated sky130_fd_sc_hd sim models (flat dir, includes resolve here)'
  cat /tmp/udp.txt /tmp/cells.txt | while read f; do cat "$f"; echo; done
} > "$FLAT/sky130_fd_sc_hd_sim.v"
ls -la "$FLAT/sky130_fd_sc_hd_sim.v"
