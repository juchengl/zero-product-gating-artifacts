import re
from pathlib import Path
p = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\paper\manuscript.tex")
t = p.read_text(encoding="utf-8")

# 1) reference fig0 (pipeline) in Methodology intro
if "fig0_pipeline" not in t:
    t = t.replace(
        "\\subsection{Measurement pipeline (corrected flow)}",
        "\\subsection{Measurement pipeline (corrected flow)}\nFig.~\\ref{fig:pipeline} shows the corrected flow and the broken branch (§\\ref{sec:artifact}).")
    # add figure env at the end before bibliography? place after pipeline subsection text
    t = t.replace(
        "\\subsection{Stimuli and statistics}",
        "\\begin{figure}[h]\\centering\\includegraphics[width=0.95\\linewidth]{fig0_pipeline.png}\n"
        "\\caption{Measurement pipeline. Corrected flow (top): post-route netlists, in-session extraction, gate replay (zero-delay and SDF), per-driver-pin activity injection, STA power. The broken branch (bottom, red) is the standard RTL-VCD→propagation path analyzed in §\\ref{sec:artifact}.}\\label{fig:pipeline}\\end{figure}\n\n"
        "\\subsection{Stimuli and statistics}")

# 2) reference fig5 (glitch wave) in §4.4
if "fig5_glitch_wave" not in t:
    t = t.replace(
        "\\label{tab:glitch}\n\\end{table}",
        "\\label{tab:glitch}\n\\end{table}\n\n"
        "\\begin{figure}[h]\\centering\\includegraphics[width=0.9\\linewidth]{fig5_glitch_wave.png}\n"
        "\\caption{Waveform of an internal multiplier net (p90, B3): the SDF glitch-true trace shows narrow glitch pulses absent from the zero-delay trace.}\\label{fig:glitchwave}\\end{figure}")

# 3) reference fig4 (layout) in §4.5
if "fig4_layout" not in t:
    t = t.replace(
        "\\label{tab:layout}\n\\end{table}",
        "\\label{tab:layout}\n\\end{table}\n\n"
        "\\begin{figure}[h]\\centering\\includegraphics[width=0.85\\linewidth]{fig4_layout.png}\n"
        "\\caption{Layout robustness: total energy vs B0 at $90\\%$ zero across three layouts. B1 flips sign; B3 never regresses.}\\label{fig:layoutbar}\\end{figure}")

p.write_text(t, encoding="utf-8")
print("manuscript updated:",
      "fig0" if "fig0_pipeline" in t else "", 
      "fig5" if "fig5_glitch_wave" in t else "",
      "fig4" if "fig4_layout" in t else "")