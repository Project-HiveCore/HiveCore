/********************************************************************
* Module Name    : tests_instr_q_mem
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/07/2026
* Description    : Test definitions for the instruction queue memory.
*********************************************************************/ 

// =======================================
//             Book Keeping
// =======================================

// Sets all mem data to 0
task reset();
    begin
        repeat (2) @(posedge clk);
        #OFFSET wr_en_0   = '1;
        #OFFSET wr_en_1   = '0;
        #OFFSET wr_addr_1 = '0;
        #OFFSET wr_data_0 = '0;
        #OFFSET wr_data_1 = '0;
        #OFFSET rd_addr_0 = '0;
        #OFFSET rd_addr_1 = '0;

        // set each elements data to 0
        for (int addr = 0; addr < depth; addr++) begin
            #OFFSET wr_addr_0 = addr;
            @(posedge clk);
        end

        #OFFSET wr_addr_0 = '0;
        repeat (2) @(posedge clk);
    end
endtask

// =======================================
//                Tests
// =======================================

// Empty test that just resets the mem state
task smoke();
    begin
        reset();
    end
endtask

