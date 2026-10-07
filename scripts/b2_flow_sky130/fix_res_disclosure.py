from pathlib import Path
p = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\paper\manuscript.tex")
t = p.read_text(encoding="utf-8")
old = ("\\texttt{report\\_power} prints 3 significant figures ($\\approx\\pm0.1\\%$ relative, "
       "$\\ll$ the $4$--$7\\%$ main effects but at the limit for the $+0.47\\%$ detection term, "
       "reported as ``at resolution limit'').")
new = ("\\texttt{report\\_power} prints 3 significant figures ($\\approx\\pm0.1\\%$ relative, "
       "$\\ll$ the $4$--$7\\%$ main effects). Re-measuring the smallest decomposed term with "
       "6-digit reporting (\\texttt{-digits 6}, all 9 workloads) shows the 3-digit print had "
       "\\emph{understated} the detection cost by $\\sim40\\%$ ($+0.77\\%$ vs $+0.47\\%$); "
       "all decomposition numbers quoted use the 6-digit re-measurement where available.")
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("resolution disclosure updated")
else:
    print("pattern not found")