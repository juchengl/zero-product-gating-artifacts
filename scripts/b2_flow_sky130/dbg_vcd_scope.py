from pathlib import Path
import sys
p = Path(r"\\wsl.localhost\Ubuntu-22.04\home\research\orfs-git\flow\results\sky130hd\mac_b3\base\6_final.v")
v = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results\replay_gate_gate_smoke\p90_random_s101_n1000_B3.window.vcd")
scope = []
count = 0
shown = 0
for line in v.read_text(errors="replace").splitlines():
    t = line.strip()
    if t.startswith("$scope"):
        scope.append(t.split()[2])
        if shown < 6:
            print("scope ->", scope)
            shown += 1
    elif t.startswith("$upscope"):
        scope.pop()
    elif t.startswith("$var"):
        count += 1
        if shown < 12:
            print("  var@", scope, t.split()[4])
            shown += 1
    elif t.startswith("$enddefinitions"):
        break
print("total vars:", count)