"""Stake Engine Math SDK production generation entrypoint for Sewer Surge.

Run from the pinned SDK repository root:
  python games/0_0_sewersurge/run.py --sims 100000 --threads 10 --batch-size 25000 --compress --clean --optimize --verify
"""
import argparse
import os
import shutil

from game_config import GameConfig
from gamestate import GameState
from game_optimization import OptimizationSetup
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs


def clean_generated_outputs(config):
    """Delete previous generated outputs, including stale _0 lookup tables."""
    for folder in ("books", "lookup_tables", "forces", "configs", "publish_files", "optimization_files", "temp_multi_threaded_files"):
        path = os.path.join(config.library_path, folder)
        if os.path.isdir(path):
            shutil.rmtree(path)
    stale_stats = os.path.join(config.library_path, "stats_summary.json")
    if os.path.isfile(stale_stats):
        os.remove(stale_stats)


def main():
    parser = argparse.ArgumentParser(description="Sewer Surge official Math SDK pipeline")
    parser.add_argument("--sims", type=int, default=100000, help="simulations per bet mode")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--rust-threads", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=25000)
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--no-compress", action="store_true")
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--clean", action="store_true", help="remove previous SDK output before this run")
    args = parser.parse_args()
    if args.verify and not args.optimize:
        parser.error("--verify requires --optimize in a fresh run; debug smoke runs should omit --verify")
    if min(args.sims, args.threads, args.rust_threads, args.batch_size) < 1:
        parser.error("sims, threads, rust-threads and batch-size must be positive")

    config = GameConfig()
    if args.clean:
        clean_generated_outputs(config)
    OptimizationSetup(config)
    compression = args.compress and not args.no_compress

    # Fresh per-mode GameState is required for SDK 0.0.0 payout sidecars:
    # `_payout_ints` is initialised in __init__, but not cleared by run_sims().
    # Reusing one state silently accumulates old modes' payouts and breaks RGS hashes.
    for mode in config.bet_modes:
        mode_state = GameState(config)
        create_books(
            mode_state, config, {mode.get_name(): args.sims},
            args.batch_size, args.threads, compression, profiling=False,
        )

    gamestate = GameState(config)
    generate_configs(gamestate)
    target_modes = [mode.get_name() for mode in config.bet_modes]
    if args.optimize:
        from optimization_program.run_script import OptimizationExecution
        OptimizationExecution().run_all_modes(config, target_modes, args.rust_threads)
        generate_configs(gamestate)
    if args.verify:
        from utils.rgs_verification import execute_all_tests
        execute_all_tests(config)


if __name__ == "__main__":
    main()
