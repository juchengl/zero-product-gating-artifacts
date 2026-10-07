from pathlib import Path
ZD = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results\replay_gate_gate_smoke\p90_random_s101_n1000_B3.window.vcd")
GL = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\r1_vcd\p90_random_s101_n1000_B3.window.vcd")

def value_at(path, netname, t_target):
    id_ = None
    t = 0.0
    val = None
    scope = []
    in_defs = True
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if in_defs:
            if s.startswith("$scope"): scope.append(s.split()[2])
            elif s.startswith("$upscope"): scope.pop()
            elif s.startswith("$var"):
                p = s.split()
                if len(scope) == 2 and p[4].lstrip("\\") == netname and p[2] == "1":
                    id_ = p[3]
            elif s.startswith("$enddefinitions"):
                in_defs = False
            continue
        if s.startswith("#"):
            t = float(s[1:]) / 1000.0
            if t > t_target and val is not None:
                return val
            continue
        if id_ and len(s) >= 2 and s[0] in "01xXzZ" and s[1:] == id_:
            val = s[0]
    return val

for tt in (100.0, 160.0, 200.0):
    z = value_at(ZD, "_0491_", tt)
    g = value_at(GL, "_0491_", tt)
    print(f"t={tt}ns  zd={z}  glitch={g}")