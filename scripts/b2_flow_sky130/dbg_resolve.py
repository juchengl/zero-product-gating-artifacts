import sys, re
sys.path.insert(0, r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\flow_sky130")
from build_activity_tcl import parse_netlist, count_vcd, resolve
from pathlib import Path

nl = Path(r"\\wsl.localhost\Ubuntu-22.04\home\research\orfs-git\flow\results\sky130hd\mac_b3\base\6_final.v")
driver, names = parse_netlist(nl)
print("names in netlist:", len(names), "drivers:", len(driver))
samples = list(names)[:5]
print("sample names:", samples)
vcd = Path(r"\\wsl.localhost\Ubuntu-22.04\home\research\b2_sky130\odo\p90_random_s101_n1000_B3.rsvcd")
name2id = {}
for line in vcd.read_text(errors="replace").splitlines():
    t = line.strip()
    if t.startswith("$var"):
        p = t.split()
        name2id[p[3]] = p[4]
print("vcd vars:", len(name2id))
vnames = list(dict.fromkeys(name2id.values()))
print("sample vcd names:", vnames[:6])
ok = 0
for n in vnames:
    r = resolve(n, names)
    if r:
        ok += 1
print(f"resolvable vcd names: {ok}/{len(vnames)}")
misses = [n for n in vnames if not resolve(n, names)]
print("miss samples:", misses[:6])
# check whether misses are ports
portscand = {"a","b","clk","rst","clear","valid","out_valid","acc"}
print("miss-that-look-like-ports:", sum(1 for n in misses if n.split("[")[0].rstrip("\\") in portscand))