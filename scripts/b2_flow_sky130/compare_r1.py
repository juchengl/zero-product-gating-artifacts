"""Compare R1 glitch-true (SDF) energy vs the zero-delay main table.
Reads ~/b2_sky130/r1/odo/<wl>_B<n>/power.txt, prints pJ/tx + delta vs B0,
and contrasts the B1/B2/B3 ordering against the zero-delay phase2_full_matrix.
"""
import re, json
from pathlib import Path

LEVELS = ["p00", "p30", "p60", "p90"]
VARIANTS = ["B0", "B1", "B2", "B3", "B4"]
NTX, WINDOW = 1000, 20020.0
factor = WINDOW * 1e-9 / NTX * 1e12

def total_w(path):
    t = path.read_text()
    m = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
    return float(m.group(4)) if m else None

r1 = {}
for wl in ["p00", "p30", "p60", "p90"]:
    name = f"{wl}_random_s101_n1000"
    for v in VARIANTS:
        p = Path.home() / f"b2_sky130/r1/odo/{name}_{v}/power.txt"
        w = total_w(p) if p.exists() else None
        r1.setdefault(wl, {})[v] = round(w * factor, 3) if w else None

zd = json.loads(Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/phase2_full_matrix.json").read_text(encoding="utf-8"))
zdelta = zd["delta_pct_vs_B0"]

print("=== R1 glitch-true (SDF) pJ/tx ===")
print("level  " + "  ".join(f"{v:>7}" for v in VARIANTS))
for wl in LEVELS:
    print(f"{wl}   " + "  ".join(f"{r1[wl][v] if r1[wl][v] is not None else 'NA':>7}" for v in VARIANTS))
print("\n=== delta vs B0: glitch-true (R1) vs zero-delay (main) ===")
print("level  B1:R1/main  B2:R1/main  B3:R1/main  B4:R1/main")
for wl in LEVELS:
    b0 = r1[wl]["B0"]
    row = []
    for v in VARIANTS[1:]:
        r1d = (r1[wl][v] - b0) / b0 * 100 if b0 and r1[wl][v] is not None else None
        zdd = zdelta[wl][v]
        row.append(f"{r1d:+.2f}/{zdd:+.2f}" if r1d is not None else "NA")
    print(f"{wl}  " + "  ".join(row))
Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/r1_glitch_compare.json").write_text(
    json.dumps({"r1_glitch_pj_tx": r1, "note": "SDF-annotated glitch-true, 4 levels, seed101 random; FF instances unannotated due to netlist-name strip (combinational delays applied -> glitch model valid)"}, indent=2))