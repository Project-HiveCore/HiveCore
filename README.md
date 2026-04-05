# HiveCore

A 64-bit RISC-V, out-of-order, superscalar CPU core.

## Extensions

**Planned:** M (Integer Mult/Div), F (Single-Precision FP), A (Atomic), D (Double-Precision FP)

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
