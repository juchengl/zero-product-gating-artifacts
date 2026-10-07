#!/usr/bin/env python3
"""G1 stimulus generator (chip-level stim format, no golden compare).

Usage: gen_g1_stim.py <mode_cfg> <force_en> <T> <pat_p> <run_cycles> <out>
Emits: rst pulse, cfg writes (thresh/mode_cfg+force_en/pat_p/pat_en=1),
run_cycles of pattern streaming, pat_en=0 stop.
"""
import sys

mode_cfg, force_en, T, pat_p, run_cycles, out = (
    int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),
    int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])

lines = []


def emit(rst, clear, we, addr, wdata, ro_addr=0, iv=0, ia=0, ib=0):
    ctl = (rst << 0) | (clear << 1) | (we << 2)
    lines.append("%x %x %x %x %x" % (ctl, addr, wdata, ro_addr,
                                     (iv << 16) | ((ia & 0xFF) << 8) | (ib & 0xFF)))


for _ in range(2):
    emit(1, 0, 0, 0, 0)
emit(0, 0, 0, 0, 0)
emit(0, 0, 1, 0, T)                                  # thresh
emit(0, 0, 1, 1, mode_cfg | (force_en << 2))         # mode_cfg + force_en
emit(0, 0, 1, 2, pat_p)                              # pat_p
emit(0, 0, 1, 3, 1)                                  # pat_en=1
for _ in range(run_cycles):
    emit(0, 0, 0, 0, 0)
emit(0, 0, 1, 3, 0)                                  # pat_en=0

with open(out, "w") as f:
    f.write("\n".join(lines) + "\n")
print("G1_STIM_OK %d cycles" % run_cycles)
