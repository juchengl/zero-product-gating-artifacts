"""Collect D3 phase-1 power runs into a paired preliminary energy table.

Parses OpenSTA report_power output (W) for runs named <workload>_B<n>, converts
to pJ per effective transaction using the B2 measurement window formula, and
emits JSON + markdown. Zero-probability levels are read from workload names.

Evidence level of these numbers: post-route power with RTL-replay VCD activity
propagated by OpenSTA (no glitch-level gate simulation, no SDF annotation).
Preliminary - not the accepted endpoint (that requires gate-level replay).

Usage: python3 collect_energy_phase1.py <power_smoke_dir> <out_dir> <n_transactions>
"""
import json, re, sys
from pathlib import Path

LEVELS = ["p00", "p10", "p30", "p60", "p90"]
VARIANTS = ["B0", "B1", "B2", "B3", "B4"]

def parse_power(path: Path):
    text = path.read_text()
    total = re.search(
        r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", text, re.M)
    if not total:
        return None
    groups = {}
    for name in ("Sequential", "Combinational", "Clock"):
        m = re.search(rf"^{name}\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)",
                      text, re.M)
        if m:
            groups[name.lower()] = {"internal_w": float(m.group(1)),
                                    "switching_w": float(m.group(2)),
                                    "leakage_w": float(m.group(3))}
    return {"internal_w": float(total.group(1)),
            "switching_w": float(total.group(2)),
            "leakage_w": float(total.group(3)),
            "groups": groups}

def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    n_tx = int(sys.argv[3])
    period_ns = 20.0
    window_ns = (n_tx + 1) * period_ns  # cycles 3 .. n+4 exclusive
    factor = window_ns * 1e-9 / n_tx * 1e12  # W -> pJ/tx
    rows = {}
    for wl in LEVELS:
        for v in VARIANTS:
            p = root / f"{wl}_random_s101_n1000_{v}" / "power.txt"
            if not p.exists():
                continue
            d = parse_power(p)
            if d is None:
                continue
            dyn = d["internal_w"] + d["switching_w"]
            tot = dyn + d["leakage_w"]
            rows.setdefault(wl, {})[v] = {
                "pJ_per_tx_total": round(tot * factor, 3),
                "pJ_per_tx_dynamic": round(dyn * factor, 3),
                "pJ_per_tx_leakage": round(d["leakage_w"] * factor, 3),
                "power_w": {"internal": d["internal_w"], "switching": d["switching_w"],
                            "leakage": d["leakage_w"]},
                "groups_pj_per_tx": {k: round((g["internal_w"] + g["switching_w"]
                                               + g["leakage_w"]) * factor, 3)
                                     for k, g in d["groups"].items()},
            }
    # deltas vs B0 per level
    deltas = {}
    for wl, variants in rows.items():
        b0 = variants.get("B0", {}).get("pJ_per_tx_total")
        if b0:
            deltas[wl] = {v: round((variants[v]["pJ_per_tx_total"] - b0) / b0 * 100, 2)
                          for v in variants if v != "B0"}
    summary = {"stage": "phase1_activity_propagated_post_route",
               "evidence_level": "preliminary; NOT SDF gate-level simulation; "
                                 "RTL-VCD activity annotated via OpenSTA read_vcd, "
                                 "53 pins annotated per run, internal activity propagated",
               "window_ns": window_ns, "transactions": n_tx, "period_ns": period_ns,
               "energy_pj_per_tx": rows, "delta_pct_vs_B0": deltas}
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase1_energy_smoke.json").write_text(json.dumps(summary, indent=2))
    lines = ["# D3 阶段-1 初步成对能耗（pJ/有效事务，零概率扫描）", "",
             f"证据层级：{summary['evidence_level']}", "",
             "工作负载：`<零概率>_random_s101_n1000`，N=1000 有效事务，窗口 20.02 µs。",
             "", "| 零概率 | " + " | ".join(VARIANTS) + " | B1Δ | B2Δ | B3Δ | B4Δ |",
             "|---|" + "---|" * 8]
    for wl in LEVELS:
        if wl not in rows:
            continue
        vals = [rows[wl][v]["pJ_per_tx_total"] for v in VARIANTS]
        d = deltas.get(wl, {})
        lines.append(f"| {wl[1:]}% | " + " | ".join(f"{x}" for x in vals) +
                     " | " + " | ".join(f"{d.get(v, 0):+.2f}%" for v in VARIANTS[1:]) + " |")
    lines += ["", "Δ = 相对 B0 的总能耗百分比变化（负值=更省能）。", "",
              "分组能耗（阶段-1 首个负载示例，pJ/tx）：",
              "```json", json.dumps(rows.get(LEVELS[0], {}).get("B0", {}).get("groups_pj_per_tx", {}), indent=1), "```"]
    (out / "phase1_energy_smoke.md").write_text("\n".join(lines))
    print("\n".join(lines[:14]))

if __name__ == "__main__":
    main()
