/**************************************************************************************************
* Module Name    : decode
* Author         : Jacob Dudik
* Creation Date  : 07/05/2026
* Last edit Date : 07/05/2026
* Description    : 
*                  
*                  
**************************************************************************************************/


`ifndef DECODE
`define DECODE
module decode
  import core_pkg::*;
  #(
    // ======= Parameters ========
    parameter FETCH_WIDTH = 4
  )
  (
    // ========= Inputs ==========
    input  logic clk,
    input  logic rst_n,

    input  logic flush,

    input  logic                         [FETCH_WIDTH-1:0] instr_valid_i,
    input  logic [INSTR_WIDTH-1:0]       [FETCH_WIDTH-1:0] instr_i,

    // ========= Outputs =========
    output logic                         [FETCH_WIDTH-1:0] instr_valid_o,
    output func_unit_t                   [FETCH_WIDTH-1:0] instr_fu_o,
    output logic [2:0]                   [FETCH_WIDTH-1:0] instr_funct3_o,
    output logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] instr_imm_o

  );

  // ============================================
  // ==          Internal Variables            ==
  // ============================================
  // Stage Output Data 
  func_unit_t                   [FETCH_WIDTH-1:0] instr_fu_d;
  logic [2:0]                   [FETCH_WIDTH-1:0] instr_funct3_d;
  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] instr_imm_d;

  // Instruction Fields
  logic [6:0]                   [FETCH_WIDTH-1:0] opcode;
  logic [2:0]                   [FETCH_WIDTH-1:0] funct3;
  logic [7:0]                   [FETCH_WIDTH-1:0] funct7;
  logic [4:0]                   [FETCH_WIDTH-1:0] rs1;
  logic [4:0]                   [FETCH_WIDTH-1:0] rs2;
  logic [4:0]                   [FETCH_WIDTH-1:0] rd;
  logic [11:0]                  [FETCH_WIDTH-1:0] imm_i_type;
  logic [11:0]                  [FETCH_WIDTH-1:0] imm_s_type;
  logic [12:0]                  [FETCH_WIDTH-1:0] imm_b_type;
  logic [19:0]                  [FETCH_WIDTH-1:0] imm_u_type;
  logic [19:0]                  [FETCH_WIDTH-1:0] imm_j_type;
  

  // ============================================
  // ==         Decoder Comb. Blocks           ==
  // ============================================
  always_comb begin
    for (int idx = 0; idx < FETCH_WIDTH; idx++) begin
      opcode[idx] = instr_i[idx][6:0];
      funct3[idx] = instr_i[idx][14:12];
      funct7[idx] = instr_i[idx][31:25];
      rs1[idx]    = instr_i[idx][19:15];
      rs2[idx]    = instr_i[idx][24:20];
      rd[idx]     = instr_i[idx][11:7];
      
      // Immediates
      imm_i_type[idx] = {
                          21'{instr_i[idx][31]},
                          instr_i[idx][30:20]
                        };
      imm_s_type[idx] = {
                          21'{instr_i[idx][31]},
                          instr_i[idx][30:25],
                          instr_i[idx][11:7]
                        };
      imm_b_type[idx] = {
                          20'{instr_i[idx][31]},  // imm[31:12]
                          instr_i[idx][7],        // imm[11]
                          instr_i[idx][30:25],    // imm[10:5]
                          instr_i[idx][11:8],     // imm[4:1]
                          1'b0                    // imm[0]
                        };
      imm_u_type[idx] = {
                          instr_i[idx][31:12],
                          12'b0
                        };
      imm_j_type[idx] = {                
                          12'{instr_i[idx][31]},  // imm[31:20]
                          instr_i[idx][19:12],    // imm[19:12]
                          instr_i[idx][20],       // imm[11]
                          instr_i[idx][30:25],    // imm[10:5]
                          instr_i[idx][24:21],    // imm[4:1]
                          1'b0                    // imm[0]
                        };
    end
  end

  // TODO: DONT FORGET ABOUT THE IMM SHIFT 5-bit AND NEEDED!!

  // ============================================
  // ==           Register Blocks              ==
  // ============================================
  always_ff @(posedge clk) begin
    if (!rst_n || flush) begin
      instr_valid_o <= '0;
    end else begin
      instr_valid_o <= instr_valid_i;
    end
  end

  always_ff @(posedge clk) begin
    instr_fu_o      <= instr_fu_d;
    instr_funct3_o  <= instr_funct3_d
    instr_imm_o     <= instr_imm_d;
  end

endmodule
`endif