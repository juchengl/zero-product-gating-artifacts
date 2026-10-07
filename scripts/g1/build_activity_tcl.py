"""Build a Tcl snippet injecting per-driver-pin power activities from the RAW
gate-level window VCD (v3): uses the VCD scope chain to name pins directly.

Inputs:
  netlist.v  - post-route verilog (unstripped); yields driver pin set
  vcd        - window-trimmed gate VCD (scopes tb_replay -> dut -> cells)
  period_ns / window_ns

For every VCD variable whose scope path is tb_replay->dut-><inst>-><net> with
(inst, net) a driver output pin of the netlist, and for top-level ports
(tb_replay->dut->port), we compute transitions (bit-level for vectors) and
emit set_power_activity -pins {inst/net} with toggles-per-ns activity.

Usage: python build_activity_tcl.py <netlist.v> <vcd> <out.tcl> <period> <window_ns>

Env:
  CELL_PREFIX  stdcell name prefix in the netlist (default sky130_fd_sc_hd__;
               IHP SG13G2 uses sg13g2_). The B2 original hardcoded the sky130
               prefix, which silently matched nothing on an IHP netlist and
               emitted an activity file with 3 injected pins out of 106k -- the
               resulting report_power looked entirely plausible because it was
               just the tool's default activity.
"""
import os
import re, sys
from pathlib import Path

OUT_PINS = {"Y", "Q", "Q_N", "X", "CO", "S", "SUM"}
CELL_PREFIX = os.environ.get("CELL_PREFIX", "sky130_fd_sc_hd__")
CELL_RE = re.compile(re.escape(CELL_PREFIX) + r"\S+\s+(\\?\S+)\s*\(")
# DUT top-level port names that must not be treated as driver pins.
PORT_NAMES = {"a", "b", "clk", "rst", "clear", "valid", "out_valid", "acc",
              "cfg_addr", "cfg_wdata", "cfg_we", "ro_addr", "ro_data",
              "inj_valid", "inj_a", "inj_b"}


def parse_netlist(path: Path):
    driver = {}
    names = set()
    text = path.read_text(errors="replace")
    for chunk in text.split(");"):
        m = CELL_RE.search(chunk)
        if not m:
            continue
        inst = m.group(1).lstrip("\\")
        for pm in re.finditer(r"\.(\w+)\s*\(\s*(\\?\S+?)\s*\)", chunk[m.end():]):
            pin, net = pm.group(1), pm.group(2).lstrip("\\")
            names.add(net)
            if pin in OUT_PINS:
                driver.setdefault((inst, pin), net)
    return driver, names


def parse_vcd(path: Path):
    """All variables sit flat under tb_replay->dut. Returns id -> dict with
    name/width and a port flag (top ports are the only non-net vars)."""
    info = {}
    scope = []
    for line in path.read_text(errors="replace").splitlines():
        t = line.strip()
        if t.startswith("$scope"):
            scope.append(t.split()[2])
        elif t.startswith("$upscope"):
            scope.pop()
        elif t.startswith("$var"):
            p = t.split()
            vid, width, raw_name = p[3], int(p[2]), p[4].lstrip("\\")
            if len(scope) != 2 or scope[0] != "tb_replay" or scope[1] != "dut":
                continue
            is_port = raw_name.split("[")[0] in PORT_NAMES
            info[vid] = {"port": is_port, "name": raw_name, "width": width}
        elif t.startswith("$enddefinitions"):
            return info
    return info


def count_transitions(path: Path, info):
    """bit-level transitions per var id; also per-bit tallies."""
    toggles = {}
    bit_toggles = {}
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
        if vid not in info:
            continue
        w = info[vid]["width"]
        bits = bits.rjust(w, "x")
        prev = last.get(vid)
        if prev is not None:
            n = 0
            for i in range(w):
                if prev[i] != bits[i]:
                    n += 1
                    bit_toggles[(vid, i)] = bit_toggles.get((vid, i), 0) + 1
            toggles[vid] = toggles.get(vid, 0) + n
        last[vid] = bits
    return toggles, bit_toggles


def main():
    netlist, vcd, out, period_ns, window_ns = sys.argv[1], Path(sys.argv[2]), sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
    driver, names = parse_netlist(Path(netlist))
    rev = {net: (inst, pin) for (inst, pin), net in driver.items()}
    info = parse_vcd(vcd)
    toggles, bit_toggles = count_transitions(vcd, info)
    lines = ["# generated v3: per-driver-pin power activity injection",
             f"# window {window_ns} ns"]
    n_inj, n_skip, n_unmap = 0, 0, 0

    def resolve(net):
        if net in names:
            return net
        if "core." + net in names:
            return "core." + net
        return ""

    for vid, count in toggles.items():
        v = info[vid]
        if v["port"]:
            base = v["name"].split("[")[0]
            if v["width"] == 1:
                lines.append(f"set_power_activity -pins {{{base}}} -activity {count / window_ns:.6g}")
                n_inj += 1
            else:
                for i in range(v["width"]):
                    bt = bit_toggles.get((vid, i), 0)
                    lines.append(f"set_power_activity -pins {{{base}[{i}]}} -activity {bt / window_ns:.6g}")
                    n_inj += 1
            continue
        net = resolve(v["name"])
        if not net or net not in rev:
            n_unmap += 1
            continue
        inst, pin = rev[net]
        act = count / window_ns
        lines.append(f'set_power_activity -pins {{"{inst}/{pin}"}} -activity {act:.6g}')
        n_inj += 1
    Path(out).write_text("\n".join(lines) + "\n")
    print(f"injected {n_inj} driver pins; {n_unmap} unmapped; {n_skip} skipped")
    # A silent near-empty injection still produces a perfectly plausible-looking
    # report_power (it is just the tool's default activity), so refuse outright.
    # This caught the first IHP run here: 3 of 106,258 pins injected.
    if not driver:
        print("FATAL: 0 driver pins parsed from the netlist -- CELL_PREFIX=%r is wrong"
              % CELL_PREFIX)
        sys.exit(1)
    if n_inj < 0.02 * len(driver):
        print("FATAL: only %.2f%% of %d driver pins received activity -- do NOT trust "
              "the resulting report_power (check VCD scope names / CELL_PREFIX)"
              % (100.0 * n_inj / len(driver), len(driver)))
        sys.exit(1)


if __name__ == "__main__":
    main()