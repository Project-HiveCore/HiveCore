# ========================
# Pytest-based cocotb flow
# ========================

SIM_DIR := $(shell pwd)
RUNNER ?= ../../../tools/sim/runner_cocotb.py # This should not change unless a different test runner is needed

# Required Settings
TEST_FILES ?= tests_module.py
SRC_FILES ?= module_template.sv
TOP_LEVEL ?= module
PARAM_REQUIRED ?= 0

# Optional Settings
SIM_ARGS += "-svinputport=net +acc +cover"
PARAM_SET ?=
TESTCASE ?=

.PHONY: module test wave clean lint

# Run test cases for all modules
test: module

# Run <module>'s test cases
module:
	SIM_DIR=$(SIM_DIR) TEST_FILES=$(TEST_FILES) SRC_FILES=$(SRC_FILES) TOP_LEVEL=$(TOP_LEVEL) PARAM_REQUIRED=$(PARAM_REQUIRED) SIM_ARGS=$(SIM_ARGS) PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) pytest -q $(RUNNER)

# View a generated waveform
# 	- If the module has parameters, require the PARAM_SET name
wave:
	ifeq ($(PARAM), 1)
		@if [ -z "$(PARAM_SET)" ]; then \
			echo "Please set PARAM_SET (example: make wave PARAM_SET=d8_r4_w4)"; \
			exit 1; \
		fi
		vsim -view sim_build/$(PARAM_SET)/vsim.wlf -do wave.do
	else
		vsim -view sim_build/vsim.wlf -do wave.do
	endif

# Remove all sim generated files and directories
clean:
	rm -rf sim_build .pytest_cache __pycache__
	rm -f results.xml *.ini vsim.wlf transcript *.log

# Run lint on all design files in this module's src directory
lint:
	verible-verilog-lint ../src/*