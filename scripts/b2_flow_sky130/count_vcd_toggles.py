"""Count total transitions per net id in a windowed VCD (value-change section
only). Compare B1 vs B3 gate activity directly.

Usage: python count_vcd_toggles.py <vcd1> <vcd2>
"""
import sys
from pathlib import Path

def count(path: Path):
    toggles = {}
    last = {}
    ntime = 0
    for line in path.read_text(errors="replace").splitlines():
        t = line.strip()
        if t.startswith("$"):
            continue
        if t.startswith("#"):
            ntime += 1
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
    return toggles, ntime

def main():
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    ta, na = count(a)
    tb, nb = count(b)
    sa, sb = sum(ta.values()), sum(tb.values())
    print(f"{a.name}: {len(ta)} nets, {sa} total transitions, {na} timestamps")
    print(f"{b.name}: {len(tb)} nets, {sb} total transitions, {nb} timestamps")
    print(f"ratio B3/B1: {sb/sa:.3f}" if sa else "")

if __name__ == "__main__":
    main()