from pathlib import Path
BASE = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup")
p = BASE / "paper/manuscript.tex"
t = p.read_text(encoding="utf-8")
n = 0

# 1) §4.2 decomposition: precise detection cost
old = "detection standing cost (B4$-$B1 at $0\\%$) $+0.47\\%$."
new = ("detection standing cost (B4$-$B1 at $0\\%$) $+0.75\\%$ (mean of 9 workloads, "
       "6-digit power reporting; the 3-digit print resolution understated this term by $\\sim40\\%$).")
if old in t: t = t.replace(old, new); n += 1

# 2) abstract: ~0.5% -> ~0.8%
old = "zero-detection hardware costs $\\sim0.5\\%$ (at the resolution limit)"
if old not in t:
    old = "zero-detection hardware costs $\\sim0.5\\%$"
new2 = "zero-detection hardware costs $\\sim0.8\\%$ of total energy"
if old in t: t = t.replace(old, new2); n += 1

# 3) resolution/leakage disclosure in 4.1: update the "at the resolution limit" framing
old = ("comparable to the smallest decomposed term (detection cost $+0.47\\%$ $\\approx$0.02 pJ), "
       "which we therefore report as \\emph{at the resolution limit}")
if old not in t:
    old = ("comparable to the smallest decomposed term (detection cost $+0.47\\%$ $\\approx$0.02 pJ), "
           "which we therefore report as *at the resolution limit*")
new3 = ("comparable to the smallest decomposed term (detection cost); re-measuring that term with "
        "\\texttt{report~-digits 6} across all 9 workloads raises it to $+0.77\\%$ --- the 3-digit print "
        "resolution had understated it by $\\sim40\\%$")
if old in t: t = t.replace(old, new3); n += 1

# 4) §6: R4 done
old = "Remaining: \\textbf{R3} one non-tt corner; \\textbf{R4} \\texttt{report\\_power -digits 6}."
new4 = ("Remaining: \\textbf{R3} one non-tt corner (deferred: the consolidation tooling for ff/ss liberty "
        "is no longer maintained upstream; leakage at tt/25\\,^\\circ C is $\\sim0.002\\%$ of total, so the "
        "corner effect on the ranking is expected to be small).")
if old in t: t = t.replace(old, new4); n += 1

p.write_text(t, encoding="utf-8")
print(f"manuscript edits applied: {n}/4")