import os
import shutil
from pathlib import Path

import pytest
from cocotb_tools.runner import get_runner


THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent / "src"

SOURCES = [
    SRC_DIR / "instr_q_mem.sv",
]

# Run the same test cases with different parameter sets
PARAM_SETS = [
    {
        "name": "d2_r2_w2",
        "parameters": {"DEPTH": 2, "RD_PORTS": 2, "WR_PORTS": 2, "DATA_WIDTH": 32},
    },
    {
        "name": "d4_r2_w2",
        "parameters": {"DEPTH": 4, "RD_PORTS": 2, "WR_PORTS": 2, "DATA_WIDTH": 32},
    },
    {
        "name": "d8_r4_w4",
        "parameters": {"DEPTH": 8, "RD_PORTS": 4, "WR_PORTS": 4, "DATA_WIDTH": 32},
    },
    {
        "name": "d16_r4_w4",
        "parameters": {"DEPTH": 16, "RD_PORTS": 4, "WR_PORTS": 4, "DATA_WIDTH": 32},
    },
]


def _selected_param_sets():
    selector = os.getenv("PARAM_SET", "").strip()

    if selector.lower() == "list":
        names = ", ".join(p["name"] for p in PARAM_SETS)
        pytest.skip(f"Available PARAM_SET values: {names}")

    if not selector:
        return PARAM_SETS

    chosen = [p for p in PARAM_SETS if p["name"] == selector]
    if not chosen:
        names = ", ".join(p["name"] for p in PARAM_SETS)
        raise ValueError(f"Unknown PARAM_SET='{selector}'. Valid values: {names}")
    return chosen


@pytest.mark.parametrize("cfg", _selected_param_sets(), ids=lambda c: c["name"])
def test_instr_q_mem(cfg):
    sim = os.getenv("SIM", "questa")
    testcase = os.getenv("TESTCASE", "").strip() or None
    waves = os.getenv("WAVES", "1") not in {"0", "false", "False"}

    runner = get_runner(sim)

    build_dir = THIS_DIR / "sim_build" / cfg["name"]

    runner.build(
        sources=[str(s) for s in SOURCES],
        hdl_toplevel="instr_q_mem",
        parameters=cfg["parameters"],
        build_dir=str(build_dir),
        timescale=("1ns", "1ps"),
        waves=waves,
        always=True,
    )

    try:
        runner.test(
            hdl_toplevel="instr_q_mem",
            test_module="tests_instr_q_mem",
            testcase=testcase,
            waves=waves,
        )
    finally:
        if waves:
            src_wlf = build_dir / "vsim.wlf"
            if src_wlf.exists():
                waves_dir = THIS_DIR / "sim_build" / "waves"
                waves_dir.mkdir(parents=True, exist_ok=True)

                suffix = f"_{testcase}" if testcase else ""
                dst_wlf = waves_dir / f"{cfg['name']}{suffix}.wlf"
                shutil.copy2(src_wlf, dst_wlf)
