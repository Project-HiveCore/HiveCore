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
│   ├── isa 	# ISA documentation
│   └── spec	# Architecture speficiations
│
├── core
│   ├── <module>
│   │   ├── sim	    # Testbenches and verification scripts
│   │   ├── spec    # Module specifications
│   │   └── src     # Module code
│   │
│   └── pkg    # Top level packages
│
└── tpl	   # Templates
```
