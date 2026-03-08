/***************************************************************
* Module Name    : tb_instr_q_mem
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/07/2026
* Description    : Testbench for the instruction queue's memory.
****************************************************************/ 

`timescale 1ns/1ns
// `timescale 1ns/100ps // uncomment for delayed test signals

module tb_instr_q_mem;
    parameter real OFFSET = 0.1;
    parameter      PERIOD = 10;  // example 100MHz clock frequency
    parameter real DUTY   = 0.5; 

    logic        clk;
    logic        rst;

    // ============================================
    // ==          Instr Queue Signals           ==
    // ============================================

    // Parameters
    parameter  depth = 4;
    parameter  data_width = 32;
    localparam addr_width = $clog2(depth); 

    // Inputs
    logic                  wr_en_0;
    logic                  wr_en_1;
    
    logic [addr_width-1:0] wr_addr_0;
    logic [addr_width-1:0] wr_addr_1;

    logic [data_width-1:0] wr_data_0;
    logic [data_width-1:0] wr_data_1;
    
    logic [addr_width-1:0] rd_addr_0;
    logic [addr_width-1:0] rd_addr_1;
    
    // Outputs
    logic [data_width-1:0] rd_data_0;
    logic [data_width-1:0] rd_data_1;

    // =============================================

    // Test specfic signals
    logic [1000:0] testname;
    integer        returnval;
    string         filename;
    integer        f;

    // Generate the test clock
    initial begin
        #OFFSET;
        forever begin
            clk = 1'b0;
            #(PERIOD - (PERIOD * DUTY)) clk = 1'b1;
            #(PERIOD * DUTY);
        end
    end

    // Instantiate the DUT
    instr_q_mem #(.DEPTH(depth), .DATA_WIDTH(data_width)) instr_q_mem  (.*);

    initial begin
        $dumpfile("dump.fst");
        $dumpvars(0, instr_q_mem);
        
        returnval = $value$plusargs("testname=%s", testname);

        repeat (2) @(posedge clk);

        case (testname)
            "smoke":    smoke();
            default:    $error("No test case defined.");
        endcase

        $finish();
    end

    `include "./tests_instr_q_mem.sv"
endmodule