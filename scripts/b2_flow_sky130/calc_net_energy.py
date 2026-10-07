"""First-principles switching-energy metric, independent of OpenSTA activity
propagation.

For each run <workload>_B<n>:
  - parse SPEF: per-net capacitance (*D_NET name *CAP value)
  - parse gate window VCD: per-net transition count in the window
  E_sw_net = 0.5 * C_net * Vdd^2 * transitions
  total E_sw in window -> pJ per effective transaction.

Net name normalization: strip backslashes, strip '$_...' instance suffixes that
ORFS fuses into net names, match SPEF names (escaped, with suffix) to VCD names.

Usage: python calc_net_energy.py  (paths at top)
"""
import re, sys, json
from pathlib import Path

VDD = 1.8
NTX = 1000
BASE = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup")
VCD_DIR = BASE / "results/replay_gate_gate_smoke"
OUT = BASE / "results_sky130"
LEVELS = ["p00", "p10", "p30", "p60", "p90"]
VARIANTS = ["B0", "B1", "B2", "B3", "B4"]


def parse_spef(path: Path):
    caps = {}
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        t = line.strip()
        if t.startswith("*D_NET"):
            name = t.split()[1]
            j = idx + 1
            cap = 0.0
            while j < len(lines) and not lines[j].strip().startswith("*END"):
                c = lines[j].strip()
                # *CAP 0.0001234 or *CAP:0.0001 12345; skip per-pin *CAP( entries
                m = re.match(r"\*CAP\s+([\d.eE+-]+)", c)
                if m:
                    cap += float(m.group(1))
                j += 1
            caps[name] = cap
    return caps


def norm_vcd_name(name: str) -> str:
    name = name.lstrip("\\")
    return name


def count_transitions(path: Path):
    toggles = {}
    last = {}
    for line in path.read_text(errors="replace").splitlines():
        t = line.strip()
        if t.startswith("$") or t.startswith("#"):
            continue
        if t.startswith(("b", "B")):
            bits, vid = t[1:].split()
        elif len(t) >= 2 and t[0] in "01xXzZ":
            bits, vid = t[0], t[1:]
        else:
            continue
        prev = last.get(vid)
        if prev is not None and prev != bits:
            toggles[vid] = toggles.get(vid, 0) + 1
        last[vid] = bits
    return toggles


def main():
    records = {}
    name2id = {}
    id2name = {}
    # map VCD id -> net name from header
    for wl in LEVELS:
        for v in VARIANTS:
            vcd = VCD_DIR / f"{wl}_random_s101_n1000_{v}.window.vcd"
            spef = Path(r"\\wsl.localhost\Ubuntu-22.04\home\research\orfs-git\flow\results\sky130hd\mac_b" + v[1] + r"\base\6_final.spef")
            caps = parse_spef(spef)
            header = {}
            for line in vcd.read_text(errors="replace").splitlines():
                t = line.strip()
                if t.startswith("$var"):
                    parts = t.split()
                    header[parts[3]] = norm_vcd_name(parts[4])
                if t.startswith("$enddefinitions"):
                    break
            toggles = count_transitions(vcd)
            e_total = 0.0
            matched_nets = 0
            unmarked = 0
            for vid, count in toggles.items():
                net = header.get(vid, "")
                if not net:
                    unmarked += count
                    continue
                # strip instance suffix fused by ORFS (e.g. acc[3]$_SDFFE_PP0P_ -> acc[3])
                net_clean = re.sub(r"\$_[A-Za-z0-9_]+_$", "", net)
                cap = caps.get(net) or caps.get(net_clean) or caps.get("\\" + net) or caps.get(net.replace("\\", ""))
                if cap is None:
                    unmarked += count
                    continue
                matched_nets += 1
                e_total += 0.5 * cap * VDD * VDD * count
            # cap units: SPEF *CAP in F (farads)? Sky130 SPEF from OpenROAD: C in F.
            e_pj = e_total * 1e12 / NTX
            covered = (matched_nets / max(1, len(toggles) - 1)) * 100 if len(toggles) > 1 else 0
            records.setdefault(wl, {})[v] = {
                "switching_energy_pJ_tx": round(e_pj, 3),
                "matched_nets": matched_nets,
                "total_nets_in_vcd": len(toggles),
                "unmatched_transitions": unmarked,
            }
    for wl, vs in records.items():
        b0 = vs["B0"]["switching_energy_pJ_tx"]
        for v, d in vs.items():
            d["delta_pct_vs_B0"] = round((d["switching_energy_pJ_tx"] - b0) / b0 * 100, 2)
    summary = {
        "metric": "0.5*C_net*Vdd^2*transitions per net, from post-route SPEF caps and "
                  "zero-delay gate-sim VCD transitions, per 1000 effective transactions",
        "vdd": VDD, "ntx": NTX,
        "note": "switching energy on nets only; excludes cell internal/short-circuit "
                "energy and leakage; no glitch timing (phase-2b pending)",
        "records": records,
    }
    (OUT / "phase2_net_energy.json").write_text(json.dumps(summary, indent=2))
    lines = ["# 阶段-2 网级开关能量（SPEF 电容 × 门级 VCD 翻转，pJ/事务）", "",
             summary["metric"], "",
             "| 零概率 | B0 | B1 | B2 | B3 | B4 | B1Δ | B2Δ | B3Δ | B4Δ |",
             "|---|" + "---|" * 8]
    for wl in LEVELS:
        vs = records[wl]
        row = [f"{vs[v]['switching_energy_pJ_tx']}" for v in VARIANTS]
        ds = [f"{vs[v]['delta_pct_vs_B0']:+.2f}%" for v in VARIANTS[1:]]
        lines.append(f"| {wl[1:]}% | " + " | ".join(row) + " | " + " | ".join(ds) + " |")
    lines += ["", "匹配网数示例（p90_B1 / p90_B3）: "
              f"{records['p90']['B1']['matched_nets']} / {records['p90']['B3']['matched_nets']}",
              f"未匹配翻转（合计）示例: {records['p90']['B1']['unmatched_transitions']} / "
              f"{records['p90']['B3']['unmatched_transitions']}"]
    (OUT / "phase2_net_energy.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()