# HiveCore

A 64-bit RISC-V, out-of-order, superscalar CPU core.

The goal of this project is to build a CPU which can run the Linux kernel on an FPGA, and eventually be submitted to tiny tapeout.

## Extensions

**Planned:** M (Integer Mult/Div), A (Atomic)

**Future Work:** F (Single-Precision FP),  D (Double-Precision FP)

**In-Progess:** I (Base Integer)

**Implemented:**

## Directories

```
.
├── arch
│   ├── isa 	        # ISA documentation
│   └── spec	        # Architecture specifications
│
├── core
│   ├── <module>        # Module name
│   │   ├── README.md   # Specifications and usage
│   │   ├── sim	        # Testbenches and verification scripts
│   │   └── src         # SV code
│   │
│   └── pkg             # Top level packages and common files
│
└── tools/sim		# Simulation tools and scripts used by all modules
```
