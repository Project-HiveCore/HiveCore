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
parameter INT_MAX_IMM_WIDTH     = 20;   // Max width of an immediate value in an instruction
                                        // - Not all immediate values are this length (ex. I-type imm == 12-bits)

// OPCODES
localparam OP_W = 7;
typedef enum logic [OP_W-1:0] {
  //  I-Extension Opcodes
  OP_LOAD   = 7'b0000011, // I-type (load)
  OP_REGIMM = 7'b0010011, // I-type (register-immediate)
  OP_AUIPC  = 7'b0010111, // U-type (add upper immediate to pc)
  OP_STORE  = 7'b0100011, // S-type
  OP_REG    = 7'b0110011, // R-type
  OP_LUI    = 7'b0110111, // U-type (load upper immediate)
  OP_BRANCH = 7'b1100011, // B-type
  OP_JALR   = 7'b1100111, // I-type (jump and link register)
  OP_JAL    = 7'b1101111, // J-type
  OP_ENV    = 7'b1110011  // I-type (environment call/break)
} opcode_t;

// FUNCTION 3
typedef enum logic [2:0] {
  ALU_ADD_SUB = 3'b000,
  ALU_SLL     = 3'b001,
  ALU_SLT     = 3'b010,
  ALU_SLTU    = 3'b011,
  ALU_XOR     = 3'b100,
  ALU_SRL_SRA = 3'b101,
  ALU_OR      = 3'b110,
  ALU_AND     = 3'b111
} alu_funct3_t;

typedef enum logic [2:0] {
  LSU_LB_SB   = 3'h0,
  LSU_LH_SH   = 3'h1,
  LSU_LW_SW   = 3'h2,
  LSU_LBU     = 3'h4,
  LSU_LHU     = 3'h5
} lsu_funct3_t;

typedef enum logic [2:0] {
  BEQ         = 3'h0,
  BNE         = 3'h1,
  BLT         = 3'h4,
  BGE         = 3'h5,
  BLTU        = 3'h6,
  BGEU        = 3'h7
} branch_funct3_t;

// Functional Unit Identifiers
typedef enum logic [2:0] {
  ALU,
  LSU,
  BRANCH,
  MUL,
  DIV
} func_unit_t;

endpackage
`endif