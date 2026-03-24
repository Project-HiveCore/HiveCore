# Pytest-based cocotb flow

SIM ?= questa
PYTEST ?= pytest
RUNNER ?= runner_instr_q_mem.py
WAVES ?= 1

# Optional filters:
#   make test_mem PARAM_SET=d8_r4_w4
#   make test_mem TESTCASE=test_10_randomized_multiport_scoreboard
PARAM_SET ?=
TESTCASE ?=

.PHONY: test test_mem list_params clean wave

test: test_mem

test_mem:
	SIM=$(SIM) PARAM_SET=$(PARAM_SET) TESTCASE=$(TESTCASE) WAVES=$(WAVES) $(PYTEST) -q $(RUNNER)

list_params:
	SIM=$(SIM) PARAM_SET=list WAVES=$(WAVES) $(PYTEST) -q $(RUNNER)

clean:
	rm -rf sim_build .pytest_cache __pycache__
	rm -f results.xml *.ini vsim.wlf transcript

wave:
	@if [ -z "$(PARAM_SET)" ]; then \
		echo "Please set PARAM_SET (example: make wave PARAM_SET=d8_r4_w4)"; \
		exit 1; \
	fi
	vsim -view sim_build/$(PARAM_SET)/vsim.wlf