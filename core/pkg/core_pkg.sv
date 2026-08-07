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

// Shift Direction
typedef enum logic {
  LEFT  = 1'b0,
  RIGHT = 1'b1
} shift_dir_e;

// OPCODES
localparam OP_W = 7;
typedef enum logic [OP_W-1:0] {
  //  I-Extension Opcodes
  OP        = 7'b01_100_11, // R-type (Reg-Reg w/ 64-bit)
  OP_32     = 7'b01_110_11, // R-type (Reg-Reg w/ 32-bit)
  
  OP_IMM    = 7'b00_100_11, // I-type (Reg-Immediate 64-bit)
  OP_IMM_32 = 7'b00_110_11, // I-type (Reg-Immediate 32-bit) 

  LOAD      = 7'b00_000_11, // I-type (load)
  STORE     = 7'b01_000_11, // S-type

  BRANCH    = 7'b11_000_11, // B-type
 
  JAL       = 7'b11_011_11, // J-type
  JALR      = 7'b11_001_11, // I-type (jump and link register)

  LUI       = 7'b01_101_11, // U-type (load upper immediate)
  AUIPC     = 7'b00_101_11, // U-type (add upper immediate to pc)

  SYSTEM    = 7'b11_100_11, // I-type (environment call/break)
  MISC_MEM  = 7'b00_011_11
} opcode_e;

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
} alu_funct3_e;

typedef enum logic [2:0] {
  LSU_LB_SB   = 3'h0,
  LSU_LH_SH   = 3'h1,
  LSU_LW_SW   = 3'h2,
  LSU_LBU     = 3'h4,
  LSU_LHU     = 3'h5
} lsu_funct3_e;

typedef enum logic [2:0] {
  BEQ         = 3'h0,
  BNE         = 3'h1,
  BLT         = 3'h4,
  BGE         = 3'h5,
  BLTU        = 3'h6,
  BGEU        = 3'h7
} branch_funct3_e;

// Functional Unit Identifiers
typedef enum logic [2:0] {
  NONE,
  ALU,
  LOAD,
  STORE,
  BRANCH,
  MUL,
  DIV,
  SYS
} func_unit_e;

endpackage
`endif