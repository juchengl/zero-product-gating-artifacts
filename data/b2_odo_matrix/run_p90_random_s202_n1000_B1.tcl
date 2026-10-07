read_liberty /home/research/orfs-git/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_db /home/research/orfs-git/flow/results/sky130hd/mac_b1/base/6_final.odb
read_sdc /home/research/orfs-git/flow/results/sky130hd/mac_b1/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /home/research/orfs-git/flow/platforms/sky130hd/rcx_patterns.rules
source /home/research/b2_sky130/odo/acts_p90_random_s202_n1000_B1.tcl
report_power > /home/research/b2_sky130/odo/p90_random_s202_n1000_B1_power.txt
