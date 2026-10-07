#!/usr/bin/env python3
"""Make an OpenROAD-written SDF actually bind in Icarus Verilog.

OpenROAD's write_sdf emits every delay as a two-slot min::max group, e.g.
    (IOPATH S0 X (0.193::0.193) (0.226::0.226))
so the min:typ:max *typ* slot is empty. Icarus's sdf parser accepts that spelling
without a word (no error, no warning, "Unable to match ModPath" never fires) but
sdf_iopath_delays() then finds delval_list->val[typ].defined == 0, skips the
assignment, and vpi_put_delays() writes back the delays the specify block already
had -- i.e. the annotation silently does nothing. Measured on a two-buffer probe:
    (3.0:3.0:3.0)  -> rise 16000   (binds)
    (3.000::3.000) -> rise 12000   (silently ignored)
Filling the typ slot makes it bind. In this SDF 41% of the 936,007 groups have
min != max, so the fill rule is a real modelling choice, not cosmetic:
    --fill max  (default) slow corner, conservative for glitch/timing risk
    --fill min  fast corner
    --fill mid  midpoint, closest estimator of "typical"

Usage: sdf_fill_typ.py IN.sdf OUT.sdf [--fill max|min|mid]
"""
import re
import sys

GROUP = re.compile(r"\((\d*\.?\d+)::(\d*\.?\d+)\)")


def pick(a, b, how):
    x, y = float(a), float(b)
    if how == "min":
        return x
    if how == "mid":
        return (x + y) / 2.0
    return y


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, dst = sys.argv[1], sys.argv[2]
    how = "max"
    if "--fill" in sys.argv:
        how = sys.argv[sys.argv.index("--fill") + 1]
    n_grp = n_diff = 0

    def sub(m):
        nonlocal n_grp, n_diff
        n_grp += 1
        if m.group(1) != m.group(2):
            n_diff += 1
        t = pick(m.group(1), m.group(2), how)
        return "(%s:%s:%s)" % (m.group(1), ("%g" % t), m.group(2))

    with open(src, encoding="utf-8", errors="replace") as fi, \
         open(dst, "w", encoding="utf-8") as fo:
        for line in fi:
            fo.write(GROUP.sub(sub, line))
    print("fill=%-3s groups=%d min!=max=%d (%.2f%%) -> %s" % (how, n_grp, n_diff,
          100.0 * n_diff / max(n_grp, 1), dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
