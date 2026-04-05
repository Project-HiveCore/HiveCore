onerror {resume}
quietly WaveActivateNextPane {} 0
add wave -noupdate /instr_q_fifo/flush
add wave -noupdate /instr_q_fifo/clk
add wave -noupdate /instr_q_fifo/rstn
add wave -noupdate -color Goldenrod /instr_q_fifo/wr_ready
add wave -noupdate -color Goldenrod /instr_q_fifo/rd_ready
add wave -noupdate -color {Blue Violet} /instr_q_fifo/wr_data
add wave -noupdate -color {Blue Violet} /instr_q_fifo/wr_en
add wave -noupdate -color {Blue Violet} /instr_q_fifo/rd_en
add wave -noupdate /instr_q_fifo/wr_error
add wave -noupdate /instr_q_fifo/rd_data
add wave -noupdate /instr_q_fifo/rd_error
add wave -noupdate /instr_q_fifo/wr_ptr
add wave -noupdate /instr_q_fifo/wr_ptr_aug
add wave -noupdate /instr_q_fifo/wr_ptr_addr
add wave -noupdate /instr_q_fifo/rd_ptr
add wave -noupdate /instr_q_fifo/rd_ptr_aug
add wave -noupdate /instr_q_fifo/rd_ptr_addr
add wave -noupdate /instr_q_fifo/wr_ptr_next
add wave -noupdate /instr_q_fifo/rd_ptr_next
add wave -noupdate /instr_q_fifo/mem_gated_wr_en
add wave -noupdate /instr_q_fifo/overflow
add wave -noupdate /instr_q_fifo/underflow
add wave -noupdate /instr_q_fifo/wr_en_mismatch
add wave -noupdate /instr_q_fifo/rd_en_mismatch
add wave -noupdate /instr_q_fifo/wr_err
add wave -noupdate /instr_q_fifo/rd_err
TreeUpdate [SetDefaultTree]
WaveRestoreCursors {{Cursor 1} {645 ns} 0}
quietly wave cursor active 1
configure wave -namecolwidth 150
configure wave -valuecolwidth 100
configure wave -justifyvalue left
configure wave -signalnamewidth 1
configure wave -snapdistance 10
configure wave -datasetprefix 0
configure wave -rowmargin 4
configure wave -childrowmargin 2
configure wave -gridoffset 0
configure wave -gridperiod 1
configure wave -griddelta 40
configure wave -timeline 0
configure wave -timelineunits ns
update
