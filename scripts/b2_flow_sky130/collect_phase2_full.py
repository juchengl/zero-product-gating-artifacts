"""Aggregate the FULL 240-run matrix into the paper main table.

Groups the 45 n1000 workloads (5 probs x 3 arrangements x 3 seeds) by zero-prob
level, reporting mean +/- std of pJ/tx across the 9 combos per level. The 3
n2000 length-sensitivity workloads are reported separately.

Usage: python3 collect_phase2_full.py <odo_dir> <out_dir>
"""
import re, sys, json, statistics
from pathlib import Path

LEVELS = ["p00", "p10", "p30", "p60", "p90"]
VARIANTS = ["B0", "B1", "B2", "B3", "B4"]
NTX = 1000
WINDOW_NS = 20020.0


def parse(path: Path):
    t = path.read_text()
    m = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
    if not m:
        return None
    return {"internal_w": float(m.group(1)), "switching_w": float(m.group(2)),
            "leakage_w": float(m.group(3)), "total_w": float(m.group(4))}


def main():
    root = Path(sys.argv[1])
    out = Path(sys.argv[2])
    factor = WINDOW_NS * 1e-9 / NTX * 1e12
    # collect per workload
    per = {}
    for p in sorted(root.glob("*_power.txt")):
        name = p.stem.replace("_power", "")
        d = parse(p)
        if d is None:
            continue
        per[name] = {v: d[f"{v}_w"] * factor for v in
                     ("internal", "switching", "leakage", "total")}
    # group n1000 by prob level
    grouped = {lv: {v: [] for v in VARIANTS} for lv in LEVELS}
    for name, vals in per.items():
        if "_n2000" in name:
            continue
        lv = name[:3]
        v = name[-2:]
        if lv not in LEVELS or v not in VARIANTS:
            continue
        grouped[lv][v].append(vals["total"])
    # stats table
    rows = {}
    for lv in LEVELS:
        rows[lv] = {}
        for v in VARIANTS:
            xs = grouped[lv][v]
            if not xs:
                continue
            rows[lv][v] = {"mean": round(statistics.mean(xs), 3),
                           "std": round(statistics.pstdev(xs), 3) if len(xs) > 1 else 0.0,
                           "n": len(xs)}
    deltas = {}
    for lv in LEVELS:
        b0 = rows[lv].get("B0", {}).get("mean")
        if not b0:
            continue
        deltas[lv] = {v: round((rows[lv][v]["mean"] - b0) / b0 * 100, 2)
                      for v in VARIANTS if v in rows[lv] and v != "B0"}
    summary = {
        "evidence_level": "post-route ORFS sky130hd; in-session OpenRCX extraction; "
                          "per-driver-pin gate-VCD activity injection; zero-delay (no glitch)",
        "aggregation": "mean+/-pstdev over 9 combos (3 arrangements x 3 seeds) per level, n1000",
        "records": rows, "delta_pct_vs_B0": deltas,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase2_full_matrix.json").write_text(json.dumps(summary, indent=2))
    L = ["# 阶段-2 全集成对能耗表（48 负载聚合，pJ/有效事务，mean±pstdev, n=9）", "",
         f"证据层级：{summary['evidence_level']}",
         f"聚合：{summary['aggregation']}", "",
         "| 零概率 | B0 | B1 | B2 | B3 | B4 | B1Δ | B2Δ | B3Δ | B4Δ |",
         "|---|" + "---|" * 8]
    for lv in LEVELS:
        vals = [f"{rows[lv][v]['mean']}±{rows[lv][v]['std']}" for v in VARIANTS]
        ds = [f"{deltas[lv][v]:+.2f}%" for v in VARIANTS[1:]]
        L.append(f"| {lv[1:]}% | " + " | ".join(vals) + " | " + " | ".join(ds) + " |")
    L += ["", "Δ = 相对 B0 的总能耗百分比（mean）。", "",
          "长度敏感性（n2000, p30 random）：", "", "| 变体 | pJ/tx |", "|---|---|"]
    for v in VARIANTS:
        for name in sorted(per):
            if name == f"p30_random_s101_n2000_{v}":
                L.append(f"| {v} | {round(per[name]['total'], 3)} |")
    (out / "phase2_full_matrix.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()