/********************************************************
* Module Name    : instr_q_mem
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/07/2026
* Description    : Register based memory unit for the
*                  Instruction Queue FIFO with 
*                  parameterizable size
********************************************************/

`ifndef INSTR_Q_MEM
`define INSTR_Q_MEM

module instr_q_mem
    #(
        parameter DEPTH=8,
        parameter DATA_WIDTH=32,
        localparam ADDR_WIDTH = $clog2(DEPTH)
    )
    (
        input                    clk,
        // no reset needed, fifo handles what slots are valid

        // ========= Write Side =========
        input                   wr_en_0,
        input                   wr_en_1,
        
        input  [ADDR_WIDTH-1:0] wr_addr_0,
        input  [ADDR_WIDTH-1:0] wr_addr_1,

        input  [DATA_WIDTH-1:0] wr_data_0,
        input  [DATA_WIDTH-1:0] wr_data_1,

        // ========= Read Side =========
        input  [ADDR_WIDTH-1:0] rd_addr_0,
        input  [ADDR_WIDTH-1:0] rd_addr_1,

        output [DATA_WIDTH-1:0] rd_data_0,
        output [DATA_WIDTH-1:0] rd_data_1
    );

    // ========= Signal Definitions =========
    logic [DEPTH-1:0] [DATA_WIDTH-1:0] mem;         // flop array
    logic [DEPTH-1:0] [DATA_WIDTH-1:0] mem_wr_data; // input lines
    logic [DEPTH-1:0]                  mem_wr_en;   // enable lines

    // Write port specific enable lines
    logic [DEPTH-1:0] mem_wr_en_0;
    logic [DEPTH-1:0] mem_wr_en_1; 
    

    // ========= Logic =========

    // Decode write pointers to enable the flop at each write addr
    always_comb begin : wr_addr_decoder_0
        mem_wr_en_0 = '0;
        mem_wr_en_0[wr_addr_0] = wr_en_0 ? '1 : '0;
    end

    always_comb begin : wr_addr_decoder_1
        mem_wr_en_1 = '0;
        mem_wr_en_1[wr_addr_1] = wr_en_1 ? '1 : '0;
    end

    // Generate fifo memory as flops
    genvar addr;
    generate
        for (addr = 0; addr < DEPTH; addr++) begin : gen_mem
            assign mem_wr_en[addr] = mem_wr_en_0[addr] | mem_wr_en_1[addr];         // New data available when either enable signal set
            assign mem_wr_data[addr] = mem_wr_en_1[addr] ? wr_data_1 : wr_data_0;   // Select the correct data based on enable

            always_ff @(posedge clk) begin
                mem[addr] <= mem_wr_en[addr] ? mem_wr_data[addr] : mem[addr];       // Store new data if enable set, otherwise keep old data
            end
        end
    endgenerate

    // Mux the mem output to get the requested data
    assign rd_data_0 = mem[rd_addr_0];
    assign rd_data_1 = mem[rd_addr_1];

endmodule

`endif