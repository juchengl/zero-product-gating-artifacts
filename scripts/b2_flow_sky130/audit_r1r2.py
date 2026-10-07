"""Audit R1/R2 simulation integrity.
A) R1: all 20 sims PASS? SDF warnings count (FF unannotated expected).
B) R2: window VCD completeness (last timestamp == 20080000) for all 10; B1 u38 anomaly check.
C) R1 glitch reality: toggle counts R1 vs zero-delay for p90 (same netlist names, stripped).
"""
import re, sys, json
from pathlib import Path

HOME = Path.home()
R1V = HOME / "b2_sky130/r1/vcd"
R2V = HOME / "b2_sky130/r2/vcd"
WLS = ["p00_random_s101_n1000", "p30_random_s101_n1000", "p60_random_s101_n1000", "p90_random_s101_n1000"]
VS = [0, 1, 2, 3, 4]

print("=== A) R1 replay PASS + SDF warnings ===")
bad = 0
for wl in WLS:
    for n in VS:
        log = R1V / f"{wl}_B{n}.run.log"
        if not log.exists():
            print("MISSING LOG", wl, n); bad += 1; continue
        t = log.read_text(errors="replace")
        passed = "PASS replay" in t
        sdfwarn = t.count("SDF WARNING")
        if not passed:
            print("FAIL", wl, n, t.strip().splitlines()[-1][:100]); bad += 1
print(f"R1 sims: {20-bad}/20 PASS, bad={bad}")

print("\n=== B) R2 window VCD completeness ===")
for U in ("u38", "u42"):
    for n in VS:
        w = R2V / f"p90_random_s101_n1000_B{n}_{U}.window.vcd"
        if not w.exists():
            print("MISSING", U, n); continue
        # last timestamp in window file
        last = None
        for line in w.read_text(errors="replace").splitlines():
            if line.startswith("#"):
                last = line[1:]
        ok = (last == "20080000")
        if not ok:
            print("INCOMPLETE", U, n, "last=", last)
print("R2 completeness checked")

print("\n=== C) R1 glitch reality: toggles r1 vs zero-delay (p90, stripped netlist vars) ===")
def count_trans(path):
    toggles = 0
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
        if vid in last and last[vid] != bits:
            toggles += 1
        last[vid] = bits
    return toggles

n90 = "p90_random_s101_n1000"
for n in VS:
    r1v = R1V / f"{n90}_B{n}.window.vcd"
    zdv = Path(r"/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/results/replay_gate_gate_smoke") / f"{n90}_B{n}.window.vcd"
    t1 = count_trans(r1v)
    t0 = count_trans(zdv)
    print(f"B{n}: r1={t1}  zerodelay={t0}  ratio={t1/max(1,t0):.2f}")
