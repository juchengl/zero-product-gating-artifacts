`timescale 1ns/1ps
`ifndef DUT
`define DUT mac_b0
`endif
module tb_replay;
    reg clk=0,rst=0,clear=0,valid=0;
    reg signed [7:0] a=0,b=0;
    wire signed [31:0] acc;
    wire out_valid;
    `DUT dut(.*);
    reg [2047:0] vector_file,vcd_file,sdf_file;
    integer f,rc,r,c,v,ai,bi,ev,cycle=0;
    real period=20.0;
    reg [31:0] expected;
    initial begin
        if ($value$plusargs("PERIOD=%f",period)) begin end
        if (period<=2.0) $fatal(1,"period must exceed 2 ns");
        if ($value$plusargs("SDF=%s",sdf_file)) $sdf_annotate(sdf_file,dut);
        if (!$value$plusargs("VECTORS=%s",vector_file)) $fatal(1,"VECTORS required");
        if ($value$plusargs("VCD=%s",vcd_file)) begin
            $dumpfile(vcd_file); $dumpvars(0,dut);
        end
        f=$fopen(vector_file,"r"); if(!f) $fatal(1,"cannot open vectors");
        while (!$feof(f)) begin
            rc=$fscanf(f,"%d %d %d %d %d %h %d\n",r,c,v,ai,bi,expected,ev);
            if(rc!=7) $fatal(1,"malformed vector");
            clk=0;rst=r;clear=c;valid=v;a=ai;b=bi;
            #(period/2.0);clk=1;#(period/2.0-0.1);
            if(acc !== expected || out_valid !== ev[0]) $fatal(1,"replay mismatch cycle=%0d",cycle);
            #0.1;cycle=cycle+1;
        end
        $fclose(f);$display("PASS replay cycles=%0d",cycle);$finish;
    end
endmodule
