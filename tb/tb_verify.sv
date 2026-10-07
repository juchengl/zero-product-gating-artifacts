`timescale 1ns/1ps
module tb_verify;
    reg clk=0, rst=0, clear=0, valid=0;
    reg signed [7:0] a=0,b=0;
    wire signed [31:0] acc[0:4];
    wire ov[0:4];
    genvar g;
    generate for(g=0;g<5;g=g+1) begin: versions
        mac #(.MODE(g)) dut(.clk(clk),.rst(rst),.clear(clear),.valid(valid),
            .a(a),.b(b),.acc(acc[g]),.out_valid(ov[g]));
    end endgenerate
    reg [2047:0] vector_file;
    integer f,rc,r,c,v,ai,bi,ev,cycle=0,k;
    reg [31:0] expected;
    initial begin
        if (!$value$plusargs("VECTORS=%s",vector_file)) $fatal(1,"VECTORS required");
        f=$fopen(vector_file,"r");
        if (!f) $fatal(1,"cannot open vectors");
        while (!$feof(f)) begin
            rc=$fscanf(f,"%d %d %d %d %d %h %d\n",r,c,v,ai,bi,expected,ev);
            if(rc!=7) $fatal(1,"malformed vector at %0d",cycle);
            clk=0; rst=r; clear=c; valid=v; a=ai; b=bi;
            #5; clk=1; #1;
            for(k=0;k<5;k=k+1) begin
                if(acc[k] !== expected || ov[k] !== ev[0])
                    $fatal(1,"FAIL cycle=%0d B%0d got=%h/%b expected=%h/%b",cycle,k,acc[k],ov[k],expected,ev[0]);
            end
            #4; cycle=cycle+1;
        end
        $fclose(f);
        $display("PASS cycles=%0d versions=5",cycle);
        $finish;
    end
endmodule
