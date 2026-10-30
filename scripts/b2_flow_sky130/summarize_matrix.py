# -*- coding: utf-8 -*-
"""Summarise the 5x4 matrix: propagated vs injected activity, per design point."""
import statistics as st
from pathlib import Path

BASE = Path.home() / "act" / "matrix" / "run"
PCTS = ["00", "30", "60", "90"]
MODES = [0, 1, 2, 3, 4]


def total_power(p):
    f = p / "power_prop.txt"
    if not f.exists():
        return None
    for line in f.read_text(errors="replace").splitlines():
        if line.startswith("Total"):
            return float(line.split()[4])
    return None


def arm_power(p, arm):
    f = p / ("power_%s.txt" % arm)
    if not f.exists():
        return None
    for line in f.read_text(errors="replace").splitlines():
        if line.startswith("Total"):
            return float(line.split()[4])
    return None


def load(p):
    out = {}
    f = p / "dump_prop.tsv"
    if not f.exists():
        return out
    for line in f.read_text(errors="replace").splitlines()[1:]:
        c = line.split("\t")
        if len(c) >= 5:
            out[c[0]] = (float(c[2]), c[4])
    return out


def load_inj(p):
    out = {}
    f = p / "dump_inj.tsv"
    if not f.exists():
        return out
    for line in f.read_text(errors="replace").splitlines()[1:]:
        c = line.split("\t")
        if len(c) >= 5:
            out[c[0]] = (float(c[2]), c[4])
    return out


rows = []
for pct in PCTS:
    for m in MODES:
        tag = "p%s_B%d" % (pct, m)
        d = BASE / tag
        if not d.exists():
            continue
        pp, pi = arm_power(d, "prop"), arm_power(d, "inj")
        dp, di = load(d), load_inj(d)
        ratios = []
        for k, (v, o) in dp.items():
            if k in di and o == "propagated" and di[k][1] == "user" and di[k][0] > 0:
                ratios.append(v / di[k][0])
        med = st.median(ratios) if ratios else float("nan")
        over = 100.0 * sum(1 for r in ratios if r > 1.0) / len(ratios) if ratios else float("nan")
        rows.append(dict(pct=pct, mode=m, prop=pp, inj=pi, n=len(ratios),
                         med=med, over=over,
                         tot_ratio=(pp / pi) if (pp and pi) else float("nan")))

print("%-5s %-3s %11s %11s %8s %8s %7s %5s" %
      ("zero", "B", "prop(W)", "inj(W)", "tot_rat", "med_pin", "over%", "n"))
for r in rows:
    print("%-5s B%-2d %11.4e %11.4e %8.3f %8.3f %7.1f %5d" %
          (r["pct"], r["mode"], r["prop"], r["inj"], r["tot_ratio"], r["med"], r["over"], r["n"]))

print("\n=== delta vs B0 (%%), propagated arm ===")
for pct in PCTS:
    base = next((r["prop"] for r in rows if r["pct"] == pct and r["mode"] == 0), None)
    if not base:
        continue
    line = "p%s  " % pct
    for r in [x for x in rows if x["pct"] == pct]:
        line += "B%d %+6.2f%%  " % (r["mode"], 100.0 * (r["prop"] / base - 1))
    print(line)

print("\n=== delta vs B0 (%%), injected arm ===")
for pct in PCTS:
    base = next((r["inj"] for r in rows if r["pct"] == pct and r["mode"] == 0), None)
    if not base:
        continue
    line = "p%s  " % pct
    for r in [x for x in rows if x["pct"] == pct]:
        line += "B%d %+6.2f%%  " % (r["mode"], 100.0 * (r["inj"] / base - 1))
    print(line)

out = Path.home() / "act" / "matrix_summary.csv"
out.write_text("zero,variant,prop_w,inj_w,total_ratio,median_pin_ratio,pct_over,n\n" +
               "\n".join("%s,B%d,%.6e,%.6e,%.4f,%.4f,%.2f,%d" %
                         (r["pct"], r["mode"], r["prop"], r["inj"], r["tot_ratio"], r["med"], r["over"], r["n"])
                         for r in rows), encoding="utf-8")
print("\nwrote", out)
