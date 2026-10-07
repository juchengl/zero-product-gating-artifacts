# Static timing check for one mapped variant (C3/D1).
# Inputs via env: LIB, NETLIST, TOP, SDC
read_liberty $::env(LIB)
read_verilog $::env(NETLIST)
link_design $::env(TOP)
read_sdc $::env(SDC)
puts "=== TIMING-START ==="
report_worst_slack -max
report_worst_slack -min
report_tns
report_checks -path_delay max -group_count 2 -digits 4
puts "=== TIMING-END ==="
