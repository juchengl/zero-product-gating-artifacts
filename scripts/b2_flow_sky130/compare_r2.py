"""R2 layout-robustness comparison: hold-vs-force gap across CORE_UTILIZATION 38/40/42.
Reads r2 power.txt (u38/u42) and the base-40 numbers from phase2_full_matrix.json.
"""
import re, json
from pathlib import Path

VARIANTS = ["B0", "B1", "B2", "B3", "B4"]
NTX, WINDOW = 1000, 20020.0
factor = WINDOW * 1e-9 / NTX * 1e12

def total_w(p):
    t = p.read_text()
    m = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
    return float(m.group(4)) if m else None

wl = "p90_random_s101_n1000"
out = {}
for U in ("u38", "u42"):
    out[U] = {}
    for v in VARIANTS:
        p = Path.home() / f"b2_sky130/r2/odo/{wl}_B{v[-1]}_{U}/power.txt"
        w = total_w(p) if p.exists() else None
        out[U][v] = round(w * factor, 3) if w else None
# base 40 from main matrix
zd = json.loads(Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/phase2_full_matrix.json").read_text(encoding="utf-8"))
out["u40"] = {v: zd["records"]["p90"][v]["mean"] for v in VARIANTS}

print("p90 pJ/tx across layouts:")
print("layout  " + "  ".join(f"{v:>7}" for v in VARIANTS) + "   B3-B2 gap(pp)  B3-B0(%)")
summary = {}
for U in ("u38", "u40", "u42"):
    vals = [out[U][v] for v in VARIANTS]
    if any(v is None for v in vals):
        print(U, "MISSING", vals)
        continue
    gap = (out[U]["B3"] - out[U]["B2"]) / out[U]["B0"] * 100
    d_b3 = (out[U]["B3"] - out[U]["B0"]) / out[U]["B0"] * 100
    print(f"{U}   " + "  ".join(f"{v:7.3f}" for v in vals) + f"   {gap:+.2f}          {d_b3:+.2f}")
    summary[U] = {"pj": out[U], "gap_B3_B2_pp": round(gap, 2), "B3_vs_B0_pct": round(d_b3, 2)}
Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/r2_layout_compare.json").write_text(
    json.dumps(summary, indent=2))
print("saved r2_layout_compare.json")