from pathlib import Path
p = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\paper\manuscript.tex")
t = p.read_text(encoding="utf-8")
old = "SDF-annotated (glitch-true) re-simulation confirms the ordering and widens the hold-vs-force gap. A layout-perturbation study"
new = ("SDF-annotated (glitch-true) re-simulation confirms the ordering and widens the hold-vs-force gap; "
       "a three-corner sweep (tt/ff/ss, 1.60--1.95 V, 25--100\\,$^\\circ$C) confirms the ordering is "
       "corner-stable within $\\pm0.15$ pp. A layout-perturbation study")
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("abstract corner sentence added")
else:
    print("pattern not found")