"""Simulation configuration for instr_q_fifo."""

SRC_FILES = [
    "instr_q_mem.sv",
    "instr_q_fifo.sv",
]

PARAM_REQUIRED = True

SIM_ARGS = ["-svinputport=net"]

PARAM_SETS = [
    {
        "name": "d2_r2_w2",
        "parameters": {
            "DEPTH": 2,
            "RD_PORTS": 2,
            "WR_PORTS": 2,
            "DATA_WIDTH": 32,
        },
    },
    {
        "name": "d8_r4_w4",
        "parameters": {
            "DEPTH": 8,
            "RD_PORTS": 4,
            "WR_PORTS": 4,
            "DATA_WIDTH": 32,
        },
    },
    {
        "name": "d16_r4_w4",
        "parameters": {
            "DEPTH": 16,
            "RD_PORTS": 4,
            "WR_PORTS": 4,
            "DATA_WIDTH": 32,
        },
    },
    {
        "name": "d16_r3_w3",
        "parameters": {
            "DEPTH": 16,
            "RD_PORTS": 3,
            "WR_PORTS": 3,
            "DATA_WIDTH": 32,
        },
    },
]

TEST_FILES = [
    "tests_instr_q_fifo",
]
