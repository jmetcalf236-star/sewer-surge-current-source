"""Official SDK optimisation targets for KingWin Sewer Surge.

Every mode targets 96.5% RTP after normalising by its configured bet cost.
Base/Ante bonus and deep-run hit-rate targets are 5x apart.
"""
from optimization_program.optimization_config import (
    ConstructConditions, ConstructParameters, ConstructScaling,
    verify_optimization_input,
)


def _params(test_spins=(50, 100, 200)):
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=4,
        max_m2m=8,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=list(test_spins),
        test_weights=[0.3, 0.4, 0.3],
        score_type="rtp",
    ).return_dict()


def _scaling(items):
    return ConstructScaling(items).return_dict()


class OptimizationSetup:
    def __init__(self, game_config):
        self.game_config = game_config
        common_cap = ConstructConditions(
            rtp=0.001, av_win=10_000, search_conditions=10_000
        ).return_dict()
        zero = ConstructConditions(
            rtp=0.0, av_win=0.0, search_conditions=0
        ).return_dict()

        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": common_cap,
                    "bonus": ConstructConditions(
                        rtp=0.280, hr=35.7,
                        search_conditions={"symbol": "scatter", "sewerTier": "bonus"},
                    ).return_dict(),
                    "deep_run": ConstructConditions(
                        rtp=0.180, hr=100.0,
                        search_conditions={"symbol": "scatter", "sewerTier": "deep-run"},
                    ).return_dict(),
                    "0": zero,
                    "basegame": ConstructConditions(rtp=0.504, hr=2.4).return_dict(),
                },
                "scaling": _scaling([
                    {"criteria": "basegame", "scale_factor": 1.0, "win_range": (0.2, 5.0), "probability": 1.0},
                    {"criteria": "bonus", "scale_factor": 1.0, "win_range": (2.0, 30.0), "probability": 1.0},
                    {"criteria": "deep_run", "scale_factor": 1.0, "win_range": (8.0, 50.0), "probability": 1.0},
                ]),
                "parameters": _params(),
            },
            "ante": {
                "conditions": {
                    "wincap": common_cap,
                    # HR 7.14 is 5x the Base feature frequency (35.7). With 3x
                    # stake, the per-feature mean target is 6.0x base bet.
                    "bonus": ConstructConditions(
                        rtp=0.280, hr=7.14,
                        search_conditions={"symbol": "scatter", "sewerTier": "bonus"},
                    ).return_dict(),
                    # HR 20 is 5x the Base deep-run frequency (100).
                    "deep_run": ConstructConditions(
                        rtp=0.180, hr=20.0,
                        search_conditions={"symbol": "scatter", "sewerTier": "deep-run"},
                    ).return_dict(),
                    "0": zero,
                    "basegame": ConstructConditions(rtp=0.504, hr=2.4).return_dict(),
                },
                "scaling": _scaling([
                    {"criteria": "basegame", "scale_factor": 1.0, "win_range": (0.6, 15.0), "probability": 1.0},
                    {"criteria": "bonus", "scale_factor": 1.0, "win_range": (1.0, 18.0), "probability": 1.0},
                    {"criteria": "deep_run", "scale_factor": 1.0, "win_range": (4.0, 30.0), "probability": 1.0},
                ]),
                "parameters": _params((20, 40, 80)),
            },
            "bonus": {
                "conditions": {
                    "wincap": common_cap,
                    "bonus": ConstructConditions(
                        rtp=0.964, hr="x",
                        search_conditions={"symbol": "scatter", "sewerTier": "bonus"},
                    ).return_dict(),
                },
                "scaling": _scaling([
                    {"criteria": "bonus", "scale_factor": 1.0, "win_range": (0.0, 1000.0), "probability": 1.0},
                ]),
                "parameters": _params((10, 20, 50)),
            },
            "super_bonus": {
                "conditions": {
                    "wincap": common_cap,
                    "deep_run": ConstructConditions(
                        rtp=0.964, hr="x",
                        search_conditions={"symbol": "scatter", "sewerTier": "deep-run"},
                    ).return_dict(),
                },
                "scaling": _scaling([
                    {"criteria": "deep_run", "scale_factor": 1.0, "win_range": (0.0, 3000.0), "probability": 1.0},
                ]),
                "parameters": _params((10, 20, 50)),
            },
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)
