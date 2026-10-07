import re, statistics, json
from pathlib import Path
HOME = Path.home()
BASE = Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup")

def total_w(p):
    m = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", p.read_text(), re.M)
    return float(m.group(4)) if m else None

vals = {"B0": [], "B1": [], "B4": []}
import glob
for v in vals:
    for p in sorted(HOME.glob(f"b2_sky130/odo/p00_*_B{v[-1]}_digits6/power.txt")):
        w = total_w(p)
        if w: vals[v].append(w * 20020.0)
means = {v: statistics.mean(x) for v, x in vals.items()}
det = (means["B4"] - means["B1"]) / means["B0"] * 100
b1 = (means["B1"] - means["B0"]) / means["B0"] * 100
b4 = (means["B4"] - means["B0"]) / means["B0"] * 100
out = {"p00_digits6_means_pj": {v: round(means[v], 4) for v in means},
       "n": {v: len(vals[v]) for v in vals},
       "detection_cost_pct": round(det, 3),
       "B1_vs_B0_pct": round(b1, 2), "B4_vs_B0_pct": round(b4, 2)}
print(json.dumps(out, indent=1))
Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/r4_p00_digits6.json").write_text(json.dumps(out, indent=2))