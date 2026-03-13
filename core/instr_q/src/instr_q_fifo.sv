/********************************************************
* Module Name    : instr_q_fifo
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/09/2026
* Description    : A dual issue, synchronous FIFO for the
*                  Instruction Queue that stores a
*                  parameterizable number of instructions.
********************************************************/ 

`ifndef INSTR_Q_FIFO
`define INSTR_Q_FIFO

module instr_q_fifo
    #(
        parameter DEPTH=8,
        parameter DATA_WIDTH=32, // remove when the instruction struct is created
        localparam ADDR_WIDTH = $clog2(DEPTH)
    )
    (
        input logic                   rstn,
        input logic                   clk,

        // ========= Write Side =========
        input  logic                  wr_en_0,
        input  logic                  wr_en_1,

        input  logic [DATA_WIDTH-1:0] wr_data_0,
        input  logic [DATA_WIDTH-1:0] wr_data_1,

        output logic                  almost_full,
        output logic                  full, 

        // ========= Read Side =========
        input  logic                  rd_en_0,
        input  logic                  rd_en_1,

        output logic [DATA_WIDTH-1:0] rd_data_0,
        output logic [DATA_WIDTH-1:0] rd_data_1,

        output logic                  almost_empty,
        output logic                  empty
    );

    // Verify the input parameter depth
    // if (!(DEPTH inside {2, 4, 8, 16, 32})) $error("Invalid depth parameter. Must be a power of 2 less than or equal to 32."); // iverilog does not support "inside" keyword

    // ============================================
    // ==          Signal Definitions            ==
    // ============================================

    // FSM Pointers (MSB is rollover flag for full/empty, referred to as the augment bit)
    // [1-bit rollover flag][ADDR_WIDTH-bit address]
    logic [ADDR_WIDTH:0] wr_ptr_0;
    logic [ADDR_WIDTH:0] wr_ptr_1;

    logic [ADDR_WIDTH:0] rd_ptr_0;
    logic [ADDR_WIDTH:0] rd_ptr_1;

    // Pull out the augment bits and addresses from the pointers
    // NOTE: These split signals are a necessity due to local sims
    //       since constant selects in always blocks arent supported.
    //       You could remove these and use selects in the logic instead.
    logic  wr_ptr_0_aug;
    assign wr_ptr_0_aug  = wr_ptr_0[ADDR_WIDTH];
    logic  [ADDR_WIDTH-1:0] wr_ptr_0_addr;
    assign wr_ptr_0_addr = wr_ptr_0[ADDR_WIDTH-1:0];

    logic  wr_ptr_1_aug;
    assign wr_ptr_1_aug  = wr_ptr_1[ADDR_WIDTH];
    logic  [ADDR_WIDTH-1:0] wr_ptr_1_addr;
    assign wr_ptr_1_addr = wr_ptr_1[ADDR_WIDTH-1:0];

    logic  rd_ptr_0_aug;
    assign rd_ptr_0_aug  = rd_ptr_0[ADDR_WIDTH];
    logic  [ADDR_WIDTH-1:0] rd_ptr_0_addr;
    assign rd_ptr_0_addr = rd_ptr_0[ADDR_WIDTH-1:0];

    logic  rd_ptr_1_aug;
    assign rd_ptr_1_aug  = rd_ptr_1[ADDR_WIDTH];
    logic  [ADDR_WIDTH-1:0] rd_ptr_1_addr;
    assign rd_ptr_1_addr = rd_ptr_1[ADDR_WIDTH-1:0];

    // Combinational ptr offset signals (offsets are from the rd/wr 0 ptrs)
    logic [ADDR_WIDTH:0] wr_ptr_plus1;
    logic [ADDR_WIDTH:0] wr_ptr_plus2;
    logic [ADDR_WIDTH:0] wr_ptr_plus3;
    assign wr_ptr_plus1 = wr_ptr_0 + 1;
    assign wr_ptr_plus2 = wr_ptr_0 + 2;
    assign wr_ptr_plus3 = wr_ptr_0 + 3;

    logic [ADDR_WIDTH:0] rd_ptr_plus1;
    logic [ADDR_WIDTH:0] rd_ptr_plus2;
    logic [ADDR_WIDTH:0] rd_ptr_plus3;
    assign rd_ptr_plus1 = rd_ptr_0 + 1;
    assign rd_ptr_plus2 = rd_ptr_0 + 2;
    assign rd_ptr_plus3 = rd_ptr_0 + 3;
    
    // Intermeditate Flag Signals
    logic mem_almost_full;  // high when 1 FIFO slot available to write
    logic mem_full;         // high when 0 FIFO slots available to write

    logic mem_almost_empty; // high when 1 FIFO slot availabe to read
    logic mem_empty;        // high when 0 FIFO slots available to read

    // Error Signals
    logic overflow;         // too many writes occuring when full or almost full 
    logic underflow;        // too many reads occuring when empty or almost empty
    logic wr_en_mismatch;   // wr enables set incorrectly (wr_en_0 low, wr_en_1 high)
    logic rd_en_mismatch;   // rd enables set incorrectly (rd_en_0 low, rd_en_1 high)
    logic wr_error;         // either write overflow or mismatch has occured
    logic rd_error;         // either read underflow or mismatch has occured 

    // Guarded Write Enable Signals
    logic mem_wr_en_0;
    logic mem_wr_en_1; 

    // FIFO Memory Instantiation
    instr_q_mem #(.DEPTH(DEPTH), .DATA_WIDTH(DATA_WIDTH)) fifo_mem 
    (
        .clk(clk),
        .wr_en_0(mem_wr_en_0),
        .wr_en_1(mem_wr_en_1),
        .wr_addr_0(wr_ptr_0_addr),
        .wr_addr_1(wr_ptr_1_addr),
        .wr_data_0(wr_data_0),
        .wr_data_1(wr_data_1),
        .rd_addr_0(rd_ptr_0_addr),
        .rd_addr_1(rd_ptr_1_addr),
        .rd_data_0(rd_data_0),
        .rd_data_1(rd_data_1)
    );


    // ====================================
    // ==          Flag Logic            ==
    // ====================================

    // Capacity Logic
    always_comb begin : capacity_logic
        // Full when address is the same but MSB rollover flags not equal
        mem_full         = (wr_ptr_0_aug != rd_ptr_0_aug) && (wr_ptr_0_addr == rd_ptr_0_addr);
        mem_almost_full  = (wr_ptr_1_aug != rd_ptr_0_aug) && (wr_ptr_1_addr == rd_ptr_0_addr);

        // Empty when address and rollover flags equal
        mem_empty        = (wr_ptr_0 == rd_ptr_0);
        mem_almost_empty = (wr_ptr_0 == rd_ptr_1);

        // Assign intermediate flags to outputs
        full             = mem_full;
        almost_full      = mem_almost_full;
        empty            = mem_empty;
        almost_empty     = mem_almost_empty;
    end : capacity_logic

    // Error Logic
    always_comb begin : error_logic
        // determine if user incorrectly set wr and rd enables
        wr_en_mismatch = !wr_en_0 && wr_en_1;
        rd_en_mismatch = !rd_en_0 && rd_en_1;

        // determine if too many reads or writes are occuring
        overflow  = (wr_en_0 && mem_full)  || (wr_en_1 && mem_almost_full);
        underflow = (rd_en_0 && mem_empty) || (rd_en_1 && mem_almost_empty);

        // generate general error flags
        wr_error = wr_en_mismatch || overflow;
        rd_error = rd_en_mismatch || underflow;
    end : error_logic


    // ========================================
    // ==          Write Side FSM            ==
    // ========================================

    // Forward wr_en signals to memory if no errors occured
    assign mem_wr_en_0 = !wr_error && wr_en_0;
    assign mem_wr_en_1 = !wr_error && wr_en_1;

    // Update write pointers 
    always_ff @(posedge clk) begin : wr_ptr_logic
        if (!rstn) begin
            wr_ptr_0 <= 'b0;
            wr_ptr_1 <= 'b1;
        end

        else begin
            // Default: ptrs stay the same if error or no enables set
            wr_ptr_0 <= wr_ptr_0;
            wr_ptr_1 <= wr_ptr_1;

            if (!wr_error) begin
                // Both write ports active
                if (wr_en_1) begin
                    wr_ptr_0 <= wr_ptr_plus2;
                    wr_ptr_1 <= wr_ptr_plus3;  
                end
                     
                // One write port active
                else if (wr_en_0) begin
                    wr_ptr_0 <= wr_ptr_plus1;
                    wr_ptr_1 <= wr_ptr_plus2; 
                end       
            end
        end
    end : wr_ptr_logic


    // =======================================
    // ==          Read Side FSM            ==
    // =======================================

    // Update read pointers
    always_ff @(posedge clk) begin : rd_ptr_logic
        if (!rstn) begin
            rd_ptr_0 <= 'b0;
            rd_ptr_1 <= 'b1;
        end

        else begin
            // Default: ptrs stay the same if error or no enables set
            rd_ptr_0 <= rd_ptr_0;
            rd_ptr_1 <= rd_ptr_1;

            if (!rd_error) begin
                // Both read ports active
                if (rd_en_1) begin
                    rd_ptr_0 <= rd_ptr_plus2;
                    rd_ptr_1 <= rd_ptr_plus3;
                end
                     
                // One read port active
                else if (rd_en_0) begin
                    rd_ptr_0 <= rd_ptr_plus1;
                    rd_ptr_1 <= rd_ptr_plus2; 
                end       
            end
        end
    end : rd_ptr_logic

endmodule

`endif