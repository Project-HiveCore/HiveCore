import os
import shlex
import shutil
from pathlib import Path

import pytest
from cocotb_tools.runner import get_runner

# Run the same test cases with different parameter sets if needed
PARAM_SETS = [
    # {
    #     "name": "params_set_name",
    #     "parameters": {},
    # },
]

def _get_param_required():
    param_required = os.getenv("PARAM_REQUIRED", "").strip().lower()
    if param_required in ("1", "true", "yes"):
        return True
    elif param_required in ("0", "false", "no"):
        return False
    else:
        raise ValueError(f"Invalid value for PARAM_REQUIRED: '{param_required}'. Use 'true' or 'false'.")

def _get_sources():
    build_srcs = os.getenv("SRC_FILES", "").strip()
    if not build_srcs:
        raise ValueError(f"Missing Verilog module files (include .sv)")
    
    build_srcs = [f"{SRC_DIR}/{src}" for src in build_srcs]
    return build_srcs

def _get_top_level():
    top_level = os.getenv("TOP_LEVEL", "")
    if not top_level:
        raise ValueError(f"Missing top level module name (exclude .sv)")
    return top_level

def _get_pytest_files(TEST_DIR):
    test_files = os.getenv("TEST_FILES", "").strip()
    if not test_files:
        raise ValueError(f"Missing python test file names (exclude .py).")
    test_files = [f"{TEST_DIR}/{test_file}" for test_file in test_files.split(" ")]
    test_files_cs = ",".join(test_files)
    return test_files_cs

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

# Get user defined build args
def _sim_build_args():
    sim_args = os.getenv("SIM_BUILD_ARGS", "").strip()
    return shlex.split(sim_args) if sim_args else []


@pytest.mark.parametrize("cfg", _selected_param_sets(), ids=lambda c: c["name"])
def test_module(cfg):
    # Get the SIM_DIR of the calling Makefile
    SIM_DIR = os.getenv("SIM_DIR")
    if not SIM_DIR:
        raise ValueError("SIM_DIR environment variable is not set. Ensure Makefile sets it correctly.")
    SIM_DIR = Path(SIM_DIR.strip()).resolve()

    # Common directories
    MODULE_DIR = SIM_DIR.parent
    SRC_DIR = MODULE_DIR / "src"
    build_dir = SIM_DIR / "sim_build" / cfg["name"]
    
    # Sim Settings
    sim = "questa"
    sim_build_args = _sim_build_args()
    testcase = os.getenv("TESTCASE", "").strip() or None
    top_level = _get_top_level()
    build_srcs = _get_sources()
    param_required = _get_param_required()

    runner = get_runner(sim)
    
    # Build the module
    runner.build(
        sources=[str(src) for src in build_srcs],
        hdl_toplevel=top_level,
        parameters=cfg["parameters"] if param_required else {},
        build_dir=str(build_dir),
        build_args=sim_build_args,
        timescale=("1ns", "1ps"),
        always=True,
    )

    SIM_TOOLS_PATH = Path(__file__).resolve().parents[3] / "tools" / "sim"
    waves_do_path = SIM_TOOLS_PATH / "waves.do"

    try:
        # Sim the module
        runner.test(
            hdl_toplevel=top_level,
            test_module=_get_pytest_files,
            test_args=[
                "-voptargs=+acc",           
                "-do", str(waves_do_path) # run a script to create waveforms with all signals exposed
            ],
            testcase=testcase,
        )
    finally:
        if param_required:
            src_wlf = build_dir / "vsim.wlf"
            if src_wlf.exists():
                waves_dir = SIM_DIR / "sim_build" / "waves"
                waves_dir.mkdir(parents=True, exist_ok=True)

                suffix = f"_{testcase}" if testcase else ""
                dst_wlf = waves_dir / f"{cfg['name']}{suffix}.wlf"
                shutil.copy2(src_wlf, dst_wlf)
