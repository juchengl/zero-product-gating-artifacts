import re, subprocess, sys
from pathlib import Path
LIB = str(Path.home() / "orfs-git/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib")
RES = str(Path.home() / "orfs-git/flow/results/sky130hd")
for v in ("B1", "B3"):
    n = v[1]
    script = (
        f"read_liberty {LIB}; read_verilog $env(HOME)/b2_sky130/mac_b{n}_pnr.v; "
        f"link_design mac_b{n}; read_sdc {RES}/mac_b{n}/base/6_1_fill.sdc; "
        f"read_spef {RES}/mac_b{n}/base/6_final.spef; "
        f"read_power_activities -vcd $env(HOME)/b2_sky130/gate_p90_random_s101_n1000_{v}.rsvcd; "
        "report_power"
    )
    out = subprocess.run(["sta", "-exit"], input=script, capture_output=True,
                         text=True, env={"HOME": str(Path.home())}).stdout
    print(f"== p90 {v} ==")
    for line in out.splitlines():
        if re.match(r"^(Sequential|Combinational|Clock|Total)\s", line):
            print(line)