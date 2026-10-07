"""Cross-check manuscript numbers against data files.
1) glitch table (manuscript tab:glitch) vs r1_glitch_compare.json
2) area numbers (manuscript 4.3) vs c3_mapping_summary.json
3) main table (tab:main) vs phase2_full_matrix.json
"""
import json, re
from pathlib import Path

BASE = Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup")
tex = (BASE / "paper/manuscript.tex").read_text(encoding="utf-8")
issues = []

# 1) main table vs json
zd = json.loads((BASE / "results_sky130/phase2_full_matrix.json").read_text(encoding="utf-8"))
for lv in ["p00", "p10", "p30", "p60", "p90"]:
    for v in ["B0", "B1", "B2", "B3", "B4"]:
        mean = zd["records"][lv][v]["mean"]
        # find e.g. '4.244$\\pm$.016' row entries: check the mean string present
        s = f"{mean:.3f}".rstrip("0").rstrip(".") if isinstance(mean, float) else str(mean)
        if s not in tex:
            issues.append(f"main {lv} {v} mean {mean} not found in tex as {s}")
        d = zd["delta_pct_vs_B0"][lv].get(v)
        if d is None:
            continue
        ds = f"{d:+.2f}"
        if ds.replace("+", "$+") .replace("%", "") not in tex and ds not in tex:
            # loose check
            if f"{d:.2f}" not in tex:
                issues.append(f"main {lv} {v} delta {d} not found in tex")

# 2) glitch table vs r1 json
r1 = json.loads((BASE / "results_sky130/r1_glitch_compare.json").read_text(encoding="utf-8"))
b0 = {lv: r1["r1_glitch_pj_tx"][lv]["B0"] for lv in r1["r1_glitch_pj_tx"]}
for lv in ["p00", "p30", "p60", "p90"]:
    for v in ["B1", "B2", "B3", "B4"]:
        val = r1["r1_glitch_pj_tx"][lv][v]
        d = (val - b0[lv]) / b0[lv] * 100
        if f"{d:.2f}" not in tex:
            issues.append(f"glitch {lv} {v} delta {d:.2f} not found in tex")

# 3) area vs c3
c3 = json.loads((BASE / "results_sky130/c3_mapping_summary.json").read_text(encoding="utf-8"))
for top, r in c3["variants"].items():
    v = top.replace("mac_", "")
    a = r["area_um2"]
    if f"{a}" not in tex:
        issues.append(f"area {v} {a} not found in tex")
    dd = r["area_delta_vs_B0_pct"]
    if f"{dd:.2f}" not in tex and f"{dd}" not in tex:
        issues.append(f"area delta {v} {dd} not found in tex")

print("ISSUES:" if issues else "ALL MANUSCRIPT NUMBERS MATCH DATA FILES")
for i in issues:
    print(" -", i)