# Makefile for running cocotb testbenches

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += ../src/instr_q_mem.sv
VERILOG_SOURCES += ../src/instr_q_fifo.sv

# Name of the toplevel module
COCOTB_TOPLEVEL = instr_q_fifo

# Basename of the Python test file(s)
COCOTB_TEST_MODULES = tests_instr_q_fifo

# SIM_ARGS ="-gDEPTH=4 -gDATA_WIDTH=32"

WAVES = 1

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim