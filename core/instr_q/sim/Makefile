# Pytest-based cocotb flow

SIM ?= questa
PYTEST ?= pytest
MEM_RUNNER ?= runner_instr_q_mem.py
FIFO_RUNNER ?= runner_instr_q_fifo.py
SIM_ARGS += "-svinputport=net +acc +cover"

# Optional filters:
#   make test_mem PARAM_SET=d8_r4_w4
#   make test_mem TESTCASE=test_10_randomized_multiport_scoreboard
PARAM_SET ?=
TESTCASE ?=

.PHONY: lint test mem fifo list_params clean wave

lint:
	verible-verilog-lint ../src/*

test: mem fifo

mem:
	SIM=$(SIM) SIM_ARGS=$(SIM_ARGS) PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) $(PYTEST) -q $(MEM_RUNNER)

fifo:
	SIM=$(SIM) SIM_ARGS=$(SIM_ARGS) PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) $(PYTEST) -q $(FIFO_RUNNER)

clean:
	rm -rf sim_build .pytest_cache __pycache__
	rm -f results.xml *.ini vsim.wlf transcript *.log

wave:
	@if [ -z "$(PARAM_SET)" ]; then \
		echo "Please set PARAM_SET (example: make wave PARAM_SET=d8_r4_w4)"; \
		exit 1; \
	fi
	vsim -view sim_build/$(PARAM_SET)/vsim.wlf -do wave.do