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
  import interface_struct_pkg::
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
    input  logic [MEM_ADDR_WIDTH-1:0]    [FETCH_WIDTH-1:0] instr_pc_i,

    // ========= Outputs =========
    output logic                         [FETCH_WIDTH-1:0] instr_valid_o,
    output decode_execute_if_t           [FETCH_WIDTH-1:0] DE_if_o;
  );

  // ============================================
  // ==          Internal Variables            ==
  // ============================================
  // Stage Output Data 
  decode_execute_if_t DE_if_d;

  // Instruction Fields
  logic [6:0]                   [FETCH_WIDTH-1:0] opcode;
  logic [2:0]                   [FETCH_WIDTH-1:0] funct3;
  logic [7:0]                   [FETCH_WIDTH-1:0] funct7;
  logic [4:0]                   [FETCH_WIDTH-1:0] rs1;
  logic [4:0]                   [FETCH_WIDTH-1:0] rs2;
  logic [4:0]                   [FETCH_WIDTH-1:0] rd;
  shift_dir_e                   [FETCH_WIDTH-1:0] shift_dir;

  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] imm_i_type;
  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] imm_s_type;
  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] imm_b_type;
  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] imm_u_type;
  logic [INT_MAX_IMM_WIDTH-1:0] [FETCH_WIDTH-1:0] imm_j_type;


  // ============================================
  // ==       Parse Instruction Fields         ==
  // ============================================
  always_comb begin
    for (int idx = 0; idx < FETCH_WIDTH; idx++) begin
      opcode[idx] = instr_i[idx][6:0];
      funct3[idx] = instr_i[idx][14:12];
      funct7[idx] = instr_i[idx][31:25];
      rs1[idx]    = instr_i[idx][19:15];
      rs2[idx]    = instr_i[idx][24:20];
      rd[idx]     = instr_i[idx][11:7];
      shift_dir   = instr_i[idx][30];
      
      // ============
      //  Immediates
      // ============
      // Sign-extend to 64-bits in EXECUTE
      imm_i_type[idx] = {
                          9'{instr_i[idx][31]},   // imm[19:11]
                          instr_i[idx][30:20]     // imm[10:0]
                        };

      // Sign-extend to 64-bits in EXECUTE
      imm_s_type[idx] = {
                          9'{instr_i[idx][31]},   // imm[19:11]
                          instr_i[idx][30:25],    // imm[10:5]
                          instr_i[idx][11:7]      // imm[4:0]
                        };
      
      // Sign-extend to 64-bits in EXECUTE
      imm_b_type[idx] = { 
                          8'{instr_i[idx][31]},   // imm[19:12]
                          instr_i[idx][7],        // imm[11]
                          instr_i[idx][30:25],    // imm[10:5]
                          instr_i[idx][11:8],     // imm[4:1]
                          1'b0                    // imm[0]
                        };

      // Zero-extend lower bits by 12, then sign-extend to 64-bits in EXECUTE
      imm_u_type[idx] =   instr_i[idx][31:12];    // imm[31:12]
      
      // Sign-extend to 64-bits in EXECUTE
      imm_j_type[idx] = {
                          instr_i[idx][19:12],    // imm[19:12]
                          instr_i[idx][20],       // imm[11]
                          instr_i[idx][30:25],    // imm[10:5]
                          instr_i[idx][24:21],    // imm[4:1]
                          1'b0                    // imm[0]
                        };
    end
  end

  // ==================================================
  // == Generate control signals/imm based on OPCODE ==
  // ==================================================
  always_comb begin
    DE_if_d.funct3 = funct3;
    DE_if_d.fu     = NONE;
    DE_if_d.imm    = '0;
    DE_if_d.is_32b = '0;
    // TODO: need to make more control signals for branch esc instructions and when to use imm/pc

    case (opcode)
      OP: begin
        DE_if_d.fu = ALU;
      end

      OP_32: begin
        DE_if_d.fu     = ALU;
        DE_if_d.is_32b = '1;
      end

      // I-type opcodes
      OP_IMM: begin
        DE_if_d.fu = ALU;

        if ((alu_funct3_e'(funct3) == ALU_SLL) || (alu_funct3_e'(funct3) == ALU_SRL_SRA)) begin
          DE_if_d.imm = {14'b0, imm_i_type[5:0]};
        end else begin
          DE_if_d.imm = imm_i_type;
        end
      end

      OP_IMM_32: begin
        DE_if_d.fu     = ALU;
        DE_if_d.is_32b = '1;

        if ((alu_funct3_e'(funct3) == ALU_SLL) || (alu_funct3_e'(funct3) == ALU_SRL_SRA)) begin
          DE_if_d.imm = {15'b0, imm_i_type[4:0]};
        end else begin
          DE_if_d.imm = imm_i_type;
        end
      end
      
      LOAD: begin
        DE_if_d.fu  = LOAD;
        DE_if_d.imm = imm_i_type;
      end

      STORE: begin
        DE_if_d.fu  = STORE;
        DE_if_d.imm = imm_s_type;
      end

      BRANCH: begin
        DE_if_d.fu  = BRANCH;
        DE_if_d.imm = imm_b_type;
      end

      JAL: begin
        DE_if_d.fu  = BRANCH;
        DE_if_d.imm = imm_j_type;
      end

      JALR: begin
        DE_if_d.fu  = BRANCH;
        DE_if_d.imm = imm_i_type;
      end

      LUI: begin
        // TODO
      end

      AUIPC: begin
        DE_if_d.fu  = BRANCH;
        DE_if_d.imm = imm_u_type;
      end

      SYSTEM: begin
        DE_if_d.fu  = SYS;
        DE_if_d.imm = imm_i_type;
      end

      MISC_MEM: begin
        // TODO
      end
    endcase
  end

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
    // Pass data along when the new instruction is valid, otherwise clock gate
    for (int idx = 0; idx < FETCH_WIDTH; idx++) begin
      DE_if_o[idx] = instr_valid_i[idx] ? DE_if_d[idx] : DE_if_o[idx]; 
    end
  end

endmodule
`endif