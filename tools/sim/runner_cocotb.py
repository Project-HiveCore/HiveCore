import os
import sys
import shlex
import shutil
import importlib.util
from pathlib import Path

import pytest
from cocotb_tools.runner import get_runner


def _get_sim_dir() -> Path:
    """Resolve SIM_DIR from the environment."""
    sim_dir = os.getenv("SIM_DIR", "").strip()
    if not sim_dir:
        raise ValueError("SIM_DIR environment variable is not set. Ensure Makefile sets it correctly.")
    return Path(sim_dir).resolve()


def _get_top_level() -> str:
    """Resolve TOP_LEVEL from the environment."""
    top_level = os.getenv("TOP_LEVEL", "").strip()
    if not top_level:
        raise ValueError("TOP_LEVEL environment variable is not set. Ensure Makefile sets it correctly.")
    return top_level


def _load_sim_config(sim_dir: Path, top_level: str):
    """Load cfg_<top_level>.py from the sim directory."""
    config_name = f"cfg_{top_level}.py"
    config_path = sim_dir / config_name
    if not config_path.exists():
        raise FileNotFoundError(f"Missing {config_name} in {sim_dir}.")
    spec = importlib.util.spec_from_file_location(config_name.removesuffix(".py"), str(config_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load the sim config and set up paths before running tests
SIM_DIR = _get_sim_dir()
TOP_LEVEL = _get_top_level()
CFG = _load_sim_config(SIM_DIR, TOP_LEVEL)
MODULE_DIR = SIM_DIR.parent
SRC_DIR = MODULE_DIR / "src"


if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


_PARAM_REQUIRED = getattr(CFG, "PARAM_REQUIRED", False)
_NO_PARAM_SET = [{"name": "default", "parameters": {}}]
_PARAM_SETS = CFG.PARAM_SETS if _PARAM_REQUIRED else _NO_PARAM_SET


def _selected_param_sets():
    # When params are not required, always run the single default set
    if not _PARAM_REQUIRED:
        return _NO_PARAM_SET

    selector = os.getenv("PARAM_SET", "").strip()

    if selector.lower() == "list":
        names = ", ".join(p["name"] for p in _PARAM_SETS)
        pytest.skip(f"Available PARAM_SET values: {names}")

    if not selector:
        return _PARAM_SETS

    chosen = [p for p in _PARAM_SETS if p["name"] == selector]
    if not chosen:
        names = ", ".join(p["name"] for p in _PARAM_SETS)
        raise ValueError(f"Unknown PARAM_SET='{selector}'. Valid values: {names}")
    return chosen


def _sim_build_args():
    """Return build args from config, with optional env-var override."""
    env_args = os.getenv("SIM_BUILD_ARGS", "").strip()
    if env_args:
        return shlex.split(env_args)
    return getattr(CFG, "SIM_ARGS", [])


def _get_sources():
    return [str(SRC_DIR / src) for src in CFG.SRC_FILES]


def _get_test_module_str():
    test_files = getattr(CFG, "TEST_FILES", [])
    module_names = [Path(tf).stem for tf in test_files]
    return ",".join(module_names)


@pytest.mark.parametrize("cfg", _selected_param_sets(), ids=lambda c: c["name"])
def test_module(cfg):
    # Get config values and paths
    param_required = getattr(CFG, "PARAM_REQUIRED", False)
    build_dir = SIM_DIR / "sim_build" / cfg["name"]
    top_level = TOP_LEVEL
    build_srcs = _get_sources()
    sim_build_args = _sim_build_args()
    testcase = os.getenv("TESTCASE", "").strip() or None

    # Init the sim runner
    runner = get_runner("questa")

    # Build the module
    runner.build(
        sources=build_srcs,
        hdl_toplevel=top_level,
        parameters=cfg["parameters"] if param_required else {},
        build_dir=str(build_dir),
        build_args=sim_build_args,
        timescale=("1ns", "1ps"),
        always=True,
    )

    SIM_TOOLS_PATH = Path(__file__).resolve().parent
    waves_do_path = SIM_TOOLS_PATH / "waves.do"

    try:
        # Sim the module
        runner.test(
            hdl_toplevel=top_level,
            test_module=_get_test_module_str(),
            test_args=[
                "-voptargs=+acc",
                "-do", str(waves_do_path),
            ],
            testcase=testcase,
        )
    finally:
        # Move waveforms to a common location
        src_wlf = build_dir / "vsim.wlf"
        if src_wlf.exists():
            waves_dir = SIM_DIR / "sim_build" / "waves"
            waves_dir.mkdir(parents=True, exist_ok=True)

            suffix = f"_{testcase}" if testcase else ""
            dst_wlf = waves_dir / f"{cfg['name']}{suffix}.wlf"
            shutil.copy2(src_wlf, dst_wlf)
