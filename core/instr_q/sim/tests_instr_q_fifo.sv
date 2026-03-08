/********************************************************************
* Module Name    : tests_instr_q_fifo
* Author         : Jacob Dudik
* Creation Date  : 09/07/2025
* Last edit Date : 02/09/2026
* Description    : Test definitions for the instruction queue fifo.
*********************************************************************/ 


// =======================================
//             Book Keeping
// =======================================

// Enable reset and set inputs to defaults
task init();
    begin
        #OFFSET rstn      = '0;
        #OFFSET wr_en_0   = '0;
        #OFFSET wr_en_1   = '0;
        #OFFSET wr_data_0 = '0;
        #OFFSET wr_data_1 = '0;
        #OFFSET rd_en_0   = '0;
        #OFFSET rd_en_1   = '0;
    end
endtask

// Bring the DUT in and out of reset
task reset();
    begin
        repeat (2) @(posedge clk);
        init();
        repeat (2) @(posedge clk);
        #OFFSET rstn = '1;
    end
endtask

task end_test();
    begin
        repeat (2) @(posedge clk);
    end
endtask

// =======================================
//                Tests
// =======================================

// Empty test that just resets the FIFO
task smoke();
    begin
        reset();
        end_test();
    end
endtask

// Write to the FIFO using only port one with constant data until full
task wr_until_full();
    begin
        reset();
        wr_data_0 = 'hA;
        
        for (int i = 0; i < depth; i++) begin
            wr_en_0 = !full;
            @(posedge clk);
        end

        wr_en_0 = '0;
        end_test();
    end
endtask
