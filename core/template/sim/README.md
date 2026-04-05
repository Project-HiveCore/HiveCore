# Introduction

The simulation flow is based on the cocotb python framework using Siemens Questa as the simulator. The simulator cocotb uses can be changed to other widely available programs like IcarusVerilog or Verilator, but the flow will require changes to run.

* `Makefile` defines cocotb settings and various run commands
* `runner_<module>.py` defines the SystemVerilog source files, parameter sets (if needed), and passes command line arguments to build and sim
* `tests_<module>.py` defines the module tests that are run for each parameter set

# Requirements

The following software and python modules are required to run the simulation flow:

```
QuestaSim	# SV simulator of choice
cocotb		# main cocotb lib
cocotb-test 	# cocotb unit testing
pytest		# used by cocotb-test
verible 	# (OPTIONAL) run lint on design
```

# Usage

* `make test`
  * Build and sim all modules in the directory with waveforms (more than one submodule may be defined in `Makefile`)
* `make <module> `
  * Build and sim the specified module with waveforms
* `make wave (PARAM_SET=<name>)`
  * Open the sim waveform and run the local wave.do file to restore previous viewing state.
  * `PARAM_SET` is required if the sim passes parameters to the module.
* `make clean`
  * Remove all sim generated files and directories.
* `make lint`
  * Run SystemVerilog linting on the design files in the module's src directory using Verible.
