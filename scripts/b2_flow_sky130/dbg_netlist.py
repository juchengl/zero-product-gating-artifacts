import re
from pathlib import Path
t = Path(r"\\wsl.localhost\Ubuntu-22.04\home\research\orfs-git\flow\results\sky130hd\mac_b3\base\6_final.v").read_text(errors="replace")
lines = t.splitlines()
# show a couple of cell instance lines
inst_lines = [l for l in lines if re.search(r"sky130_fd_sc_hd__\w+_?\d*\s+\\?\w", l) and "module" not in l]
print("sample inst lines:")
for l in inst_lines[:4]:
    print("   ", l.strip()[:150])
inst_re = re.compile(r"sky130_fd_sc_hd__\S+\s+(\S+)\s*\(", re.S)
print("instance regex matches:", len(inst_re.findall(t)))
m = inst_re.search(t)
print("first match:", m.group(1) if m else None)