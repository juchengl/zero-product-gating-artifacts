import json, subprocess
n = subprocess.run(["bash", "-c", "ls ~/b2_sky130/odo/*_power.txt | wc -l"], capture_output=True, text=True).stdout.strip()
print("power files:", n)
d = json.load(open("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results_sky130/phase2_full_matrix.json"))
for lv, vs in d["records"].items():
    print(lv, {v: vs[v]["n"] for v in vs})
# also verify mean consistency: recompute deltas from records
import math
ok = True
for lv, vs in d["records"].items():
    b0 = vs["B0"]["mean"]
    for v in vs:
        if v == "B0":
            continue
        calc = round((vs[v]["mean"] - b0) / b0 * 100, 2)
        stored = d["delta_pct_vs_B0"][lv][v]
        if abs(calc - stored) > 0.01:
            print("DELTA MISMATCH", lv, v, calc, stored); ok = False
print("delta consistency:", "OK" if ok else "FAILED")