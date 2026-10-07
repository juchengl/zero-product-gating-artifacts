from pathlib import Path
p = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\r1_vcd\p90_random_s101_n1000_B3.window.vcd")
scope = []
nvars = 0
shown = 0
for line in p.read_text(errors="replace").splitlines():
    s = line.strip()
    if s.startswith("$scope"):
        scope.append(s.split()[2])
        if shown < 8:
            print("scope ->", scope); shown += 1
    elif s.startswith("$upscope"):
        scope.pop()
    elif s.startswith("$var"):
        nvars += 1
        if shown < 16:
            print("  var@", scope, s.split()[4]); shown += 1
    elif s.startswith("$enddefinitions"):
        break
print("total vars:", nvars)