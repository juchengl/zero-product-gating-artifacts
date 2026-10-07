#!/bin/bash
for form in "(posedge CLK => (Q : D)) = (0.01, 0.01);" "(CLK => (Q, D)) = (0.01, 0.01);" "(posedge CLK => (Q, D)) = (0.01, 0.01);"; do
cat > /tmp/e.v <<VEOF
\`timescale 1ns/1ps
module e (Q, CLK, D);
  output reg Q; input CLK, D;
  always @(posedge CLK) Q <= D;
  specify
    $form
  endspecify
endmodule
VEOF
echo "FORM: $form"
iverilog -g2012 -gspecify -o /tmp/e.vvp /tmp/e.v 2>&1 | head -2; echo "exit=$?"
done