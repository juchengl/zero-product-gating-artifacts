`timescale 1ns/1ps
// B3-S2.3 chip-level testbench: cfg writes + pattern/injection runs + readout.
// Per stimulus cycle: ctl={rst,clear,cfg_we}, cfg addr/wdata, ro_addr, inj bus.
// Captures ro_data post-edge each cycle for the golden comparator.
module tb_replay;
    reg clk = 0;
    reg rst, clear, cfg_we, inj_valid;
    reg [3:0] cfg_addr;
    reg [15:0] cfg_wdata;
    reg [6:0] ro_addr;
    reg signed [7:0] inj_a, inj_b;
    wire [31:0] ro_data;

    chip_top dut (
        .clk(clk), .rst(rst), .clear(clear),
        .cfg_addr(cfg_addr), .cfg_wdata(cfg_wdata), .cfg_we(cfg_we),
        .ro_addr(ro_addr), .ro_data(ro_data),
        .inj_valid(inj_valid), .inj_a(inj_a), .inj_b(inj_b)
    );

    always #5 clk = ~clk;

    integer fd_in, fd_out, r;
    reg [1023:0] stim_path, out_path;
    reg [1023:0] vcd_path;
    integer dump_on, dump_off, cyc;
    reg vcd_en;
    reg [2:0] c;
    reg [3:0] a;
    reg [15:0] w;
    reg [6:0] ra;
    reg [16:0] ij;

    initial begin
        if (!$value$plusargs("STIM=%s", stim_path)) begin
            $display("missing +STIM"); $finish; end
        if (!$value$plusargs("OUT=%s", out_path)) begin
            $display("missing +OUT"); $finish; end
        vcd_en = $value$plusargs("VCD=%s", vcd_path);
        dump_on = -1; dump_off = -1;
        if (vcd_en) begin
            if ($value$plusargs("DUMPON=%d", dump_on)) ;
            if ($value$plusargs("DUMPOFF=%d", dump_off)) ;
            $dumpfile(vcd_path);
            $dumpvars(0, dut);
            $dumpoff;
        end
        begin: sdf_blk
            reg [1023:0] sdf_path;
            if ($value$plusargs("SDF=%s", sdf_path)) $sdf_annotate(sdf_path, dut);
        end
        cyc = 0;
        fd_in = $fopen(stim_path, "r");
        fd_out = $fopen(out_path, "w");
        r = $fscanf(fd_in, "%h %h %h %h %h\n", c, a, w, ra, ij);
        while (r == 5) begin
            rst      = c[0];
            clear    = c[1];
            cfg_we   = c[2];
            cfg_addr = a;
            cfg_wdata = w;
            ro_addr  = ra;
            inj_valid = ij[16];
            inj_a    = ij[15:8];
            inj_b    = ij[7:0];
            @(posedge clk);
            #1;
            if (vcd_en) begin
                cyc = cyc + 1;
                if (cyc == dump_on)  $dumpon;
                if (cyc == dump_off) $dumpoff;
            end
            $fwrite(fd_out, "%h\n", ro_data);
            r = $fscanf(fd_in, "%h %h %h %h %h\n", c, a, w, ra, ij);
        end
        $fclose(fd_in);
        $fclose(fd_out);
        $finish;
    end
endmodule
