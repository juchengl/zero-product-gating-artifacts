from pathlib import Path
p = Path("/mnt/c/Users/Administrator/Desktop/科研/B2_MAC_Followup/paper/manuscript.tex")
t = p.read_text(encoding="utf-8")
# find the area line by a stable prefix and rewrite the whole line
lines = t.splitlines()
for i, l in enumerate(lines):
    if l.startswith("Mapping estimate (sky130hd, pre-PnR): B0"):
        lines[i] = ("Mapping estimate (sky130hd, pre-PnR): B0 $=6204.70\\,\\mu\\mathrm{m}^2$; "
                    "B1 $=6349.84$ ($+2.34\\%$); B2 $=6273.52$ ($+1.11\\%$); "
                    "B3 $=6403.64$ ($+3.21\\%$); B4 $=6397.39$ ($+3.11\\%$); "
                    "all meet timing at $20\\,\\mathrm{ns}$.")
        print("rewritten line", i + 1)
        break
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
