#!/bin/bash
cat > /tmp/t.v <<'VEOF'
`timescale 1ns/1ps
module m (Y, A, B);
  output Y; input A, B;
  assign Y = A & B;
  specify
    IOPATH (A, Y) = (0.01, 0.01);
    IOPATH (B, Y) = (0.01, 0.01);
  endspecify
endmodule
VEOF
echo "--- test1: (0.01,0.01) ---"
iverilog -g2012 -gspecify -o /tmp/t.vvp /tmp/t.v 2>&1 | head -4; echo "exit=$?"
cat > /tmp/t2.v <<'VEOF'
`timescale 1ns/1ps
module m2 (Y, A, B);
  output Y; input A, B;
  assign Y = A & B;
  specify
    (A => Y) = (0.01, 0.01);
    (B => Y) = (0.01, 0.01);
  endspecify
endmodule
VEOF
echo "--- test2: (A => Y) ---"
iverilog -g2012 -gspecify -o /tmp/t2.vvp /tmp/t2.v 2>&1 | head -4; echo "exit=$?"