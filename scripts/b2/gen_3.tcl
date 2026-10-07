read_db /home/research/orfs-git/flow/results/sky130hd/mac_b3/base/6_final.odb
read_liberty /home/research/orfs-git/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_sdc /home/research/orfs-git/flow/results/sky130hd/mac_b3/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /home/research/orfs-git/flow/platforms/sky130hd/rcx_patterns.rules
write_sdf /home/research/b2_sky130/sdf/mac_b3.sdf
