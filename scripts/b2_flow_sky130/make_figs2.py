"""Generate supplementary paper figures:
fig0_pipeline.png  - measurement flow diagram (corrected vs broken path)
fig4_layout.png    - layout robustness grouped bars (R2)
fig5_glitch_wave.png - zero-delay vs SDF glitch waveform for one internal net
fig1 update        - overlay glitch-true points on boundary curves
"""
import json, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup")
OUT = BASE / "paper/fig"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- fig0: pipeline diagram ----------
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.axis("off")
def box(x, y, w, h, text, fc, fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                fc=fc, ec="k", lw=0.8))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs)
def arrow(x1, y1, x2, y2, color="k", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                                 mutation_scale=12, color=color, lw=1.2, linestyle=ls))
# main corrected flow (top row)
steps = [
    (0.01, "RTL\n5 variants\n(B0–B4)"),
    (0.155, "ORFS PnR\nsky130hd\n(+layout perturb.)"),
    (0.31, "In-session:\nOpenRCX extract\n+ read_spef"),
    (0.475, "Gate replay\nzero-delay\n+ SDF glitch"),
    (0.64, "Per-pin activity\ninjection\n(~820 pins)"),
    (0.805, "OpenSTA\nreport_power\n→ pJ/tx"),
]
for x, t in steps:
    box(x, 0.55, 0.135, 0.30, t, "#e8f0e8")
for i in range(len(steps) - 1):
    arrow(steps[i][0] + 0.135, 0.70, steps[i+1][0], 0.70)
# broken path (bottom row)
box(0.31, 0.12, 0.30, 0.26, "BROKEN: RTL-VCD →\nOpenSTA read_vcd\n(53 pins) → propagate", "#f6d5d5")
ax.text(0.46, 0.06, "sign-reversal artifact:\nB3 reported worst (+33%),\ntruly best (−7.4%)",
        ha="center", va="center", fontsize=8, color="#a00")
arrow(0.475, 0.55, 0.52, 0.38, color="#a00", ls="--")
arrow(0.61, 0.38, 0.61, 0.12, color="#a00", ls="--")
ax.text(0.63, 0.25, "✗", fontsize=20, color="#a00")
ax.text(0.5, 0.97, "Measurement pipeline (corrected flow) and the artifact branch (§5)",
        ha="center", fontsize=10, weight="bold")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.tight_layout()
fig.savefig(OUT / "fig0_pipeline.png", dpi=300)
print("fig0 done")

# ---------- fig1 update: overlay glitch points ----------
D = json.loads((BASE / "results_sky130/phase2_full_matrix.json").read_text(encoding="utf-8"))
R1 = json.loads((BASE / "results_sky130/r1_glitch_compare.json").read_text(encoding="utf-8"))
x = [0, 10, 30, 60, 90]
VARIANTS = ["B1", "B2", "B3", "B4"]
COLORS = {"B1": "#1f77b4", "B2": "#ff7f0e", "B3": "#2ca02c", "B4": "#9467bd"}
LABELS = {"B1": "B1 valid-isolation", "B2": "B2 force-to-zero",
          "B3": "B3 input-hold", "B4": "B4 mask-only (control)"}
fig, ax = plt.subplots(figsize=(6.8, 4.4))
for v in VARIANTS:
    means = [D["delta_pct_vs_B0"][lv][v] for lv in ["p00", "p10", "p30", "p60", "p90"]]
    stds = [D["records"][lv][v]["std"] / D["records"][lv]["B0"]["mean"] * 100 for lv in ["p00", "p10", "p30", "p60", "p90"]]
    ax.errorbar(x, means, yerr=stds, marker="o", capsize=3, color=COLORS[v], label=LABELS[v])
    gx, gy = [], []
    for lv, xx in zip(["p00", "p30", "p60", "p90"], [0, 30, 60, 90]):
        b0 = R1["r1_glitch_pj_tx"][lv]["B0"]
        val = R1["r1_glitch_pj_tx"][lv][v]
        gy.append((val - b0) / b0 * 100); gx.append(xx)
    ax.scatter(gx, gy, marker="x", s=55, color=COLORS[v], zorder=5)
ax.scatter([], [], marker="x", s=55, color="k", label="SDF glitch-true (seed101)")
ax.axhline(0, color="k", lw=0.8, ls="--")
ax.set_xlabel("Zero-product probability (%)")
ax.set_ylabel("Total energy vs B0 (%)")
ax.set_title("Net-energy boundary: zero-delay curves with glitch-true confirmation")
ax.legend(fontsize=8, loc="lower left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig1_breakeven.png", dpi=300)
print("fig1 updated")

# ---------- fig4: layout robustness grouped bars ----------
R2 = json.loads((BASE / "results_sky130/r2_layout_compare.json").read_text(encoding="utf-8"))
layouts = ["u38", "u40", "u42"]
import numpy as np
xpos = np.arange(len(VARIANTS))
w = 0.25
fig, ax = plt.subplots(figsize=(6.5, 4.0))
for i, U in enumerate(layouts):
    vals = [(R2[U]["pj"][v] - R2[U]["pj"]["B0"]) / R2[U]["pj"]["B0"] * 100 for v in VARIANTS]
    bars = ax.bar(xpos + (i - 1) * w, vals, w, label=f"layout {U}")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + (0.25 if v >= 0 else -0.55),
                f"{v:+.1f}", ha="center", fontsize=7)
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(xpos); ax.set_xticklabels([LABELS[v].split()[0] for v in VARIANTS])
ax.set_ylabel("Total energy vs B0 (%)  @90% zero")
ax.set_title("Layout robustness: B1 flips sign; B3 never regresses")
ax.legend(fontsize=8)
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(OUT / "fig4_layout.png", dpi=300)
print("fig4 done")