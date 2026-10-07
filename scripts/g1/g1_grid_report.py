#!/usr/bin/env python3
"""Aggregate the G1 grid power reports into the comparison table for S3.2.

Reads ~/b3_ihp/g1/power_<tag>.txt where tag is one of the legacy p30 names
(b0/b3/b2/auto) or the grid names (p60T4_b0 ...). Prints per-grid-point
totals, the combinational component (the only group the mechanism touches),
and the auto-vs-best-static margin that the G1 criterion is defined on.
"""
import os
import re
import sys

W = os.path.expanduser("~/b3_ihp/g1")
GROUPS = ("Sequential", "Combinational", "Clock")


def parse(path):
    if not os.path.isfile(path):
        return None
    out = {}
    for line in open(path):
        m = re.match(r"^(%s|Total)\s+" % "|".join(GROUPS), line)
        if m:
            f = line.split()
            # Internal Switching Leakage Total pct
            out[m.group(1)] = {"int": float(f[1]), "sw": float(f[2]),
                               "tot": float(f[4])}
    return out or None


def pct(a, b):
    return (a / b - 1.0) * 100.0 if b else float("nan")


POINTS = [
    ("p30 T4  (31.02%)", [("B0", "b0"), ("B3", "b3"), ("B2", "b2"),
                          ("ADAPTIVE", "auto")]),
    ("p60 T4  (62.40%)", [("B0", "p60T4_b0"), ("B3", "p60T4_b3"),
                          ("ADAPTIVE", "p60T4_auto")]),
    ("p60 T16 (62.40%)", [("B0", "p60T16_b0"), ("B3", "p60T16_b3"),
                          ("ADAPTIVE", "p60T16_auto")]),
    ("p90 T4  (87.47%)", [("B0", "p90T4_b0"), ("B3", "p90T4_b3"),
                          ("ADAPTIVE", "p90T4_auto")]),
    ("p90 T16 (87.47%)", [("B0", "p90T16_b0"), ("B3", "p90T16_b3"),
                          ("ADAPTIVE", "p90T16_auto")]),
]

print("=" * 78)
print("G1 grid -- power by group (W). comb = the only group the mechanism touches")
print("=" * 78)
for label, variants in POINTS:
    data = {n: parse(os.path.join(W, "power_%s.txt" % t)) for n, t in variants}
    data = {n: v for n, v in data.items() if v}
    if not data:
        print("\n%s -- MISSING" % label)
        continue
    print("\n--- %s ---" % label)
    print("  %-9s %10s %10s %10s %10s" % ("variant", "total", "comb", "seq", "clock"))
    for n in data:
        d = data[n]
        print("  %-9s %10.4e %10.4e %10.4e %10.4e"
              % (n, d["Total"]["tot"], d["Combinational"]["tot"],
                 d["Sequential"]["tot"], d["Clock"]["tot"]))
    if "B0" in data:
        b0 = data["B0"]["Total"]["tot"]
        c0 = data["B0"]["Combinational"]["tot"]
        statics = {k: v for k, v in data.items() if k.startswith("B")}
        best = min(statics, key=lambda k: statics[k]["Total"]["tot"])
        print("  best static = %s (%.4e W)" % (best, statics[best]["Total"]["tot"]))
        for k in ("B2", "B3", "ADAPTIVE"):
            if k in data and k != "B0":
                dt = pct(data[k]["Total"]["tot"], b0)
                dc = pct(data[k]["Combinational"]["tot"], c0)
                verdict = ""
                if k == "ADAPTIVE":
                    gap = pct(data[k]["Total"]["tot"],
                              statics[best]["Total"]["tot"])
                    verdict = ("  | auto vs best static: %+.3f%% -> %s"
                               % (gap, "PASS (<=0)" if gap <= 1e-9 else "FAIL"))
                print("    %-9s vs B0: total %+.3f%%  comb %+.3f%%%s"
                      % (k, dt, dc, verdict))

print("\n" + "=" * 78)
print("criterion: ADAPTIVE total must be <= best static total at EVERY grid point")
print("=" * 78)
fails = []
for label, variants in POINTS:
    data = {n: parse(os.path.join(W, "power_%s.txt" % t)) for n, t in variants}
    data = {n: v for n, v in data.items() if v}
    if "ADAPTIVE" not in data:
        continue
    statics = {k: v["Total"]["tot"] for k, v in data.items() if k.startswith("B")}
    best = min(statics.values())
    a = data["ADAPTIVE"]["Total"]["tot"]
    ok = a <= best * (1 + 1e-6)
    print("  %-20s auto=%.5e best_static=%.5e  %s"
          % (label, a, best, "PASS" if ok else "FAIL"))
    if not ok:
        fails.append(label)
print("\nFAILING POINTS: %s" % (", ".join(fails) if fails else "none"))
sys.exit(0)
