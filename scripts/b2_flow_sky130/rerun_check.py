import subprocess
from pathlib import Path
HOME = Path.home()
WL = "p90_random_s101_n1000"
for U in ("u38", "u42"):
    for n in range(5):
        vvp = HOME / f"b2_sky130/r2/tb{n}_{U}.vvp"
        r = subprocess.run(["vvp", str(vvp),
                            "+VECTORS=" + str(HOME) + f"/b2_sky130/r1/vec/{WL}.txt",
                            "+PERIOD=20"], capture_output=True, text=True, timeout=120)
        status = "PASS" if "PASS replay" in r.stdout else "FAIL"
        tail = r.stdout.strip().splitlines()[-1][:80] if r.stdout.strip() else "no-out"
        print(U, n, status, "|", tail)
