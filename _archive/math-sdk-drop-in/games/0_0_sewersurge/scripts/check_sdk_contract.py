#!/usr/bin/env python3
"""Check Sewer Surge interfaces and optionally enforce the exact SDK pins."""
from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import subprocess
from pathlib import Path

from game_config import GameConfig
from game_optimization import OptimizationSetup
from gamestate import GameState


def parameter_names(method: object) -> set[str]:
    return set(inspect.signature(method).parameters)


def read_pin_file(game_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    pin_path = game_dir / "SDK_PIN.txt"
    if not pin_path.is_file():
        raise SystemExit(f"Missing SDK pin file: {pin_path}")
    for line in pin_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SystemExit(f"Malformed SDK pin line: {line}")
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def verify_exact_pins(sdk_root: Path, game_dir: Path, pins: dict[str, str]) -> None:
    try:
        source_commit = subprocess.check_output(
            ["git", "-C", str(sdk_root), "rev-parse", "HEAD"], text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Cannot verify SDK source commit; use a clean Git checkout: {exc}") from exc
    if source_commit != pins.get("ENGINEIO_MATH_SDK_COMMIT"):
        raise SystemExit(
            "Math SDK source commit mismatch: "
            f"expected {pins.get('ENGINEIO_MATH_SDK_COMMIT')}, found {source_commit}"
        )

    try:
        distribution = importlib.metadata.distribution("stakeengine")
        direct_url_text = distribution.read_text("direct_url.json")
        direct_url = json.loads(direct_url_text or "{}")
        runtime_commit = direct_url.get("vcs_info", {}).get("commit_id")
    except (importlib.metadata.PackageNotFoundError, json.JSONDecodeError, TypeError) as exc:
        raise SystemExit(f"Cannot verify installed stakeengine VCS pin: {exc}") from exc
    if runtime_commit != pins.get("STAKEENGINE_RUNTIME_COMMIT"):
        raise SystemExit(
            "stakeengine runtime dependency commit mismatch: "
            f"expected {pins.get('STAKEENGINE_RUNTIME_COMMIT')}, found {runtime_commit}"
        )

    print(f"Exact Math SDK source pin verified: {source_commit}")
    print(f"Exact stakeengine runtime pin verified: {runtime_commit}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-exact-pin", action="store_true",
                        help="require exact Git source and stakeengine runtime commits")
    args = parser.parse_args()

    config = GameConfig()
    expected_modes = {"base": 1.0, "ante": 3.0, "bonus": 100.0, "super_bonus": 500.0}
    actual_modes = {mode.get_name(): mode.get_cost() for mode in config.bet_modes}
    if actual_modes != expected_modes:
        raise SystemExit(f"Bet mode mismatch: expected {expected_modes}, received {actual_modes}")

    state = GameState(config)
    if "sim" not in parameter_names(state.run_spin):
        raise SystemExit("GameState.run_spin must accept the SDK sim argument")
    if not callable(state.run_freespin):
        raise SystemExit("GameState.run_freespin must exist for the SDK abstract contract")

    # Exercise the parent's original one-argument seed-reset call.
    state.reset_seed(0)
    if getattr(state, "_round_retry_index", None) != 0:
        raise SystemExit("Sewer Surge retry RNG bookkeeping was not initialized")

    # Uses the official Math SDK input validator; it does not invoke Rust.
    OptimizationSetup(config)

    game_dir = Path(__file__).resolve().parents[1]
    sdk_root = game_dir.parents[1]
    required = (
        "game_config.py", "gamestate.py", "game_events.py", "game_executables.py",
        "game_calculations.py", "game_override.py", "game_optimization.py", "run.py",
    )
    for filename in required:
        if not (game_dir / filename).is_file():
            raise SystemExit(f"Missing SDK game file: {filename}")

    if args.require_exact_pin:
        verify_exact_pins(sdk_root, game_dir, read_pin_file(game_dir))

    print("Sewer Surge SDK contract and optimizer input check passed.")
    print(f"game_id={config.game_id}; provider_name={config.provider_name}; provider_number={config.provider_number}")
    print("modes=base:1x, ante:3x, bonus:100x, super_bonus:500x")
    if not args.require_exact_pin:
        print("Exact Git source/runtime commit check was not requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
