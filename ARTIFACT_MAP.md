# Artifact Map — paper element → artifact

| Paper element | Primary artifact(s) |
|---|---|
| Table 1 — MAC variant definitions | `rtl/mac/mac.sv` (single parameterized module, `MODE` 0–4) |
| Table 2 — single-MAC net energy, 48 workloads | `data/b2_odo_matrix/*_power.txt` (reports) + `*_acts` TCLs; stimulus set `stimuli/b2_gate_smoke/manifest.json` |
| Table 3 — glitch-true (SDF) replay | `data/b2_fig5/` (zero-delay vs SDF VCDs, `fig5.csv`), `scripts/b2/gen_*.tcl`, `netlists/sky130_delayed.v`, `scripts/g1/sdf_fill_typ.py` |
| Table — 3 PDK corners (tt/ff/ss) | `data/b2_odo_matrix/run_corner_*` (30 files), `scripts/b2_flow_sky130/apply_r3.py` |
| Table — layout robustness (3 layouts) | `netlists/mac_b*_pnr.v` per-variant netlists, `scripts/b2/run_pnr_five.sh`, `scripts/b2_flow_sky130/{apply_r4.py,collect_r4.py,compare_r2.py}` |
| Table — 8×8 array grid (cross-scale) | `data/g1/repower_*.txt` (9-digit, the published series); `power_*.txt` = initial 3-digit run; `acts_*.tcl` = injected activities |
| Fig. 1 — measurement pipeline | diagram (no data) |
| Fig. 2 — net-energy breakeven | derived from `data/b2_odo_matrix/` via `scripts/b2_flow_sky130/calc_net_energy.py` |
| Fig. 3 — power decomposition | derived from `data/b2_odo_matrix/` |
| Fig. 4 — sign-reversal artifact (B0/B3 reported vs measured) | `data/b2_fix1/` (in-session RCX + named-SPEF reference) vs RTL-VCD-propagation reports in `data/b2_odo_matrix/` |
| Fig. 5 — glitch-wave (B3 @ p90) | `data/b2_fig5/fig5.csv` + `zero_delay_B3_p90.vcd` / `sdf_B3_p90.vcd` |
| §7 artifact diagnosis | `scripts/b2_flow_sky130/build_activity_tcl.py` (per-driver-pin injection = the fix), `data/b2_fix1/mac_b0_parasitic_coverage.txt` |
| §8 pattern quantization (31.02/62.40/87.47%) | `scripts/g1/pat_sparsity.py` |

## Naming conventions

- Single-MAC workloads: `p{00,10,30,60,90}_{random,even,clustered}_s{seed}_n{length}` — zero-product probability target, operand-stream pattern class, RNG seed, stream length.
- Variants: `B0` pass-through baseline, `B1` valid-isolation, `B2` force-to-zero, `B3` input-hold, `B4` mask-only control.
- Array configs: `{p30,p60,p90}T{T,4,16}_{b0,b3,auto}` — pattern density × run-length threshold × mode (`auto` = run-length adaptive hold/force).
- `run_corner_*`: corner sweep `tt_025C_1v80` / `ff_100C_1v95` / `ss_100C_1v60`, p90 workload, variants B0–B4.
