# -*- coding: utf-8 -*-
"""Compare propagated activity against injected (measured) activity, per pin.

Inputs: dump_prop.tsv, dump_inj.tsv produced by
  sta::report_activity_dump_cmd   (pin, net, density[s^-1], duty, origin)

Outputs: summary on stdout + activity_compare.tsv with per-pin ratio.
"""
import statistics as st
import sys
from pathlib import Path

D = Path(sys.argv[1] if len(sys.argv) > 1 else r"E:/科研/act")


def load(p):
    out = {}
    for line in Path(p).read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 5:
            continue
        out[f[0]] = (float(f[2]), float(f[3]), f[4], f[1])
    return out


prop = load(D / "dump_prop.tsv")
inj = load(D / "dump_inj.tsv")
common = [p for p in prop if p in inj]

rows, ratios = [], []
for p in common:
    dp, wt, op, net = prop[p]
    di, wi, oi, _ = inj[p]
    if op != "propagated" or oi != "user":
        continue
    if di <= 0:
        continue
    r = dp / di
    rows.append((p, net, dp, di, r, wt, wi))
    ratios.append(r)

rows.sort(key=lambda x: -x[4])
n = len(rows)
print("common pins: %d   compared (propagated vs user): %d" % (len(common), n))
if n:
    q = st.quantiles(ratios, n=100)
    print("ratio prop/inj : median %.3f  p10 %.3f  p90 %.3f  max %.2f  min %.3f"
          % (st.median(ratios), q[9], q[89], max(ratios), min(ratios)))
    over = sum(1 for r in ratios if r > 1.0)
    print("over-estimated pins: %d (%.1f%%)   under-estimated: %d"
          % (over, 100.0 * over / n, n - over))
    tot_p = sum(r[2] for r in rows)
    tot_i = sum(r[3] for r in rows)
    print("sum density (compared pins): prop %.4e  inj %.4e  ratio %.3f"
          % (tot_p, tot_i, tot_p / tot_i))
    print("\ntop 10 over-estimated:")
    for r in rows[:10]:
        print("  %-28s %-10s prop %.3e  inj %.3e  x%.1f" % (r[0], r[1], r[2], r[3], r[4]))
    print("\ntop 5 under-estimated:")
    for r in rows[-5:]:
        print("  %-28s %-10s prop %.3e  inj %.3e  x%.2f" % (r[0], r[1], r[2], r[3], r[4]))

out = D / "activity_compare.tsv"
out.write_text("pin\tnet\tprop_density\tinj_density\tratio\tprop_duty\tinj_duty\n"
               + "\n".join("%s\t%s\t%.6e\t%.6e\t%.4f\t%.4f\t%.4f" % r for r in rows),
               encoding="utf-8")
print("\nwrote", out)
