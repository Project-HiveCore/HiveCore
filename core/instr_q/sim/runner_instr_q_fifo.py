import os
import shlex
import shutil
from pathlib import Path

import pytest
from cocotb_tools.runner import get_runner


THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent / "src"

SOURCES = [
    SRC_DIR / "instr_q_mem.sv",
    SRC_DIR / "instr_q_fifo.sv",
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
    {
        "name": "d16_r3_w3",
        "parameters": {"DEPTH": 16, "RD_PORTS": 3, "WR_PORTS": 3, "DATA_WIDTH": 32},
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


def _sim_build_args():
    sim_args = os.getenv("SIM_ARGS", "").strip()
    return shlex.split(sim_args) if sim_args else []


@pytest.mark.parametrize("cfg", _selected_param_sets(), ids=lambda c: c["name"])
def test_instr_q_fifo(cfg):
    sim = os.getenv("SIM", "questa")
    sim_build_args = _sim_build_args()
    testcase = os.getenv("TESTCASE", "").strip() or None

    runner = get_runner(sim)

    build_dir = THIS_DIR / "sim_build" / cfg["name"]

    runner.build(
        sources=[str(s) for s in SOURCES],
        hdl_toplevel="instr_q_fifo",
        parameters=cfg["parameters"],
        build_dir=str(build_dir),
        build_args=sim_build_args,
        timescale=("1ns", "1ps"),
        always=True,
    )

    

    PKG_PATH = Path(__file__).resolve().parents[2] / "pkg"
    waves_do_path = PKG_PATH / "waves.do"

    try:
        runner.test(
            hdl_toplevel="instr_q_fifo",
            test_module="tests_instr_q_fifo",
            test_args=[
                "-voptargs=+acc",
                "-do", str(waves_do_path)
            ],
            testcase=testcase,
        )
    finally:
        src_wlf = build_dir / "vsim.wlf"
        if src_wlf.exists():
            waves_dir = THIS_DIR / "sim_build" / "waves"
            waves_dir.mkdir(parents=True, exist_ok=True)

            suffix = f"_{testcase}" if testcase else ""
            dst_wlf = waves_dir / f"{cfg['name']}{suffix}.wlf"
            shutil.copy2(src_wlf, dst_wlf)
