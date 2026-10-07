# Zero-Product Gating Artifacts — from a Single INT8 MAC to an 8×8 Array on sky130hd

Artifacts for the manuscript **"A Cross-Scale Post-Route Power Study of Zero-Product Gating: From a Single INT8 MAC to an 8×8 Array on an Open PDK, with a Sign-Reversal Artifact in the Standard Activity-Annotation Flow"** (Jucheng Liu, under review at *Integration, the VLSI Journal*, manuscript **VLSIJ-D-26-01655**).

All power numbers in the paper are **post-route** values measured on the SkyWater **sky130hd** open PDK with OpenROAD/OpenSTA, using a **per-driver-pin activity-injection flow** that fixes a sign-reversal artifact in the standard RTL-VCD → OpenSTA activity-propagation path (§7 of the paper).

## Repository layout

| Path | Contents |
|---|---|
| `rtl/mac/mac.sv` | Five-variant INT8 MAC, single parameterized module (`MODE` 0–4) |
| `rtl/array/` | 8×8 PE array SoC: `chip_top.sv` (contains `cfg_regs`, `pat_gen`, `mac_pe`), `pe_array.sv`, `runlen_ctrl.sv` |
| `tb/` | `tb_replay.sv` (single-MAC gate replay), `tb_verify.sv` (functional check), `tb_gate_chip.sv` (array gate replay) |
| `stimuli/b2_gate_smoke/` | 48-workload single-MAC stimulus set: `manifest.json` + per-workload operand streams |
| `netlists/` | Post-synthesis (`mac_b*_netlist.v`) and post-route (`mac_b*_pnr.v`) netlists for B0–B4; array post-route netlist `b3_chip_6_final.v` + SDCs; `b3_chip.sdf.gz`; layout `b3_chip_6_final.def.gz`; parasitics `b3_chip_6_final.spef.gz`; cell sim models (`sky130_delayed.v`, `sky130_fd_sc_hd_sim.v`) |
| `scripts/b2/` | Single-MAC measurement: in-session OpenRCX + `read_spef` + `report_power` recipe (`b2_insession_rcx_power.tcl`), SDF generation, per-driver-pin activity injection runner, matrix driver, VCD tooling |
| `scripts/b2_flow_sky130/` | Project-level analysis: activity-TCL builder (`build_activity_tcl.py`), net-energy calculator (`calc_net_energy.py`), figure/table collectors, audits |
| `scripts/g1/` | Array-grid pipeline: `run_g1.sh`, activity builder, `pat_sparsity.py`, `g1_grid_report.py`, `g1_recompute_from_acts.sh` (9-digit recompute), `g1_window_rescale.py`, `sdf_fill_typ.py`, `rebuild_sky130_odb.sh`, `silicon_measurability.py` |
| `scripts/orfs_designs/` | ORFS design configs (`config.mk` + constraints) for `mac_b0`–`mac_b4`, `mac_common`, `b3_chip` |
| `data/b2_odo_matrix/` | Full single-MAC matrix outputs: per workload × variant activity TCLs + power reports, incl. 3-corner sweep (`run_corner_*`) |
| `data/g1/` | Array grid outputs: activity TCLs (`acts_*`), gate-sim logs (`out_*`), power reports (`power_*` 3-digit, `repower_*` 9-digit — the series behind the array table) |
| `data/b2_fix1/` | SPEF annotation coverage + no-VCD power reference for `mac_b0` |
| `data/b2_fig5/` | Glitch-wave figure data (`fig5.csv`, zero-delay and SDF replay VCDs for B3 at p90) |
| `data/RTL_PROVENANCE.txt` | md5 checks: array RTL identical across all milestones; MAC RTL identical between run copy and curated copy |
| `TOOL_VERSIONS.txt` | Exact tool versions used |

## Toolchain

See `TOOL_VERSIONS.txt`. In short: OpenROAD-flow-scripts (ORFS) at commit `8ae3ae3` with its bundled sky130hd platform; OpenROAD `v2.0-17598-ga008522d8`; Yosys `0.69+` (git `20091e4ca`); Icarus Verilog `11.0`; OpenSTA `2.6.0`. The sky130 PDK (Apache-2.0) is not redistributed here — use the ORFS-bundled platform.

## Reproducing

### A. Single-MAC matrix (variant definitions, net-energy, corners, glitch-true replay)

1. **PnR** the five variants with ORFS using `scripts/orfs_designs/mac_b{0..4}`, or take the included post-route netlists directly.
2. **Gate replay**: `iverilog -g2012 tb/tb_replay.sv netlists/mac_bX_pnr.v netlists/sky130_delayed.v` with a stimulus from `stimuli/b2_gate_smoke/` → VCD.
3. **Activity injection**: `scripts/b2_flow_sky130/build_activity_tcl.py` converts the VCD into per-driver-pin `set_power_activity` TCLs (the corrected flow; the uncorrected RTL-VCD propagation reproduces the §7 sign-reversal artifact).
4. **Power**: OpenROAD in-session — `scripts/b2/b2_insession_rcx_power.tcl` is the full recipe (read ODB → in-session OpenRCX extraction → `read_spef` → inject activities → `report_power`). Raw outputs for every workload × variant: `data/b2_odo_matrix/`.

### B. 8×8 array grid (cross-scale confirmation and scale effect)

1. Rebuild the ODB if needed: `scripts/g1/rebuild_sky130_odb.sh` (from `netlists/b3_chip_6_final.def.gz`), or re-run ORFS with `scripts/orfs_designs/b3_chip`.
2. `scripts/g1/run_g1.sh sdf` then `run_g1.sh run`: per-config (mode_cfg × force_en × T × pat_p) gate-level sim → activity TCL → in-session power. `TB_HALF_NS=10` (default) matches the SDC's 20 ns clock; `TB_HALF_NS=5` reproduces the initial 2×-clock profiling run exactly (see comments in `run_g1.sh` and `g1_window_rescale.py`).
3. `g1_recompute_from_acts.sh` regenerates the 9-significant-digit power reports (`repower_*.txt`) from the retained activity files without re-running simulation. `pat_sparsity.py` documents the on-chip pattern quantization: `pat_p/16` → realized zero-word fractions 31.02% / 62.40% / 87.47%.

### Caveats (also stated in the paper)

- The array-grid numbers are **zero-delay gate replay** ("identical flow, zero-delay accounting"). The SDF is provided for timing-annotated runs; if OpenROAD's `write_sdf` emits typ-less `(min::max)` triples, run `sdf_fill_typ.py` first — Icarus otherwise silently fails to bind delays.
- Gate-level VCDs (~620 MB each for the array) are not distributed; the pipeline regenerates and deletes them per config.

## License

Apache-2.0 (see `LICENSE`). The SkyWater sky130 PDK and OpenROAD-flow-scripts are governed by their own licenses.

## Citation

```bibtex
@misc{liu2026zeroproduct_artifacts,
  author       = {Liu, Jucheng},
  title        = {Artifacts for "A Cross-Scale Post-Route Power Study of Zero-Product Gating"},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://github.com/USERNAME/zero-product-gating-artifacts}
}
```

(DOI and URL are finalized when the Zenodo record is minted.)
