"""fig5: side-by-side waveform (zero-delay vs SDF glitch) for the internal net
with the largest glitch excess, p90 B3."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ZD = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results\replay_gate_gate_smoke\p90_random_s101_n1000_B3.window.vcd")
GL = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\results_sky130\r1_vcd\p90_random_s101_n1000_B3.window.vcd")
OUT = Path(r"C:\Users\Administrator\Desktop\科研\B2_MAC_Followup\paper\fig")

def parse(path):
    id2name, name2id = {}, {}
    scope = []
    events = {}  # id -> list[(t_ns, val)]
    t = 0.0
    in_defs = True
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if in_defs:
            if s.startswith("$scope"):
                scope.append(s.split()[2])
            elif s.startswith("$upscope"):
                scope.pop()
            elif s.startswith("$var"):
                p = s.split()
                if len(scope) == 2 and scope[0] == "tb_replay" and scope[1] == "dut":
                    nm = p[4].lstrip("\\")
                    if p[2] == "1":
                        name2id.setdefault(nm, p[3])
                        id2name[p[3]] = nm
            elif s.startswith("$enddefinitions"):
                in_defs = False
            continue
        if s.startswith("#"):
            t = float(s[1:]) / 1000.0  # ps -> ns
            continue
        if s.startswith("$"):
            continue
        if len(s) >= 2 and s[0] in "01xXzZ":
            vid = s[1:]
            if vid in id2name:
                events.setdefault(vid, []).append((t, s[0]))
        # skip vectors
    return name2id, events

nm_zd, ev_zd = parse(ZD)
nm_gl, ev_gl = parse(GL)
# pick internal scalar net (name like _NNNN_ or netN) with max (glitch - zerodelay) transition count
best, best_id, gain = None, None, -1
for nm, vid in nm_gl.items():
    if not (nm.startswith("_") or nm.startswith("net")):
        continue
    g = len(ev_gl.get(vid, []))
    z = len(ev_zd.get(nm_zd.get(nm, vid), [])) if nm in nm_zd else 0
    if g - z > gain and g > 40:
        gain, best, best_id = g - z, nm, vid
print(f"picked net {best}: glitch {len(ev_gl.get(best_id, []))} vs zd transitions")
# waveform segment: first 4 us of window
T0, T1 = 60.0, 64.0
def steps(events, t0, t1):
    pts_t, pts_v = [t0], [None]
    for tt, v in events:
        if tt < t0: 
            pts_t[0], pts_v[0] = tt, v
            continue
        if tt > t1: break
        pts_t.append(tt); pts_v.append(1 if v == "1" else 0)
    pts_t.append(t1); pts_v.append(pts_v[-1])
    return pts_t, pts_v
w = 0.004  # ns per cycle*2 -> waveform half period 10ns; use 4us? too long. use 2 cycles = 40ns? too dense. Use 200ns window
T1 = T0 + 200.0
fig, axes = plt.subplots(2, 1, figsize=(7.5, 3.6), sharex=True)
for ax, (ev, title, color) in zip(axes, [
        (ev_zd.get(nm_zd.get(best, best), []), "Zero-delay gate simulation", "#1f77b4"),
        (ev_gl.get(best_id, []), "SDF glitch-true (post-route delays)", "#d62728")]):
    tt, vv = steps(ev, T0, T1)
    ax.step(tt, vv, where="post", color=color, lw=1.1)
    ax.set_ylim(-0.15, 1.15); ax.set_yticks([0, 1])
    ax.set_ylabel(title, fontsize=8)
    ax.grid(alpha=0.3)
axes[1].set_xlabel("time (ns)")
axes[0].set_title(f"Net {best} (p90, B3): glitch transitions appear only with post-route delays", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "fig5_glitch_wave.png", dpi=300)
print("fig5 done")