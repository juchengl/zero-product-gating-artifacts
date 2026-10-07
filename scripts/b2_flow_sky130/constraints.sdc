# Common constraints for the five-variant sky130hd mapping check (C3/D1).
# 20 ns period matches the B2 protocol's common feasibility clock; this is a
# synthesis/sign-off constraint, NOT a validated operating frequency.
# Note: input delay on the clock port is 0 and has no effect with ideal clocks.
create_clock -name clk -period 20.0 [get_ports clk]
set_input_delay 0.0 -clock clk [all_inputs]
set_output_delay 0.0 -clock clk [all_outputs]
set_load 0.0 [all_outputs]
