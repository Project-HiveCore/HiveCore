`ifndef CORE_PKG
`define CORE_PKG
package core_pkg;

    //=========================================
    //       RV64I Base ISA Definitions
    //=========================================
    parameter INSTR_WIDTH           = 32;   // Instruction width
    parameter MEM_ADDR_WIDTH        = 64;   // 64-bit address space 

    parameter INT_REGS              = 32;   // Number of integer registers
    parameter INT_REG_ADDR_WIDTH    = 5;    // Register address width
    parameter INT_REG_WIDTH         = 64;   // Register data width (XLEN = 64)

endpackage
`endif