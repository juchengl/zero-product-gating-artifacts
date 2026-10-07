"""Collect five-variant sky130hd mapping results (area, cells, timing) into
one summary JSON + a human-readable markdown table.

Usage: python3 collect_summary.py <work_dir> <out_dir>
"""
import json, re, sys
from pathlib import Path

VARIANTS = {
    "mac_b0": "B0 baseline (sample every cycle)",
    "mac_b1": "B1 valid isolation",
    "mac_b2": "B2 force-to-zero",
    "mac_b3": "B3 input hold",
    "mac_b4": "B4 mask-only control (B1 sampling + zero mask)",
}

def parse_stat(path: Path):
    d = json.loads(path.read_text())
    mod = next(iter(d["modules"].values()))
    area = mod.get("area")
    cells = mod.get("num_cells", sum(mod.get("num_cells_by_type", {}).values()))
    by_type = mod.get("num_cells_by_type", {})
    ffs = sum(v for k, v in by_type.items() if re.search(r"df|dl", k.lower()))
    return {"area_um2": round(area, 2) if area else None, "cells": cells,
            "cells_by_type": by_type, "ff_cells": ffs}

def parse_sta(path: Path):
    text = path.read_text()
    slacks = [float(x) for x in re.findall(r"worst slack\s+([-\d.]+)", text)]
    setup = slacks[0] if len(slacks) > 0 else None
    hold = slacks[1] if len(slacks) > 1 else None
    m_tns = re.search(r"tns\s+([-\d.]+)", text)
    return {"setup_slack_ns": setup, "hold_slack_ns": hold,
            "tns_ns": float(m_tns.group(1)) if m_tns else None,
            "timing_met": (setup is not None and setup >= 0
                           and hold is not None and hold >= 0)}

def main():
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = {}
    for top, desc in VARIANTS.items():
        rows[top] = {"description": desc,
                     **parse_stat(work / f"{top}_stat.json"),
                     **parse_sta(work / f"{top}_sta.log")}
    b0 = rows["mac_b0"]["area_um2"]
    for top, r in rows.items():
        r["area_delta_vs_B0_pct"] = (round((r["area_um2"] - b0) / b0 * 100, 2)
                                     if (r["area_um2"] and b0) else None)
    summary = {"stage": "library_mapping_only_not_pnr",
               "constraint": "20ns common clock, ideal inputs, zero I/O delay",
               "note": "Post-synthesis mapping estimate; NOT post-route PPA. "
                       "Cell area from sky130_fd_sc_hd tt_025C_1v80 liberty.",
               "variants": rows}
    (out / "c3_mapping_summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["# C3/D1 五版 sky130hd 库映射结果（综合后，非布局布线）", "",
             "| 变体 | 面积 µm² | Δvs.B0 | 单元数 | 触发器单元 | setup slack (ns) | hold slack (ns) | 时序达标 |",
             "|---|---|---|---|---|---|---|---|"]
    for top, r in rows.items():
        lines.append(f"| {top.replace('mac_','').upper()} | {r['area_um2']} | "
                     f"{r['area_delta_vs_B0_pct']}% | {r['cells']} | {r['ff_cells']} | "
                     f"{r['setup_slack_ns']} | {r['hold_slack_ns']} | "
                     f"{'是' if r['timing_met'] else '否'} |")
    lines += ["", "共同约束：20 ns 时钟、理想输入、零输出延迟；仅库映射，未做布局布线。",
              "", "```json", json.dumps(summary, indent=2), "```"]
    (out / "c3_mapping_summary.md").write_text("\n".join(lines))
    print(json.dumps(summary, indent=2)[:2000])

if __name__ == "__main__":
    main()
