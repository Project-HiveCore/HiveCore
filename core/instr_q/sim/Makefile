# ========================
# Pytest-based cocotb flow
# ========================

PROJ_ROOT := ../../..
TOOLS_DIR := $(PROJ_ROOT)/tools/sim
RUNNER    := $(TOOLS_DIR)/runner_cocotb.py
SIM_DIR   := $(shell pwd)

include $(TOOLS_DIR)/sim.mk

# Optional overrides from command line
PARAM_SET ?=
VIEW	  ?= default
TESTCASE  ?=

.PHONY: test fifo mem

# Run test cases for all modules in this directory
test: fifo mem

# Run instr_q_fifo test cases
fifo:
	SIM_DIR=$(SIM_DIR) TOP_LEVEL=instr_q_fifo PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) pytest -q $(RUNNER)

# Run instr_q_mem test cases
mem:
	SIM_DIR=$(SIM_DIR) TOP_LEVEL=instr_q_mem PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) pytest -q $(RUNNER)