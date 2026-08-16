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

.PHONY: test decode

# Run test cases for all decodes in this directory
test: decode

# Run decode test cases
decode:
	SIM_DIR=$(SIM_DIR) TOP_LEVEL=decode PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) pytest -q $(RUNNER)