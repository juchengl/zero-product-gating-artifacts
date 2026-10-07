"""Generate paper figures from phase2_full_matrix.json + diagnostic data.
Fig1 break-even curves; Fig2 mechanism decomposition @90%; Fig3 artifact comparison.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\paper\fig")
OUT.mkdir(parents=True, exist_ok=True)
D = json.loads(Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\phase2_full_matrix.json").read_text(encoding="utf-8"))

LEVELS = ["p00", "p10", "p30", "p60", "p90"]
x = [0, 10, 30, 60, 90]
VARIANTS = ["B1", "B2", "B3", "B4"]
COLORS = {"B1": "#1f77b4", "B2": "#ff7f0e", "B3": "#2ca02c", "B4": "#9467bd"}
LABELS = {"B1": "B1 valid-isolation", "B2": "B2 force-to-zero",
          "B3": "B3 input-hold", "B4": "B4 mask-only (control)"}

# Fig 1: break-even curves
fig, ax = plt.subplots(figsize=(6.5, 4.2))
for v in VARIANTS:
    means = [D["delta_pct_vs_B0"][lv][v] for lv in LEVELS]
    stds = [D["records"][lv][v]["std"] / D["records"][lv]["B0"]["mean"] * 100 for lv in LEVELS]
    ax.errorbar(x, means, yerr=stds, marker="o", capsize=3, color=COLORS[v], label=LABELS[v])
ax.axhline(0, color="k", lw=0.8, ls="--")
ax.set_xlabel("Zero-product probability (%)")
ax.set_ylabel("Total energy vs B0 (%)")
ax.set_title("Net-energy boundary: isolation benefit vs sparsity")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig1_breakeven.png", dpi=300)
print("fig1 done")

# Fig 2: mechanism decomposition at 90%
d90 = D["delta_pct_vs_B0"]["p90"]
b1, b2, b3, b4 = d90["B1"], d90["B2"], d90["B3"], d90["B4"]
comps = {
    "valid-isolation\nbaseline (B1@0%)": D["delta_pct_vs_B0"]["p00"]["B1"],
    "zero-gating\nincrement (B3-B1)": b3 - b1,
    "hold vs force\n(B3-B2)": b3 - b2,
    "detection hw\ncost (B4-B1@0%)": (D["delta_pct_vs_B0"]["p00"]["B4"] - D["delta_pct_vs_B0"]["p00"]["B1"]),
}
fig, ax = plt.subplots(figsize=(6.5, 4.0))
names = list(comps.keys())
vals = [comps[k] for k in names]
bar_colors = ["#1f77b4", "#2ca02c", "#2ca02c", "#d62728"]
bars = ax.bar(names, vals, color=bar_colors)
ax.axhline(0, color="k", lw=0.8)
for b, v in zip(bars, vals):
    off = 0.12 if v >= 0 else -0.12
    ax.text(b.get_x() + b.get_width()/2, v + off,
            f"{v:+.2f}%", ha="center", va="bottom" if v >= 0 else "top", fontsize=9)
ax.set_ylabel("Energy change vs B0 (%)")
ax.set_title("Mechanism decomposition @90% zero (neg=saving, pos=cost)")
ax.set_ylim(min(vals) - 0.8, max(vals) + 0.8)
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(OUT / "fig2_decomposition.png", dpi=300)
print("fig2 done")

# Fig 3: artifact comparison for B3 @90%
fig, ax = plt.subplots(figsize=(5.5, 4.0))
methods = ["Broken:\nRTL-VCD propagation", "Corrected:\nper-pin injection", "Gate VCD\ntoggle ratio (ref)"]
vals = [33.9, -7.41, -58.0]  # +33% artifact; -7.41% corrected; B3/B1 toggle ratio-100
colors = ["#d62728", "#2ca02c", "#7f7f7f"]
bars = ax.bar(methods, vals, color=colors)
ax.axhline(0, color="k", lw=0.8)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + (1 if v > 0 else -1),
            f"{v:+.1f}%", ha="center", va="bottom" if v > 0 else "top", fontsize=10)
ax.set_ylabel("B3 vs B0, total energy (%)")
ax.set_title("Activity-annotation artifact: sign reversal for hold-style")
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(OUT / "fig3_artifact.png", dpi=300)
print("fig3 done")