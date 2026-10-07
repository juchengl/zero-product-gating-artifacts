"""Audit R2 (zero-delay re-run): sims PASS? acts files non-empty? u42 B3 vs B0 power identical?
Re-run each sim capturing output to verify PASS, and compare power files.
"""
import subprocess, re, json
from pathlib import Path
import os

HOME = Path.home()
WORK = HOME / "b2_sky130/r2"
P = "/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup"
WL = "p90_random_s101_n1000"

print("=== re-run 10 sims with PASS capture ===")
for U in ("u38", "u42"):
    for n in range(5):
        vvp = WORK / f"tb{n}_{U}.vvp"
        if not vvp.exists():
            print("MISSING VVP", U, n); continue
        r = subprocess.run(["vvp", str(vvp), f"+VECTORS={WORK}/r1vec_reuse.txt" if False else f"{HOME}/b2_sky130/r1/vec/{WL}.txt",
                            "+PERIOD=20"],
                           capture_output=True, text=True, timeout=120)
        passed = "PASS replay" in r.stdout
        print(f"u{U[1:]} B{n}: {'PASS' if passed else 'FAIL'} | {r.stdout.strip().splitlines()[-1][:60] if r.stdout.strip() else 'no-out'}")

print("\n=== acts tcl sizes ===")
for U in ("u38", "u42"):
    for n in range(5):
        a = WORK / f"odo/acts_{WL}_B{n}_{U}.tcl"
        print(U, n, a.stat().st_size if a.exists() else "MISSING")

print("\n=== u42 B0 vs B3 power identical? ===")
for pair in [("B0", "B3"), ("B0", "B2")]:
    f1 = WORK / f"odo/{WL}_{pair[0]}_u42/power.txt"
    f2 = WORK / f"odo/{WL}_{pair[1]}_u42/power.txt"
    if f1.exists() and f2.exists():
        same = f1.read_bytes() == f2.read_bytes()
        print(pair, "identical" if same else "differ")
    else:
        print(pair, "missing")