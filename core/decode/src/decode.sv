/**************************************************************************************************
* Module Name    : decode
* Author         : Jacob Dudik
* Creation Date  : 07/05/2026
* Last edit Date : 07/05/2026
* Description    : 
*                  
*                  
**************************************************************************************************/
import core_pkg::*;

`ifndef DECODE
`define DECODE
module decode
  #(
    // ======= Parameters ========
    parameter FETCH_WIDTH = 4
  )
  (
    // ========= Inputs ==========
    input  logic clk,
    input  logic rst_n,

    input  logic [INSTR_WIDTH-1:0] [FETCH_WIDTH-1:0] instr_i,
    input  logic                   [FETCH_WIDTH-1:0] instr_valid_i,

    // ========= Outputs =========
    output logic                         [FETCH_WIDTH-1:0] instr_valid_o,
    output func_unit_t                   [FETCH_WIDTH-1:0] instr_fu_o,
    output logic [2:0]                   [FETCH_WIDTH-1:0] instr_funct3_o,
    output logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] instr_imm_o

  );

  // ============================================
  // ==            Blank Header                ==
  // ============================================
  

endmodule
`endif