read_db /home/research/orfs-git/flow/results/sky130hd/mac_b0/base/6_final.odb
read_sdc /home/research/orfs-git/flow/results/sky130hd/mac_b0/base/6_1_fill.sdc
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /home/research/orfs-git/flow/platforms/sky130hd/rcx_patterns.rules
write_spef /home/research/b2_sky130/fix1/mac_b0_named.spef
read_spef /home/research/b2_sky130/fix1/mac_b0_named.spef
report_parasitic_annotation -report_unannotated > /home/research/b2_sky130/fix1/mac_b0_parasitic_coverage.txt
report_power > /home/research/b2_sky130/fix1/mac_b0_power_novcd.txt
