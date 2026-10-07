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
