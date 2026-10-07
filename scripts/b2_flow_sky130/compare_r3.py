"""R3 corner sweep comparison: pJ/tx and deltas vs B0 across tt/ff/ss at p90."""
import re, json
from pathlib import Path
HOME = Path.home()
NTX, WINDOW = 1000, 20020.0
factor = WINDOW * 1e-9 / NTX * 1e12
CORNERS = ["tt_025C_1v80", "ff_100C_1v95", "ss_100C_1v60"]
VARIANTS = ["B0", "B1", "B2", "B3", "B4"]
out = {}
for C in CORNERS:
    out[C] = {}
    for n, v in enumerate(VARIANTS):
        p = HOME / f"b2_sky130/r1/../b2_sky130/odo/corner_{C}_B{n}/power.txt"
        p = HOME / f"b2_sky130/odo/corner_{C}_B{n}/power.txt"
        t = p.read_text()
        m = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
        out[C][v] = round(float(m.group(4)) * factor, 3) if m else None
rows = {}
for C in CORNERS:
    b0 = out[C]["B0"]
    rows[C] = {"pj": out[C], "delta": {v: round((out[C][v]-b0)/b0*100, 2) for v in VARIANTS if v != "B0"}}
print("p90 pJ/tx across corners:")
print("corner          " + "  ".join(f"{v:>7}" for v in VARIANTS))
for C in CORNERS:
    print(f"{C:14}  " + "  ".join(f"{out[C][v]:7.3f}" for v in VARIANTS))
print("\nDelta vs B0 (%):")
print("corner          " + "  ".join(f"{v:>7}" for v in VARIANTS[1:]))
for C in CORNERS:
    print(f"{C:14}  " + "  ".join(f"{rows[C]['delta'][v]:+7.2f}" for v in VARIANTS[1:]))
Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/r3_corner_compare.json").write_text(
    json.dumps(rows, indent=2))
print("\nsaved r3_corner_compare.json")