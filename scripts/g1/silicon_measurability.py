#!/usr/bin/env python3
"""Silicon measurability budget for narrative (a): can idle-subtraction recover
the HOLD mechanism's effect above instrument noise?

The mechanism only touches combinational power, which is 1.9-6.8% of array-level
total. Measuring total supply current directly puts the effect at ~1%, i.e. inside
typical measurement uncertainty. The design's existing DFT allows an idle-subtraction
measurement instead: pat_en=0 gives a clock+LFSR baseline, and mode_cfg selects
HOLD vs ADAPTIVE on the same die.

This computes, per grid point, the residual dynamic power after subtraction and the
required instrument accuracy, so the go/no-go decision can be made before paying
for a tapeout.
"""
import os
import re

W = os.path.expanduser("~/b3_ihp/g1")
# PREFIX=repower reads the 2026-09-22 rescaled reports (9 significant digits,
# activity-window divisor corrected, produced by scripts/g1_recompute_from_acts.sh);
# PREFIX=power reads the original 3-digit ones. Missing files fall back to power_*.
PREFIX = os.environ.get("PREFIX", "power")


def parse(tag):
    p = None
    for cand in ("%s_%s.txt" % (PREFIX, tag), "power_%s.txt" % tag):
        c = os.path.join(W, cand)
        if os.path.isfile(c):
            p = c
            break
    if p is None:
        return None
    d = {}
    for line in open(p):
        m = re.match(r"^(Sequential|Combinational|Clock|Total)\s+", line)
        if m:
            f = line.split()
            d[m.group(1)] = {"int": float(f[1]), "sw": float(f[2]),
                             "leak": float(f[3]), "tot": float(f[4])}
    return d


# VDD for the sky130hd corner used throughout G1
VDD = 1.80

POINTS = [("p30 T4", "b0", "b3", "auto"),
          ("p60 T4", "p60T4_b0", "p60T4_b3", "p60T4_auto"),
          ("p60 T16", "p60T16_b0", "p60T16_b3", "p60T16_auto"),
          ("p90 T4", "p90T4_b0", "p90T4_b3", "p90T4_auto"),
          ("p90 T16", "p90T16_b0", "p90T16_b3", "p90T16_auto")]

print("Idle-subtraction measurability budget (sky130 G1 data, VDD=%.2f V, reports=%s_*)"
      % (VDD, PREFIX))
print("=" * 96)
hdr = ("%-9s %10s %10s %10s %9s %9s %11s" %
       ("point", "I_tot b0", "I_tot b3", "dI(b0-b3)", "dI/I_b0", "I_dyn b3",
               "needed acc"))
print(hdr)
print("-" * 96)
rows = []
for label, t0, t3, ta in POINTS:
    b0, b3 = parse(t0), parse(t3)
    if not b0 or not b3:
        continue
    i0 = b0["Total"]["tot"] / VDD          # supply current, A
    i3 = b3["Total"]["tot"] / VDD
    dI = i0 - i3                            # the signal we must resolve
    # idle baseline ~= clock + seq internal (flop clock pins) + leakage; the
    # datapath comb switching is what survives subtraction
    i_idle = (b3["Clock"]["tot"] + b3["Sequential"]["int"]
              + b3["Total"]["leak"]) / VDD
    i_dyn = i3 - i_idle                     # residual dynamic after subtraction
    rel = dI / i0
    # accuracy needed on each of the two current readings for SNR=3 on dI
    need = dI / 3.0 / i0
    rows.append((label, i0, i3, dI, rel, i_dyn, need))
    print("%-9s %8.3f mA %8.3f mA %8.1f uA %8.3f%% %7.1f uA %9.3f%%"
          % (label, i0 * 1e3, i3 * 1e3, dI * 1e6, rel * 100,
             i_dyn * 1e6, need * 100))

print("-" * 96)
if rows:
    best = max(rows, key=lambda r: r[3])
    print("\nbest measurement point (largest absolute current delta): %s"
          "  dI = %.1f uA  (%.3f%% of total)" % (best[0], best[3] * 1e6,
                                                 best[4] * 100))
    print("required per-reading accuracy for SNR=3: %.3f%% of ~%.2f mA"
          % (best[6] * 100, best[1] * 1e3))
    print("\nreference: a typical bench SMU at 10 mA range / 100 ms NPLC gives")
    print("~0.05-0.2%% of reading; at %.2f mA that is %.1f-%.1f uA."
          % (best[1] * 1e3, best[1] * 1e6 * 0.0005, best[1] * 1e6 * 0.002))
    print("signal is %.1f uA -> SNR %.1f-%.1f with averaging."
          % (best[3] * 1e6, best[3] * 1e6 / (best[1] * 1e6 * 0.002),
             best[3] * 1e6 / (best[1] * 1e6 * 0.0005)))
