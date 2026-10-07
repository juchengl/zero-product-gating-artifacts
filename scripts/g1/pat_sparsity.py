#!/usr/bin/env python3
"""Achieved zero-word fraction for the chip_top on-chip pattern generator.

Mirrors pat_gen in rtl/chip_top.sv: 8-bit maximal LFSR,
fb = lfsr[7]^lfsr[5]^lfsr[4]^lfsr[3], sample = {lfsr[7],lfsr[5],lfsr[3],lfsr[1]},
make_zero = sample < pat_p, per-PE SEED = (13*i+11) % 256.

Usage: pat_sparsity.py <pat_p> [n_pe] [window_cycles]
Reports the array-averaged zero fraction over the G1 dump window and over ten
full LFSR periods, so the paper can state measured rather than nominal sparsity.
"""
import sys


def bit(v, n):
    return (v >> n) & 1


def stream(seed, cycles, pat_p):
    lfsr = seed
    zeros = 0
    for _ in range(cycles):
        fb = bit(lfsr, 7) ^ bit(lfsr, 5) ^ bit(lfsr, 4) ^ bit(lfsr, 3)
        sample = bit(lfsr, 7) * 8 + bit(lfsr, 5) * 4 + bit(lfsr, 3) * 2 + bit(lfsr, 1)
        if sample < pat_p:
            zeros += 1
        lfsr = ((lfsr << 1) | fb) & 0xFF
    return zeros


pat_p = int(sys.argv[1])
n_pe = int(sys.argv[2]) if len(sys.argv) > 2 else 64
window = int(sys.argv[3]) if len(sys.argv) > 3 else 500

for label, cyc in (("window %d cyc" % window, window), ("10 LFSR periods", 2550)):
    tot = sum(stream((13 * i + 11) % 256, cyc, pat_p) for i in range(n_pe))
    frac = tot / (n_pe * cyc)
    print("pat_p=%-3d %-18s zero-word fraction = %.4f  (%.2f%%)  nominal %.4f"
          % (pat_p, label, frac, frac * 100, pat_p / 16.0))
