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

.PHONY: test module

# Run test cases for all modules in this directory
test: module

# Run <module> test cases
module:
	SIM_DIR=$(SIM_DIR) TOP_LEVEL=module PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) pytest -q $(RUNNER)