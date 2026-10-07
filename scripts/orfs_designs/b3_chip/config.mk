export DESIGN_NAME = chip_top
export PLATFORM    = sky130hd

export DESIGN_NICKNAME = b3_chip
export VERILOG_FILES = $(DESIGN_HOME)/src/b3_chip/chip_top.sv \
                       $(DESIGN_HOME)/src/b3_chip/pe_array.sv \
                       $(DESIGN_HOME)/src/b3_chip/runlen_ctrl.sv
export SDC_FILE      = $(DESIGN_HOME)/sky130hd/b3_chip/constraint.sdc

export CORE_UTILIZATION = 40
export PLACE_DENSITY    = 0.55
export TNS_END_PERCENT  = 100
export USE_FILL         = 1
