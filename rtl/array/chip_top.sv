// B3 second paper: chip top = 8x8 PE array + config regs + per-PE pattern
// generators (on-chip zero-run streams for silicon energy experiments) +
// direct-injection mux + accumulator readout mux. Single clock domain.
// Block-level spec: docs/S2.1_阵列架构设计.md §5.
module cfg_regs (
    input  wire clk, rst,
    input  wire [3:0] cfg_addr,
    input  wire [15:0] cfg_wdata,
    input  wire cfg_we,
    output reg  [15:0] r_thresh,
    output reg  [1:0] r_mode_cfg,      // 00 auto, 01 sticky PASS, 10 HOLD, 11 FORCE
    output reg  r_force_en,
    output reg  r_pat_valid_mode,      // 0: zero word = valid1,a=b0  1: zero word = valid0
    output reg  [3:0] r_pat_p,         // P(zero word) ~ pat_p/16
    output reg  r_pat_en,
    output reg  r_inj_en
);
    always @(posedge clk) begin
        if (rst) begin
            r_thresh <= 16'd0;
            r_mode_cfg <= 2'b00;
            r_force_en <= 1'b0;
            r_pat_valid_mode <= 1'b0;
            r_pat_p <= 4'd0;
            r_pat_en <= 1'b0;
            r_inj_en <= 1'b0;
        end else if (cfg_we) begin
            case (cfg_addr)
                4'd0: r_thresh <= cfg_wdata;
                4'd1: begin
                    r_mode_cfg <= cfg_wdata[1:0];
                    r_force_en <= cfg_wdata[2];
                    r_pat_valid_mode <= cfg_wdata[3];
                end
                4'd2: r_pat_p <= cfg_wdata[3:0];
                4'd3: begin
                    r_pat_en <= cfg_wdata[0];
                    r_inj_en <= cfg_wdata[1];
                end
                default: ;
            endcase
        end
    end
endmodule

// Per-PE on-chip stream: 8-bit maximal LFSR data words with memoryless zero
// insertion, P(zero) ~ pat_p/16 (geometric zero-run lengths). Two zero-word
// flavors selected by pat_valid_mode; both count as zero cycles for the
// per-PE run detector. Seed 13*i+11 is nonzero for every PE index i.
module pat_gen (
    input  wire clk, rst,
    input  wire [3:0] pat_p,
    input  wire pat_valid_mode,
    input  wire [7:0] seed,
    output wire       o_valid,
    output wire signed [7:0] o_a, o_b
);
    reg [7:0] lfsr;
    wire fb = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];
    wire [3:0] sample = {lfsr[7], lfsr[5], lfsr[3], lfsr[1]};
    wire make_zero = (sample < pat_p);
    always @(posedge clk) begin
        if (rst) lfsr <= seed;
        else     lfsr <= {lfsr[6:0], fb};
    end
    assign o_valid = pat_valid_mode ? 1'b0 : 1'b1;
    assign o_a = make_zero ? 8'sd0 : lfsr;
    assign o_b = make_zero ? 8'sd0 : {lfsr[3:0], lfsr[7:4]};
endmodule

module chip_top #(parameter integer N = 8, parameter integer TW = 8) (
    input  wire clk, rst, clear,
    input  wire [3:0] cfg_addr,
    input  wire [15:0] cfg_wdata,
    input  wire cfg_we,
    input  wire [6:0] ro_addr,           // 0..63: acc[PE]; 64..127: mode[PE]
    output wire [31:0] ro_data,
    input  wire inj_valid,
    input  wire [7:0] inj_a, inj_b   // unsigned at top level: OpenROAD's
                                     // Verilog reader rejects `signed` (B1 pit);
                                     // interpretation happens in mac_pe
);
    wire [15:0] r_thresh;
    wire [1:0] r_mode_cfg;
    wire r_force_en, r_pat_valid_mode, r_pat_en, r_inj_en;
    wire [3:0] r_pat_p;

    cfg_regs u_cfg (
        .clk(clk), .rst(rst),
        .cfg_addr(cfg_addr), .cfg_wdata(cfg_wdata), .cfg_we(cfg_we),
        .r_thresh(r_thresh), .r_mode_cfg(r_mode_cfg),
        .r_force_en(r_force_en), .r_pat_valid_mode(r_pat_valid_mode),
        .r_pat_p(r_pat_p), .r_pat_en(r_pat_en), .r_inj_en(r_inj_en)
    );

    wire [N*N-1:0] pat_valid;
    wire [N*N*8-1:0] pat_a, pat_b;

    genvar i;
    generate
        for (i = 0; i < N*N; i = i + 1) begin : pats
            localparam [7:0] SEED = (13*i + 11) % 256;
            wire pv;
            wire signed [7:0] pa, pb;
            pat_gen pg (
                .clk(clk), .rst(rst),
                .pat_p(r_pat_p), .pat_valid_mode(r_pat_valid_mode),
                .seed(SEED),
                .o_valid(pv), .o_a(pa), .o_b(pb)
            );
            assign pat_valid[i] = pv;
            assign pat_a[8*i +: 8] = pa;
            assign pat_b[8*i +: 8] = pb;
        end
    endgenerate

    // Stream mux per PE: injection > pattern > idle.
    wire [N*N-1:0] s_valid;
    wire [N*N*8-1:0] s_a, s_b;
    generate
        for (i = 0; i < N*N; i = i + 1) begin : strm
            assign s_valid[i] = r_inj_en ? inj_valid : (r_pat_en ? pat_valid[i] : 1'b0);
            assign s_a[8*i +: 8] = r_inj_en ? inj_a : (r_pat_en ? pat_a[8*i +: 8] : 8'sd0);
            assign s_b[8*i +: 8] = r_inj_en ? inj_b : (r_pat_en ? pat_b[8*i +: 8] : 8'sd0);
        end
    endgenerate

    wire [N*N*32-1:0] acc_flat;
    wire [N*N-1:0] ov_flat;
    wire [2*N*N-1:0] dbg_mode_flat;

    pe_array #(.N(N), .TW(TW)) u_array (
        .clk(clk), .rst(rst), .clear(clear),
        .valid(s_valid), .a_flat(s_a), .b_flat(s_b),
        .mode_cfg(r_mode_cfg), .force_en(r_force_en),
        .thresh(r_thresh[TW-1:0]),
        .acc_flat(acc_flat), .out_valid_flat(ov_flat),
        .dbg_mode_flat(dbg_mode_flat)
    );

    assign ro_data = ro_addr[6] ? {30'b0, dbg_mode_flat[(ro_addr[5:0])*2 +: 2]}
                                : acc_flat[ro_addr[5:0]*32 +: 32];
endmodule
