`ifndef INTERFACE_STRUCT_PKG
`define INTERFACE_STRUCT_PKG
package interface_struct_pkg;

typedef struct packed {
  logic [MEM_ADDR_WIDTH-1:0]    pc;       // Program Counter
  func_unit_e                   fu;       // Functional Unit
  logic [3:0]                   uOP;      // Micro-OP for FUs
  logic [4:0]                   rs1_addr; // rs1 address
  logic [INT_REG_WIDTH-1:0]     rs1_data; // rs1 data from regfile
  logic [4:0]                   rs2_addr; // rs2 address
  logic [INT_REG_WIDTH-1:0]     rs2_data; // rs2 data from regfile
  logic [INT_MAX_IMM_WIDTH-1:0] imm;      // Selected immediate value
  logic                         is_32b;   // Instruction output is 32-bit
  logic                         en_wb;    // Writeback stage enable
} decode_execute_if_t;

endpackage
`endif