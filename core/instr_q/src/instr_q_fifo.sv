/************************************************************
* Module Name    : instr_q_fifo
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 03/25/2026
* Description    : A synchronous FIFO for the Instruction
*                  Queue with a parameterizable number of
*                  instructions, read ports, and write ports.
*************************************************************/

`ifndef INSTR_Q_FIFO
`define INSTR_Q_FIFO

module instr_q_fifo
    #(
        parameter  int RD_PORTS     = 4,
        parameter  int WR_PORTS     = 4,
        parameter  int DEPTH        = 8,
        parameter  int DATA_WIDTH   = 32,
        localparam int AddrWidth    = $clog2(DEPTH)
    )
    (
        input  logic                  clk,
        input  logic                  rstn,
        input  logic                  flush,

        // ========= Write Side =========
        output logic                  wr_ready [WR_PORTS],
        input  logic                  wr_en    [WR_PORTS],
        input  logic [DATA_WIDTH-1:0] wr_data  [WR_PORTS],
        output logic                  wr_error,

        // ========= Read Side =========
        output logic                  rd_ready [RD_PORTS],
        input  logic                  rd_en    [RD_PORTS],
        output logic [DATA_WIDTH-1:0] rd_data  [RD_PORTS],
        output logic                  rd_error
    );

    // ========= Parameter Checks =========
    if (RD_PORTS > DEPTH) $error("Invalid number of read ports. Must be less than depth.");
    if (WR_PORTS > DEPTH) $error("Invalid number of write ports. Must be less than depth.");
    if (!(DEPTH inside {2, 4, 8, 16, 32, 64, 128, 256}))
        $error("Invalid depth parameter. Must be a power of 2 less than or equal to 256.");

    // ============================================
    // ==          Signal Definitions            ==
    // ============================================

    // FSM Pointers (MSB is rollover flag for full/empty, referred to as the augment bit)
    // [1-bit rollover flag][ADDR_WIDTH-bit address]
    logic [AddrWidth:0]   wr_ptr      [WR_PORTS];
    logic                 wr_ptr_aug  [WR_PORTS];
    logic [AddrWidth-1:0] wr_ptr_addr [WR_PORTS];

    logic [AddrWidth:0]   rd_ptr      [RD_PORTS];
    logic                 rd_ptr_aug  [RD_PORTS];
    logic [AddrWidth-1:0] rd_ptr_addr [RD_PORTS];

    logic [AddrWidth:0] wr_ptr_next [(2*WR_PORTS)];
    logic [AddrWidth:0] rd_ptr_next [(2*RD_PORTS)];

    // Break pointers into address and augment bits
    generate
        for (genvar i = 0; i < WR_PORTS; i++) begin
            assign wr_ptr_aug[i]  = wr_ptr[i][AddrWidth];
            assign wr_ptr_addr[i] = wr_ptr[i][AddrWidth-1:0];
        end
        for (genvar i = 0; i < RD_PORTS; i++) begin
            assign rd_ptr_aug[i]  = rd_ptr[i][AddrWidth];
            assign rd_ptr_addr[i] = rd_ptr[i][AddrWidth-1:0];
        end
    endgenerate

    // Intermeditate Flag Signals
    logic wr_slots_ready [WR_PORTS]; // valid ports to write
    logic rd_slots_ready [RD_PORTS]; // valid ports to read

    // Guarded Write Enable Signals
    logic mem_gated_wr_en [WR_PORTS];

    // Error Signals
    logic overflow;         // too many writes occuring
    logic underflow;        // too many reads occuring
    logic wr_en_mismatch;   // wr enables set incorrectly (wr_en_0 low, wr_en_1 high)
    logic rd_en_mismatch;   // rd enables set incorrectly (rd_en_0 low, rd_en_1 high)
    logic wr_err;           // either write overflow or mismatch has occured
    logic rd_err;           // either read underflow or mismatch has occured

    // FIFO Memory Instantiation
    instr_q_mem #(
        .RD_PORTS(RD_PORTS),
        .WR_PORTS(WR_PORTS),
        .DEPTH(DEPTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) fifo_mem
    (
        .clk(clk),
        .wr_en(mem_gated_wr_en),
        .wr_addr(wr_ptr_addr),
        .wr_data(wr_data),
        .rd_addr(rd_ptr_addr),
        .rd_data(rd_data)
    );


    // ====================================
    // ==          Flag Logic            ==
    // ====================================

    // Capacity Logic
    always_comb begin : capacity_logic
        // Set write ready signals (opposite of full conditions)
        for (int port = 0; port < WR_PORTS; port++) begin
            wr_slots_ready[port] = !((wr_ptr_aug[port]  != rd_ptr_aug[0]) &&
                                     (wr_ptr_addr[port] == rd_ptr_addr[0]));
        end

        // Set read ready signals (opposite of empty conditions)
        for (int port = 0; port < RD_PORTS; port++) begin
            rd_slots_ready[port] = (wr_ptr[0] != rd_ptr[port]);
        end

        // Assign intermediate flags to outputs
        wr_ready = wr_slots_ready;
        rd_ready = rd_slots_ready;
    end : capacity_logic

    // Error Logic
    always_comb begin : error_logic
        // determine if user incorrectly set wr and rd enables
        for (int port = 1; port < WR_PORTS; port++) begin
            wr_en_mismatch |= (wr_en[port] && !wr_en[port-1]);
        end
        for (int port = 1; port < RD_PORTS; port++) begin
            rd_en_mismatch |= (rd_en[port] && !rd_en[port-1]);
        end

        // determine if too many reads or writes are occuring
        for (int port = 0; port < WR_PORTS; port++) begin
            overflow |= (wr_en[port] && !wr_slots_ready[port]);
        end
        for (int port = 0; port < RD_PORTS; port++) begin
            underflow |= (rd_en[port] && !rd_slots_ready[port]);
        end

        // generate general error flags
        wr_err = wr_en_mismatch || overflow;
        rd_err = rd_en_mismatch || underflow;

        // assign error outputs
        wr_error = wr_err;
        rd_error = rd_err;
    end : error_logic


    // ========================================
    // ==          Write Side FSM            ==
    // ========================================

    // Calculate next pointer values for writes
    always_comb begin : next_wr_ptr_logic
        for (int i = 0; i < WR_PORTS; i++) begin
            wr_ptr_next[i] = wr_ptr[i];
            wr_ptr_next[WR_PORTS + i] = wr_ptr[WR_PORTS - 1] + i;
        end
    end : next_wr_ptr_logic

    // Forward wr_en signals to memory if no errors occured
    always_comb begin : wr_en_gate
        for (int port = 0; port < WR_PORTS; port++) begin
            mem_gated_wr_en[port] = wr_en[port] && !wr_err;
        end
    end : wr_en_gate

    // Update write pointers
    always_ff @(posedge clk) begin : wr_ptr_logic
        if (!rstn || flush) begin
            for (int ptr = 0; ptr < WR_PORTS; ptr++) begin
                wr_ptr[ptr] <= AddrWidth'(ptr);
            end
        end

        else begin
            // Default: ptrs stay the same if error or no enables set
            wr_ptr <= wr_ptr;

            if (!wr_err) begin
                // Shift write pointers based on the most significant enable
                for (int port = (WR_PORTS-1); port >= 0; port--) begin
                    if (wr_en[port]) begin
                        wr_ptr <= wr_ptr_next[(port + 1) +: WR_PORTS];
                        break;
                    end
                end
            end
        end
    end : wr_ptr_logic


    // =======================================
    // ==          Read Side FSM            ==
    // =======================================

     // Calculate next pointer values for reads
    always_comb begin : next_rd_ptr_logic
        for (int i = 0; i < RD_PORTS; i++) begin
            rd_ptr_next[i] = rd_ptr[i];
            rd_ptr_next[RD_PORTS + i] = rd_ptr[RD_PORTS - 1] + i;
        end
    end : next_rd_ptr_logic

    // Update read pointers
    always_ff @(posedge clk) begin : rd_ptr_logic
        if (!rstn || flush) begin
            for (int ptr = 0; ptr < RD_PORTS; ptr++) begin
                rd_ptr[ptr] <= AddrWidth'(ptr);
            end
        end

        else begin
            // Default: ptrs stay the same if error or no enables set
            rd_ptr <= rd_ptr;

            if (!rd_err) begin
                // Shift read pointers based on the most significant enable
                for (int port = (RD_PORTS-1); port >= 0; port--) begin
                    if (rd_en[port]) begin
                        rd_ptr <= rd_ptr_next[(port + 1) +: RD_PORTS];
                        break;
                    end
                end
            end
        end
    end : rd_ptr_logic

endmodule

`endif
