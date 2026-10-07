// B3 second paper: per-PE zero-run-length adaptive hold/force controller.
// Semantics fixed by docs/S2.1_阵列架构设计.md §4:
//   idle_or_zero = !valid || is_zero   (one "zero cycle" of the PE stream)
//   run_len      = saturated count of consecutive zero cycles
//   switch rule  : force_en && idle_or_zero && (run_len >= thresh), evaluated
//                  on the registered run_len -> FORCE conditioning starts the
//                  cycle after run_len reaches thresh. thresh==0 forces on the
//                  first idle edge; force_en==0 degenerates to static HOLD.
//   run break (valid && !is_zero) always returns to HOLD (one-cycle reload;
//   HOLD samples on valid && !is_zero, so no data is lost).
// The FSM never emits PASS (2'b00); PASS exists only via the sticky config.
module runlen_ctrl #(parameter integer TW = 8) (
    input  wire clk, rst,
    input  wire valid, is_zero,
    input  wire force_en,
    input  wire [TW-1:0] thresh,
    output reg  [1:0] mode            // 2'b01 HOLD, 2'b10 FORCE
);
    localparam [1:0] HOLD  = 2'b01;
    localparam [1:0] FORCE = 2'b10;

    reg [TW-1:0] run_len;
    wire idle_or_zero = !valid || is_zero;
    wire [TW-1:0] run_max = {TW{1'b1}};
    wire sw = force_en && idle_or_zero && (run_len >= thresh);

    always @(posedge clk) begin
        if (rst) begin
            run_len <= {TW{1'b0}};
            mode    <= HOLD;
        end else begin
            if (idle_or_zero)
                run_len <= (run_len == run_max) ? run_max : run_len + 1'b1;
            else
                run_len <= {TW{1'b0}};
            if (idle_or_zero)
                mode <= sw ? FORCE : mode;
            else
                mode <= HOLD;
        end
    end
endmodule
