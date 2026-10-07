read_db /home/research/orfs-git/flow/results/sky130hd/mac_b2/base/6_final.odb
read_liberty /home/research/b2_sky130/pdk_hd/sky130B/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_100C_1v95.lib
read_sdc /home/research/orfs-git/flow/results/sky130hd/mac_b2/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /home/research/orfs-git/flow/platforms/sky130hd/rcx_patterns.rules
source /home/research/b2_sky130/odo/acts_p90_random_s101_n1000_B2.tcl
report_power -digits 6 > /home/research/b2_sky130/odo/corner_ff_100C_1v95_B2/power.txt
