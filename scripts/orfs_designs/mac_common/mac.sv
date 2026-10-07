// Exact signed INT8 MAC. MODE is fixed at elaboration, never a runtime input.
// Synchronous reset/clear flush the pending transaction. Arithmetic wraps mod 2^32.
// MODE 4 (B4, added in B2_MAC_Followup) is the control variant for factor
// decomposition: B1's input sampling policy combined with B2/B3's accumulator
// zero mask. It isolates the accumulator-masking effect (B1 vs B4) from the
// input-isolation effect (B4 vs B2/B3). Arithmetic is identical to B1.
module mac #(parameter integer MODE = 0) (
    input wire clk, rst, clear, valid,
    input wire signed [7:0] a, b,
    output reg signed [31:0] acc,
    output reg out_valid
);
    reg signed [7:0] a_q, b_q;
    reg valid_q, zero_q;
    wire is_zero = (a == 8'sd0) || (b == 8'sd0);
    wire signed [15:0] product = a_q * b_q;
    wire signed [31:0] extended_product = {{16{product[15]}}, product};
    always @(posedge clk) begin
        if (rst || clear) begin
            a_q <= 0; b_q <= 0;
            valid_q <= 0; zero_q <= 0;
            acc <= 0; out_valid <= 0;
        end else begin
            // The previous cycle's transaction retires, including valid zero MACs.
            out_valid <= valid_q;
            if (valid_q && !zero_q) acc <= acc + extended_product;
            valid_q <= valid;
            zero_q <= (MODE >= 2) && valid && is_zero;
            if (MODE == 0) begin
                a_q <= a; b_q <= b;
            end else if (MODE == 1) begin
                if (valid) begin a_q <= a; b_q <= b; end
            end else if (MODE == 2) begin
                if (valid && !is_zero) begin a_q <= a; b_q <= b; end
                else begin a_q <= 0; b_q <= 0; end
            end else if (MODE == 3) begin
                if (valid && !is_zero) begin a_q <= a; b_q <= b; end
            end else if (MODE == 4) begin
                if (valid) begin a_q <= a; b_q <= b; end
            end
        end
    end
endmodule

module mac_b0(input wire clk,rst,clear,valid, input wire signed [7:0] a,b,
              output wire signed [31:0] acc, output wire out_valid);
    mac #(.MODE(0)) core(.*);
endmodule
module mac_b1(input wire clk,rst,clear,valid, input wire signed [7:0] a,b,
              output wire signed [31:0] acc, output wire out_valid);
    mac #(.MODE(1)) core(.*);
endmodule
module mac_b2(input wire clk,rst,clear,valid, input wire signed [7:0] a,b,
              output wire signed [31:0] acc, output wire out_valid);
    mac #(.MODE(2)) core(.*);
endmodule
module mac_b3(input wire clk,rst,clear,valid, input wire signed [7:0] a,b,
              output wire signed [31:0] acc, output wire out_valid);
    mac #(.MODE(3)) core(.*);
endmodule
module mac_b4(input wire clk,rst,clear,valid, input wire signed [7:0] a,b,
              output wire signed [31:0] acc, output wire out_valid);
    mac #(.MODE(4)) core(.*);
endmodule
