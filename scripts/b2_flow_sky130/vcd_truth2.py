# -*- coding: utf-8 -*-
"""Gate-level VCD -> per-(instance,pin) activity, hierarchy-safe.

The VCD carries several names per signal id (net name, instance-pin name, and
names inside the cell behavioural model such as `.base.A`).  The join key with
the netlist is the **instance path**: for every VCD variable we strip its scope
back to the longest prefix that is a real instance name in the netlist.

Outputs (out_dir):
  truth.tsv     inst  pin  net  toggles  duty  act_per_cycle
  acts_inj.tcl  every driver pin found
  acts_reg.tcl  registers only (Q/Q_N) -- the set the stock flow annotates
  summary.json  counts

Usage: python3 vcd_truth2.py <netlist.v> <vcd> <window_ns> <period_ns> <out_dir>
"""
import json
import re
import sys
from pathlib import Path

POWER_PINS = {"VPWR", "VGND", "VNB", "VPB", "VDD", "VSS"}
OUT_PINS = {"Y", "Q", "Q_N", "X", "CO", "S", "SUM", "COUT"}


def parse_netlist(path):
    """Instance names present in the netlist (flat path names)."""
    text = Path(path).read_text(errors="replace")
    insts = set()
    for m in re.finditer(r"sky130_fd_sc_hd__\w+\s+(\\?\S+)\s*\(", text):
        insts.add(m.group(1).lstrip("\\"))
    return insts


def parse_vcd(path):
    """id -> list of (scope_path, name, width). One id may carry several names."""
    ids = {}
    scope = []
    with open(path, errors="replace") as f:
        for line in f:
            t = line.strip()
            if t.startswith("$scope"):
                scope.append(t.split()[2])
            elif t.startswith("$upscope"):
                if scope:
                    scope.pop()
            elif t.startswith("$var"):
                p = t.split()
                ids.setdefault(p[3], []).append((".".join(scope), p[4], int(p[2])))
            elif t.startswith("$enddefinitions"):
                break
    return ids


def window_stats(path, ids, t0_ps, t1_ps):
    toggles = dict.fromkeys(ids, 0)
    high = dict.fromkeys(ids, 0.0)
    state = {k: "0" for k in ids}
    t_change = dict.fromkeys(ids, t0_ps)
    cur, in_win = 0, False
    with open(path, errors="replace") as f:
        for line in f:
            if not line:
                continue
            c = line[0]
            if c == "#":
                cur = int(line[1:])
                in_win = t0_ps <= cur <= t1_ps
                continue
            if c in "01xzXZ" and len(line) > 2:
                vid, v = line[1:].strip(), c
            elif c in "bB":
                parts = line[1:].split()
                if len(parts) != 2:
                    continue
                val, vid = parts[0], parts[1].strip()
                if vid not in ids:
                    continue
                v = val[-1]
            else:
                continue
            if vid not in ids:
                continue
            if not in_win:
                state[vid] = "1" if v == "1" else "0"
                t_change[vid] = cur
                continue
            prev = state[vid]
            now = "1" if v == "1" else "0"
            if now != prev:
                toggles[vid] += 1
                if prev == "1":
                    high[vid] += cur - max(t_change[vid], t0_ps)
                t_change[vid] = cur
                state[vid] = now
    for vid in ids:
        if state[vid] == "1":
            high[vid] += max(t1_ps - max(t_change[vid], t0_ps), 0)
    return toggles, high


def match_inst(scope, insts):
    """Strip the scope back until it names a real instance."""
    s = scope
    while s:
        if s in insts:
            return s
        i = s.rfind(".")
        if i < 0:
            return None
        s = s[:i]
    return None


def main():
    netlist, vcd, win_ns, period_ns, outdir = sys.argv[1:6]
    win_ns, period_ns = float(win_ns), float(period_ns)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    insts = parse_netlist(netlist)
    ids = parse_vcd(vcd)
    toggles, high = window_stats(vcd, ids, 0, win_ns * 1000.0)
    cycles = win_ns / period_ns
    win_ps = win_ns * 1000.0
    per_s = 1e9 / period_ns   # transitions per cycle -> per second

    # best record per (inst,pin): prefer driver pins, then any pin
    best = {}
    for vid, names in ids.items():
        t = toggles[vid]
        duty = min(max(high[vid] / win_ps, 0.0), 1.0)
        act = t / cycles
        for scope, name, width in names:
            if width != 1 or name in POWER_PINS:
                continue
            if not scope.startswith("tb_replay.dut"):
                continue
            sub = scope[len("tb_replay.dut"):].lstrip(".")
            inst = match_inst(sub, insts)
            if inst is None:
                continue
            key = (inst, name)
            rank = 2 if name in OUT_PINS else 1
            if key not in best or rank > best[key][0]:
                best[key] = (rank, t, duty, act)

    rows, inj, reg = [], [], []
    for (inst, name), (rank, t, duty, act) in best.items():
        rows.append((inst, name, t, duty, act))
        if rank == 2:
            inj.append("sta::set_power_pin_activity_by_name {%s/%s} %.6e %.6f"
                       % (inst, name, act * per_s, duty))
            if name in ("Q", "Q_N"):
                reg.append("set k {%s}\nset ACT($k) {%.6e %.6f}" % (inst, act * per_s, duty))

    rows.sort(key=lambda r: -r[4])
    (out / "truth.tsv").write_text(
        "inst\tpin\ttoggles\tduty\tact_per_cycle\n"
        + "\n".join("%s\t%s\t%d\t%.4f\t%.6f" % r for r in rows), encoding="utf-8")
    (out / "acts_inj.tcl").write_text("\n".join(inj) + "\n", encoding="utf-8")
    (out / "acts_reg.tcl").write_text("\n".join(reg) + "\n", encoding="utf-8")
    info = dict(ids=len(ids), insts=len(insts), records=len(rows),
                driver_pins=len(inj), reg_pins=len(reg))
    (out / "summary.json").write_text(json.dumps(info), encoding="utf-8")
    print("ids=%d insts=%d records=%d driver=%d reg=%d"
          % (info["ids"], info["insts"], info["records"], info["driver_pins"], info["reg_pins"]))


if __name__ == "__main__":
    main()
