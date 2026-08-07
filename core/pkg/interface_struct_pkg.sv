`ifndef INTERFACE_STRUCT_PKG
`define INTERFACE_STRUCT_PKG
package interface_struct_pkg;

typedef struct packed {
  logic [MEM_ADDR_WIDTH-1:0]    pc;
  func_unit_e                   fu;
  logic [2:0]                   funct3;
  logic [4:0]                   rs1_addr;
  logic [31:0]                  rs1_data;
  logic [4:0]                   rs2_addr;
  logic [31:0]                  rs2_data;
  logic [INT_MAX_IMM_WIDTH-1:0] imm;
  logic                         is_32b;
} decode_execute_if_t;

endpackage
`endif