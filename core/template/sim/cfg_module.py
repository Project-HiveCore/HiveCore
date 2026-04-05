"""Simulation configuration for <module>.

Rename this file to cfg_<module>.py and update all fields below.
Add a corresponding make target in the Makefile for each cfg file.
"""

# RTL source files (relative to the module's src/ directory)
SRC_FILES = [
    "module.sv",
]

# Set to True if the design has parameters to sweep
# If False, PARAM_SETS can be left empty.
PARAM_REQUIRED = False

# Extra simulator build arguments
SIM_ARGS = ["-svinputport=net"]

# Required when PARAM_REQUIRED = True
# Each entry is one simulation run
# 'name' is used as the build directory and waveform filename
PARAM_SETS = [
    {
        "name": "param_set_1",
        "parameters": {
            "PARAM_A": 1,
            "PARAM_B": 2,
        },
    },
]

# cocotb test files (relative to this sim/ directory)
TEST_FILES = [
    "tests_module.py",
]

