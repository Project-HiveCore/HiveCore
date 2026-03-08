TESTNAME=default

SRC_DIR=../../../src/instruction_queue/

MEM_SRC_FILES=$(SRC_DIR)instr_q_mem.sv
MEM_SIM_FILES=tb_instr_q_mem.sv

FIFO_SRC_FILES=$(SRC_DIR)instr_q_mem.sv $(SRC_DIR)instr_q_fifo.sv
FIFO_SIM_FILES=tb_instr_q_fifo.sv

sim_mem:
	IVERILOG_DUMPER=fst
	iverilog '-Wall' '-g2012' $(MEM_SRC_FILES) $(MEM_SIM_FILES) && vvp a.out -fst +testname=$(TESTNAME)

sim_fifo:
	IVERILOG_DUMPER=fst
	iverilog '-Wall' '-g2012' $(FIFO_SRC_FILES) $(FIFO_SIM_FILES) && vvp a.out -fst +testname=$(TESTNAME)

wave:
	GDK_BACKEND=x11 gtkwave dump.fst wave_conf.sav

clean:
	rm -rf 		\
		*.out 	\
		*.fst 	

