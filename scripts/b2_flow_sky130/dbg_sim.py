import subprocess
from pathlib import Path
HOME = Path.home()
vvp = HOME / "b2_sky130/r2/tb0_u38.vvp"
r = subprocess.run(["vvp", str(vvp), "+VECTORS=" + str(HOME) + "/b2_sky130/r1/vec/p90_random_s101_n1000.txt",
                    "+PERIOD=20"], capture_output=True, text=True, timeout=120)
print("STDOUT:")
print(r.stdout[:900])
print("STDERR:")
print(r.stderr[:300])
