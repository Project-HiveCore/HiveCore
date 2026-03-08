/********************************************************
* Module Name    : tb_instr_q_fifo
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/09/2026
* Description    : Testbench for the instruction queue.
********************************************************/ 

`timescale 1ns/1ns
// `timescale 1ns/100ps

module tb_instr_q_fifo;
    parameter real OFFSET = 0.1;
    parameter      PERIOD = 10;  // 100MHz clock frequency
    parameter real DUTY   = 0.5; 

    logic        clk;
    logic        rstn;

    // ============================================
    // ==          Instr Queue Signals           ==
    // ============================================
    parameter depth = 4;
    parameter data_width = 32;

    // Inputs
    logic                  wr_en_0;
    logic                  wr_en_1;

    logic [data_width-1:0] wr_data_0;
    logic [data_width-1:0] wr_data_1;

    logic                  rd_en_0;
    logic                  rd_en_1;
    
    // Outputs
    logic                  almost_full;
    logic                  full;

    logic [data_width-1:0] rd_data_0;
    logic [data_width-1:0] rd_data_1;

    logic                  almost_empty;
    logic                  empty;
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
    instr_q_fifo #(.DEPTH(depth), .DATA_WIDTH(data_width)) instr_q_fifo  (.*);

    initial begin
        $dumpfile("dump.fst");
        $dumpvars(0, instr_q_fifo);
        
        returnval = $value$plusargs("testname=%s", testname);

        init();
        repeat (2) @(posedge clk);

        case (testname)
            "smoke":                smoke();
            "wr_until_full":        wr_until_full();
            default:                $error("No test case defined.");
        endcase

        $finish();
    end

    `include "./tests_instr_q_fifo.sv"
endmodule