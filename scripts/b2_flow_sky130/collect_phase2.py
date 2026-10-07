"""Collect the 25 in-session power results into the phase-2 paired energy table.

Validity: post-route extraction in-session (parasitics applied) + per-driver-pin
activity injected from gate-level VCD (zero-delay, no glitch timing - 2b pending).

Usage: python3 collect_phase2.py <odo_dir> <out_dir>
"""
import re, sys, json
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
    factor = WINDOW_NS * 1e-9 / NTX * 1e12  # W -> pJ per tx
    rows = {}
    for wl in LEVELS:
        for v in VARIANTS:
            p = root / f"{wl}_random_s101_n1000_{v}_power.txt"
            d = parse(p)
            if d is None:
                print("MISSING", p)
                continue
            rows.setdefault(wl, {})[v] = {
                "pJ_tx_total": round(d["total_w"] * factor, 3),
                "pJ_tx_dynamic": round((d["internal_w"] + d["switching_w"]) * factor, 3),
                "power_total_uW": round(d["total_w"] * 1e6, 3),
                "power_switching_uW": round(d["switching_w"] * 1e6, 3),
            }
    deltas = {}
    for wl, vs in rows.items():
        b0 = vs["B0"]["pJ_tx_total"]
        deltas[wl] = {v: round((vs[v]["pJ_tx_total"] - b0) / b0 * 100, 2) for v in vs if v != "B0"}
    summary = {
        "evidence_level": "post-route ORFS sky130hd; in-session OpenRCX extraction "
                          "(parasitics applied); activity injected per driver pin from "
                          "zero-delay gate-level VCD (~820 pins/run); NOT SDF glitch-true",
        "window_ns": WINDOW_NS, "transactions": NTX, "vdd": 1.8,
        "records": rows, "delta_pct_vs_B0": deltas,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase2_power_matrix.json").write_text(json.dumps(summary, indent=2))
    L = ["# 阶段-2 成对能耗表（修复后口径，pJ/有效事务）", "",
         f"证据层级：{summary['evidence_level']}", "",
         "工作负载 `<零概率>_random_s101_n1000`，窗口 20.02 µs / 1000 事务，1.8 V，sky130hd tt 25°C。",
         "", "| 零概率 | B0 | B1 | B2 | B3 | B4 | B1Δ | B2Δ | B3Δ | B4Δ |",
         "|---|" + "---|" * 8]
    for wl in LEVELS:
        vs = rows[wl]
        vals = [f"{vs[v]['pJ_tx_total']}" for v in VARIANTS]
        ds = [f"{deltas[wl][v]:+.2f}%" for v in VARIANTS[1:]]
        L.append(f"| {wl[1:]}% | " + " | ".join(vals) + " | " + " | ".join(ds) + " |")
    L += ["", "Δ = 相对 B0 的总能耗百分比。", "",
          "附：切换功耗（µW）", "",
          "| 零概率 | B0 | B1 | B2 | B3 | B4 |", "|---|" + "---|" * 5]
    for wl in LEVELS:
        vs = rows[wl]
        L.append(f"| {wl[1:]}% | " + " | ".join(f"{vs[v]['power_switching_uW']}" for v in VARIANTS) + " |")
    (out / "phase2_power_matrix.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()