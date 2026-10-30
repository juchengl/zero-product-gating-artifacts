# Tool versions (recorded at measurement time)

```
yosys:    Yosys 0.69+ (git sha1 20091e4ca, Release, GNU /usr/bin/c++ 11.4.0) [github.com/The-OpenROAD-Project/yosys at master]
iverilog: Icarus Verilog version 11.0 (stable)
openroad: v2.0-17598-ga008522d8
opensta:  2.6.0
orfs:     8ae3ae362e2e9be94ab1d27b3dd647c8328a783f (OpenROAD-flow-scripts, Fri Dec 13 13:53:07 2024 +0000)
```

- Platform: ORFS-bundled `sky130hd` (SkyWater sky130 open PDK, Apache-2.0). The corner sweep used the
  tt/ff/ss liberty files from the same PDK build (`tt_025C_1v80`, `ff_100C_1v95`, `ss_100C_1v60`).
- Array design `b3_chip` was synthesized on 2026-09-19 (ORFS stage `1_1_yosys`), post-routed the same day;
  the published netlist is `netlists/b3_chip_6_final.v`.
- The simulation cell model `netlists/sky130_delayed.v` is the delayed-glitch replay model used for
  SDF-annotated single-MAC runs; `netlists/sky130_fd_sc_hd_sim.v` is the standard sky130 hd behavioral
  simulation model.
- Environment: Ubuntu 22.04 (WSL2), x86_64.

## Additional toolchain for the §7 per-pin evidence and Table 6

The activity-propagation comparison required two things the stock OpenSTA 2.6.0 release does not
provide, so a patched build was used:

```
opensta:  3.1.0 (built from source, The-OpenROAD-Project/OpenSTA @ master, 2026-10-30)
eigen:    3.4.0-2ubuntu2         (libeigen3-dev)
cudd:     3.0.0  (built from The-OpenROAD-Project/cudd, install prefix $HOME/cudd-install)
flex:     2.6.4  (libfl-dev, for FlexLexer.h)
iverilog: 11.0   (VCD generation, zero-delay; SDF not used for this comparison)
```

Two commands were added to `power/Power.i` + `power/Power.{hh,cc}`:

- `report_activity_dump_cmd <file>` — dumps `pin, net, density, duty, origin` for every leaf pin
  (`origin` is `propagated`, `user`, `clock` or `unknown`).
- `set_power_pin_activity_by_name <pin_path> <density> <duty>` — bypasses `get_pins` pattern
  matching, which cannot address escaped identifiers such as `a_q[0]$_SDFFE_PP0P_`.

Notes that matter for reproduction:

- `setUserActivity` takes **transitions per second**, not per clock cycle; `vcd_truth2.py`
  converts with a factor `1e9 / period_ns`.
- Register pins cannot be reached by name; the script walks `get_cells -hier *SDFFE*`, strips the
  `core.` prefix from `get_full_name`, and sets the pin object through
  `sta::set_power_pin_activity`.
- The stock flow "annotates the register outputs and propagates" arm is reproduced by setting the
  51 register Q pins only (`acts_reg.tcl`); the corrected arm sets every driver pin
  (`acts_inj.tcl`).
