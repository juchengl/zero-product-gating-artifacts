#!/usr/bin/env python3
"""Re-scale the G1 grid power numbers for the activity-window divisor error.

What happened: run_g1.sh passed ACT_T1 (the window's END time, 12000 ns) as
build_activity_tcl.py's `window_ns`, but the injected activity is
`transitions / window_ns`, i.e. toggles-per-ns -- so the divisor must be the
window's DURATION. The tb dumps [DUMPON=100, DUMPOFF=600] cycles and the clock
is 10 ns/cycle (`timescale 1ns/1ps` + `always #5 clk = ~clk`), so the real
window is 500 cycles x 10 ns = 5000 ns. Every acts_*.tcl carries
"# window 12000.0 ns" and clk activity 0.0834167 = 1000/12000 -- 1000 clk edges
is exactly 500 cycles, which independently confirms the 5000 ns duration.

Consequence: all injected activities, hence all dynamic power, are a factor
12000/5000 = 2.4 too LOW. Leakage is activity-independent, so only the
internal+switching columns scale. Because the same constant divided every
config, the *relative* comparison (and thus the G1 verdict) is unchanged.

The fix is to regenerate the acts files with 5000 and re-run report_power, but
that needs the window VCDs, which run_g1.sh deletes after a successful power
report. Until then this script gives the corrected absolutes from the retained
reports (note: those carry only 3 significant digits).

Usage: g1_window_rescale.py [dir]   (default: ~/b3_ihp/g1)
"""
import os
import re
import sys

WRONG_DIVISOR = 12000.0   # ns, passed as window_ns
TRUE_WINDOW = 5000.0      # ns, (DUMPOFF - DUMPON) * ns_per_cycle
SCALE = WRONG_DIVISOR / TRUE_WINDOW   # 2.4: fixes the toggles-per-ns divisor
VDD = 1.8   # sky130hd nominal, the platform these reports come from

# Second, independent factor: the tb clock is 10 ns/cycle (`timescale 1ns/1ps`
# + `always #5 clk = ~clk`) while every SDC says `create_clock -period 20.0`,
# i.e. the sim runs the chip at 100 MHz against a 50 MHz constraint. Dynamic
# power is proportional to toggle rate, so re-referencing to the constrained
# operating point divides by 2 again. Post-route timing does NOT support the
# simulated rate either (IHP nobuf WNS 7.575 ns at 20 ns -> ~80 MHz max).
TB_PERIOD_NS = 10.0
SDC_PERIOD_NS = 20.0
FREQ_REDUCE = TB_PERIOD_NS / SDC_PERIOD_NS   # 0.5

# name -> (sparsity label, T) for the grid points; the four unprefixed files are
# the original p30/T4 set.
POINTS = [
    ("p30T4", "b0"), ("p30T4", "b3"), ("p30T4", "auto"),
    ("p60T4", "b0"), ("p60T4", "b3"), ("p60T4", "auto"),
    ("p60T16", "b0"), ("p60T16", "b3"), ("p60T16", "auto"),
    ("p90T4", "b0"), ("p90T4", "b3"), ("p90T4", "auto"),
    ("p90T16", "b0"), ("p90T16", "b3"), ("p90T16", "auto"),
]

TOTAL_RE = re.compile(
    r"^Total\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)"
)


def read_total(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = TOTAL_RE.match(line.strip())
            if m:
                return [float(x) for x in m.groups()]
    return None


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/b3_ihp/g1")
    print("recorded reports divided every toggle count by %g ns; the dumped window "
          "is %g ns\n  -> x%.2f to get the simulated rate (tb clk = %g ns = %g MHz)"
          % (WRONG_DIVISOR, TRUE_WINDOW, SCALE, TB_PERIOD_NS, 1e3 / TB_PERIOD_NS))
    print("  -> x%.2f net to re-reference to the SDC operating point (%g ns = %g MHz)\n"
          % (SCALE * FREQ_REDUCE, SDC_PERIOD_NS, 1e3 / SDC_PERIOD_NS))
    hdr = "%-9s %-6s %11s %11s %11s %9s   %s"
    print(hdr % ("point", "variant", "recorded W", "@100MHz W", "@50MHz W",
                 "@50 mA", "comment"))
    rows = {}
    for point, var in POINTS:
        stem = var if point == "p30T4" else "%s_%s" % (point, var)
        path = os.path.join(d, "power_%s.txt" % stem)
        if not os.path.exists(path):
            print(hdr % (point, var, "-", "-", "-", "-", "NO REPORT"))
            continue
        internal, switching, leakage, total = read_total(path)
        at_100 = (internal + switching) * SCALE + leakage
        at_50 = (internal + switching) * SCALE * FREQ_REDUCE + leakage
        rows[(point, var)] = at_50
        note = ""
        if var == "auto":
            statics = [v for (p, vv), v in rows.items()
                       if p == point and vv in ("b0", "b3")]
            best = min(statics)
            rel = (at_50 - best) / best * 100.0
            note = "auto vs best_static: %+.2f%%%s" % (
                rel, "  (within 3-digit rounding of the source reports)"
                if abs(rel) < 0.2 else "")
        print(hdr % (point, var, "%.3e" % total, "%.3e" % at_100, "%.3e" % at_50,
                     "%.2f" % (at_50 / VDD * 1e3), note))
    print("\nOnly the magnitude changes: every config was divided by the same "
          "constant, so the G1 ranking is untouched. Differences below ~0.2% are "
          "inside the 3-significant-digit precision of power_*.txt and must not "
          "be read as a win either way.")


if __name__ == "__main__":
    main()
