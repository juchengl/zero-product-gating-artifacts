import json, re
from pathlib import Path
root = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\power_smoke")
for wl in ("p90_random_s101_n1000",):
    print("==", wl)
    for v in ("B1", "B3", "B4"):
        t = (root / f"{wl}_{v}" / "power.txt").read_text()
        total = re.search(r"^Total\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
        seq = re.search(r"^Sequential\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
        comb = re.search(r"^Combinational\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
        clk = re.search(r"^Clock\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)", t, re.M)
        f = lambda m: " ".join(f"{float(x)*1e3:.1f}" for x in m.groups()) if m else "NA"
        print(f" {v}: int/sw/leak (mW)")
        print(f"   Total: {f(total)}")
        print(f"   Seq:   {f(seq)}")
        print(f"   Comb:  {f(comb)}")
        print(f"   Clock: {f(clk)}")
