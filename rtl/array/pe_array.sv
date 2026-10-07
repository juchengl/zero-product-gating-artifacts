// B3 second paper: N x N PE array of first-paper MACs with per-PE adaptive
// input conditioning. PE mode semantics are bit-exact with the first paper:
//   PASS (2'b00) = B0 : sample every cycle, no zero mask
//   HOLD (2'b01) = B3 : sample on valid && !is_zero, else keep old inputs;
//                       zero-masked retirement (valid zero MACs retire, no add)
//   FORCE (2'b10) = B2: sample on valid && !is_zero, else a_q=b_q=0; same mask
// Arithmetic: INT8 x INT8 -> INT32, wraps mod 2^32; sync rst/clear.
// mode_cfg (array-shared): 00 auto (per-PE runlen_ctrl), 01 sticky PASS,
// 10 sticky HOLD, 11 sticky FORCE.
module mac_pe (
    input  wire clk, rst, clear, valid,
    input  wire signed [7:0] a, b,
    input  wire [1:0] mode,
    output reg  signed [31:0] acc,
    output reg  out_valid
);
    reg signed [7:0] a_q, b_q;
    reg valid_q, zero_q;
    wire is_zero = (a == 8'sd0) || (b == 8'sd0);
    wire signed [15:0] product = a_q * b_q;
    wire signed [31:0] extended_product = {{16{product[15]}}, product};
    wire sample_en = (mode == 2'b00) ? 1'b1 : (valid && !is_zero);

    always @(posedge clk) begin
        if (rst) begin
            a_q <= 0; b_q <= 0;
            valid_q <= 0; zero_q <= 0;
            acc <= 0; out_valid <= 0;
        end else begin
            out_valid <= valid_q;
            if (valid_q && !zero_q) acc <= acc + extended_product;
            valid_q <= valid;
            zero_q <= (mode != 2'b00) && valid && is_zero;
            case (mode)
                2'b00: begin a_q <= a; b_q <= b; end                  // PASS (B0)
                2'b01: if (sample_en) begin a_q <= a; b_q <= b; end   // HOLD (B3)
                2'b10: if (sample_en) begin a_q <= a; b_q <= b; end   // FORCE (B2)
                       else    begin a_q <= 0; b_q <= 0; end
                default: if (sample_en) begin a_q <= a; b_q <= b; end // 2'b11 unused: HOLD-like
            endcase
        end
    end
endmodule

module pe_array #(parameter integer N = 8, parameter integer TW = 8) (
    input  wire clk, rst, clear,
    input  wire [N*N-1:0] valid,
    input  wire [N*N*8-1:0] a_flat,      // PE i: a_flat[8*i +: 8]
    input  wire [N*N*8-1:0] b_flat,
    input  wire [1:0] mode_cfg,
    input  wire force_en,
    input  wire [TW-1:0] thresh,
    output wire [N*N*32-1:0] acc_flat,   // PE i: acc_flat[32*i +: 32]
    output wire [N*N-1:0] out_valid_flat,
    output wire [2*N*N-1:0] dbg_mode_flat // PE i effective mode (post-mux), for
                                          // verification and silicon test readout
);
    // FSM mode per PE: 2 bits, PE i at [2*i +: 2]
    wire [2*N*N-1:0] fsm_mode;

    genvar i;
    generate
        for (i = 0; i < N*N; i = i + 1) begin : pes
            wire signed [7:0] a_i  = a_flat[8*i +: 8];
            wire signed [7:0] b_i  = b_flat[8*i +: 8];
            wire is_zero_i = (a_i == 8'sd0) || (b_i == 8'sd0);
            wire [1:0] mode_i = (mode_cfg == 2'b00) ? fsm_mode[2*i +: 2] :
                                (mode_cfg == 2'b01) ? 2'b00 :   // sticky PASS
                                (mode_cfg == 2'b10) ? 2'b01 :   // sticky HOLD
                                                      2'b10;    // sticky FORCE
            runlen_ctrl #(.TW(TW)) ctrl (
                .clk(clk), .rst(rst),
                .valid(valid[i]), .is_zero(is_zero_i),
                .force_en(force_en), .thresh(thresh),
                .mode(fsm_mode[2*i +: 2])
            );
            wire [31:0] acc_i;
            wire ov_i;
            mac_pe pe (
                .clk(clk), .rst(rst), .clear(clear), .valid(valid[i]),
                .a(a_i), .b(b_i), .mode(mode_i),
                .acc(acc_i),
                .out_valid(ov_i)
            );
            assign acc_flat[32*i +: 32] = acc_i;
            assign out_valid_flat[i] = ov_i;
            assign dbg_mode_flat[2*i +: 2] = mode_i;
        end
    endgenerate
endmodule
