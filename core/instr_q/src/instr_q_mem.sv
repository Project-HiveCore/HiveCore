/********************************************************
* Module Name    : instr_q_mem
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 03/24/2026
* Description    : Register based memory unit for the
*                  Instruction Queue FIFO with
*                  parameterizable numbers of rd/wr
*                  ports and data width
********************************************************/

`ifndef INSTR_Q_MEM
`define INSTR_Q_MEM

module instr_q_mem
    #(
        parameter  int RD_PORTS     = 4,
        parameter  int WR_PORTS     = 4,
        parameter  int DEPTH        = 8,
        parameter  int DATA_WIDTH   = 32,
        localparam int AddrWidth    = $clog2(DEPTH)
    )
    (
        input                   clk,
        // no reset needed, fifo handles what slots are valid

        // ========= Write Side =========
        input                   wr_en  [WR_PORTS],
        input  [AddrWidth-1:0] wr_addr[WR_PORTS],
        input  [DATA_WIDTH-1:0] wr_data[WR_PORTS],

        // ========= Read Side =========
        input  [AddrWidth-1:0] rd_addr[RD_PORTS],
        output [DATA_WIDTH-1:0] rd_data[RD_PORTS]
    );

    // ========= Parameter Checks =========
    if (RD_PORTS > DEPTH) $error("Invalid number of read ports. Must be less than depth.");
    if (WR_PORTS > DEPTH) $error("Invalid number of write ports. Must be less than depth.");
    if (!(DEPTH inside {2, 4, 8, 16, 32, 64, 128, 256}))
        $error("Invalid depth parameter. Must be a power of 2 less than or equal to 256.");

    // ========= Signal Definitions =========
    logic [DEPTH-1:0] [DATA_WIDTH-1:0]  mem;         // flop array
    logic [DEPTH-1:0] [DATA_WIDTH-1:0]  mem_wr_data; // input lines
    logic [DEPTH-1:0] [WR_PORTS-1:0]    mem_wr_en;   // each addr has one enable bit per write port

    // ========= Write Enable Decoders =========
    always_comb begin
        mem_wr_en = '0;

        for (int wr_port = 0; wr_port < WR_PORTS; wr_port++) begin
            // Set the port's write enable bit for the specified address
            mem_wr_en[wr_addr[wr_port]][wr_port] = wr_en[wr_port];
        end
    end

    // ========= Write Data Select =========
    always_comb begin
        // One-hot mux for selecting data from write ports
        mem_wr_data = '0;
        for (int addr = 0; addr < DEPTH; addr++) begin
            for (int port = 0; port < WR_PORTS; port++) begin
                mem_wr_data[addr] |= wr_data[port] & {DATA_WIDTH{mem_wr_en[addr][port]}};
            end
        end
    end

    // ========= Write MEM Registers =========
    always_ff @(posedge clk) begin
        for (int addr = 0; addr < DEPTH; addr++) begin : gen_mem
            // If any write enable is active for this address, write the selected data; otherwise clock gate
            mem[addr] <= |mem_wr_en[addr] ? mem_wr_data[addr] : mem[addr];
        end
    end

    // ========= Read Mux =========
    genvar rd_port;
    generate
        for (rd_port = 0; rd_port < RD_PORTS; rd_port++) begin : gen_rd_mux
            assign rd_data[rd_port] = mem[rd_addr[rd_port]];
        end : gen_rd_mux
    endgenerate

endmodule

`endif
