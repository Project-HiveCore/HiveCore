/**************************************************************************************************
* Module Name    : int_regfile
* Author         : Jacob Dudik
* Creation Date  : 08/16/2026
* Last edit Date : 08/16/2026
* Description    : Parameterizable integer register file with configurable read/write
*                  ports and size. Used as the architectural register file for the
*                  in-order core, but parameterizable to >32 registers for use
*                  as the physical register file in the out-of-order core.
**************************************************************************************************/


`ifndef INT_REGFILE
`define INT_REGFILE
module int_regfile
  import core_pkg::*;
  #(
    parameter  RD_PORTS   = 2,
    parameter  WR_PORTS   = 1,
    parameter  NUM_REGS   = 32,

    localparam ADDR_WIDTH = $clog2(NUM_REGS)
  )
  (
    input  logic clk,
    input  logic rst_n,

    // Read Ports
    input  logic [RD_PORTS-1:0] [ADDR_WIDTH-1:0]    rd_addr_i,
    output logic [RD_PORTS-1:0] [INT_REG_WIDTH-1:0] rd_data_i,

    // Write Ports
    input  logic [WR_PORTS-1:0]                     wr_valid_i,
    input  logic [WR_PORTS-1:0] [ADDR_WIDTH-1:0]    wr_addr_i,
    input  logic [WR_PORTS-1:0] [INT_REG_WIDTH-1:0] wr_data_i
  );

  // Register memory and d-pin signals
  logic [INT_REG_WIDTH-1:0] regs   [NUM_REGS];
  logic [INT_REG_WIDTH-1:0] regs_d [NUM_REGS];

  // Maintain the register state at clk
  always_ff @(posedge clk) begin
    regs <= regs_d;
  end

  // Read Logic
  always_comb begin
    // Read the registers regardless of intent
    for (int port = 0; port < RD_PORTS; port++) begin
      rd_data_i[port] = regs[rd_addr_i[port]];
    end
  end

  // Write Logic
  always_comb begin
    // Maintain previous state if not being written to
    regs_d = regs;

    // Write the new data when that write port has valid data
    for (int port = 0; port < WR_PORTS; port++) begin
      if (wr_valid_i[port]) begin
        regs_d[wr_addr_i[port]] = wr_data_i[port];
      end
    end

    // Always assign register 0 to 0x0
    regs_d[0] = '0;
  end
endmodule : int_regfile
`endif