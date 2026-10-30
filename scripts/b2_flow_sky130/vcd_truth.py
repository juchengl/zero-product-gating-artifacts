# -*- coding: utf-8 -*-
"""Gate-level VCD -> per-driver-pin truth + set_power_activity Tcl.

Structure of the iverilog VCD for the flat gate netlist (verified on mac_b3):
  tb_replay.dut.<net>            <- internal net, name like _0915_
  tb_replay.dut.<inst>.<pin>     <- instance pin; almost all of these are the
                                    power/ground pins of the cell model
  tb_replay.dut                  <- top-level ports
So simulation truth is read per **net**, and the net name is the join key with
the netlist: net -> (instance, driver pin) via parse_netlist.

Outputs (into out_dir):
  truth.tsv      net  driver_pin  toggles  duty  act_per_cycle
  acts_inj.tcl   set_power_activity for every driver pin found in the netlist
  acts_prop.tcl  set_power_activity for top-level ports only (propagation proxy)

Usage:
  python3 vcd_truth.py <netlist.v> <vcd> <window_ns> <period_ns> <out_dir>
"""
import re
import sys
from pathlib import Path

POWER_PINS = {"VPWR", "VGND", "VNB", "VPB", "VDD", "VSS"}
OUT_PINS = {"Y", "Q", "Q_N", "X", "CO", "S", "SUM"}


def parse_netlist(path):
    """net -> (inst, pin) for driver pins."""
    text = Path(path).read_text(errors="replace")
    rev = {}
    for chunk in text.split(");"):
        m = re.search(r"sky130_fd_sc_hd__\S+\s+(\\?\S+)\s*\(", chunk)
        if not m:
            continue
        inst = m.group(1).lstrip("\\")
        for pm in re.finditer(r"\.(\w+)\s*\(\s*(\\?\S+?)\s*\)", chunk[m.end():]):
            pin, net = pm.group(1), pm.group(2).lstrip("\\")
            if pin in OUT_PINS:
                rev.setdefault(net, (inst, pin))
    return rev


def parse_vcd(path):
    """id -> (scope_path, name, width)."""
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
                ids[p[3]] = (".".join(scope), p[4], int(p[2]))
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
                if vid not in ids or ids[vid][2] != 1:
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


def main():
    netlist, vcd, win_ns, period_ns, outdir = sys.argv[1:6]
    win_ns, period_ns = float(win_ns), float(period_ns)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    rev = parse_netlist(netlist)
    ids = parse_vcd(vcd)
    toggles, high = window_stats(vcd, ids, 0, win_ns * 1000.0)
    cycles = win_ns / period_ns
    win_ps = win_ns * 1000.0

    rows, inj, prop, reg = [], [], [], []
    for vid, (scope, name, width) in ids.items():
        if width != 1 or name in POWER_PINS:
            continue
        parts = scope.split(".")
        t = toggles[vid]
        duty = min(max(high[vid] / win_ps, 0.0), 1.0)
        act = t / cycles
        if len(parts) == 2:
            # tb_replay.dut.<net>  (internal net) or a top-level port
            pin = rev.get(name)
            if pin:
                rows.append((name, "%s/%s" % pin, t, duty, act))
                inj.append("sta::set_power_pin_activity_by_name {%s/%s} %.6f %.6f"
                           % (pin[0], pin[1], act, duty))
            else:
                rows.append((name, name, t, duty, act))
                prop.append("sta::set_power_pin_activity_by_name {%s} %.6f %.6f"
                            % (name, act, duty))
        elif len(parts) >= 3:
            # tb_replay.dut.<inst path>...<pin> ; keep the full instance path
            # (netlist path names include the RTL hierarchy, e.g. core.a_q[0]$...)
            inst = ".".join(parts[2:])
            rows.append((name, "%s/%s" % (inst, name), t, duty, act))
            inj.append("sta::set_power_pin_activity_by_name {%s/%s} %.6f %.6f"
                       % (inst, name, act, duty))
            if name in ("Q", "Q_N"):
                reg.append("lappend PAIRS {%s} {%s %s}" % (inst, act, duty))

    rows.sort(key=lambda r: -r[2])
    (out / "truth.tsv").write_text(
        "net\tdriver_pin\ttoggles\tduty\tact_per_cycle\n"
        + "\n".join("%s\t%s\t%d\t%.4f\t%.6f" % r for r in rows), encoding="utf-8")
    (out / "acts_inj.tcl").write_text("\n".join(inj) + "\n", encoding="utf-8")
    (out / "acts_reg.tcl").write_text("set PAIRS {}\n" + "\n".join(reg) + "\n", encoding="utf-8")
    (out / "acts_prop.tcl").write_text("\n".join(prop) + "\n", encoding="utf-8")
    print("vars=%d nets=%d driver_pins=%d reg_pins=%d ports=%d"
          % (len(ids), len(rows), len(inj), len(reg), len(prop)))


if __name__ == "__main__":
    main()
