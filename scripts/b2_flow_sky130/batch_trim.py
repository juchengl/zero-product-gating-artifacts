"""Batch trim all gate VCDs in the replay directory to measurement window.
Usage: python batch_trim.py <vcd_dir>
"""
import sys, subprocess, os
from pathlib import Path

vcd_dir = Path(sys.argv[1])
vcds = sorted(vcd_dir.glob("*_B?.vcd"))
print(f"vcds: {len(vcds)}")
for v in vcds:
    out = v.with_suffix(".window.vcd")
    if out.exists():
        continue
    subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "window_vcd.py"),
         str(v), str(out), "--start-tick", "60000", "--end-tick", "20080000"],
        capture_output=True, timeout=60)
    print(f"trimmed {v.name}", end=" ")
window = sorted(vcd_dir.glob("*.window.vcd"))
print(f"\ntrimmed: {len(window)}")