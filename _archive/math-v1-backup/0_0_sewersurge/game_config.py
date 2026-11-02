"""KingWin Sewer Surge official Stake Engine Math SDK configuration.

Pricing:
  base=1x, ante=3x, normal bonus buy=100x,
  super bonus buy=500x (owner-confirmed).

Ante mode uses the official SDK optimisation approach: its bonus and
deep-run feature hit rates are each targeted at 5x Base's rate. The
3x stake is included in the per-mode RTP targets.
"""
import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    def __init__(self):
        super().__init__()
        self.game_id = "0_0_sewersurge"  # replace leading 0 with KingWin's assigned provider number
        self.game_name = "sewer_surge"
        self.provider_name = "KingWin"
        self.provider_number = 0  # PORTAL VALUE REQUIRED before production submission
        self.working_name = "Sewer Surge"
        self.output_regular_json = False
        self.min_denomination = 0.1
        self.wincap = 10_000.0
        self.win_type = "scatter"
        self.rtp = 0.965
        # SDK versions differ: older versions take game_id; current versions use self.game_id.
        try:
            self.construct_paths(self.game_id)
        except TypeError:
            self.construct_paths()

        self.num_reels = 5
        self.num_rows = [5, 5, 5, 5, 5]
        self.include_padding = False
        self.paytable = {
            (1, "I"): 0.0,
            (1, "L"): 0.0,
            (1, "T"): 0.0,
            (1, "X"): 0.0,
        }
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "multiplier": []}
        self.freespin_triggers = {
            self.basegame_type: {3: 1},
            self.freegame_type: {3: 1},
        }
        self.anticipation_triggers = {
            self.basegame_type: 2,
            self.freegame_type: 2,
        }
        self.reels = {
            "BR0": self.read_reels_csv(os.path.join(self.reels_path, "BR0.csv")),
        }

        # Reusable server-side conditions. payout_weights is a Sewer Surge
        # extension consumed only inside gamestate.py; it is not a client input.
        reel_weights = {self.basegame_type: {"BR0": 1}}
        def condition(payout_weights, *, scatter_triggers=None, force_wincap=False, force_freegame=False):
            result = {
                "reel_weights": reel_weights,
                "force_wincap": force_wincap,
                "force_freegame": force_freegame,
                "payout_weights": payout_weights,
            }
            if scatter_triggers is not None:
                result["scatter_triggers"] = scatter_triggers
            return result

        base_feature = {
            "bonus": condition(
                {2.0: 2, 4.0: 3, 6.0: 5, 8.0: 5, 10.0: 4, 12.0: 3, 20.0: 1, 30.0: 0.2},
                scatter_triggers={3: 1}, force_freegame=True,
            ),
            "deep_run": condition(
                {8.0: 2, 10.0: 3, 12.0: 4, 15.0: 4, 20.0: 3, 25.0: 2, 30.0: 1, 50.0: 0.2},
                scatter_triggers={4: 4, 5: 1}, force_freegame=True,
            ),
        }
        base_distributions = [
            Distribution(
                criteria="wincap", quota=0.001, win_criteria=self.wincap,
                conditions=condition({self.wincap: 1}, scatter_triggers={4: 4, 5: 1}, force_wincap=True, force_freegame=True),
            ),
            Distribution(criteria="bonus", quota=0.10, conditions=base_feature["bonus"]),
            Distribution(criteria="deep_run", quota=0.10, conditions=base_feature["deep_run"]),
            Distribution(
                criteria="0", quota=0.35, win_criteria=0.0,
                conditions=condition({0.0: 1}, force_freegame=False),
            ),
            Distribution(
                criteria="basegame", quota=0.449,
                conditions=condition({0.2: 3, 0.5: 7, 0.8: 9, 1.0: 10, 1.2: 6, 1.5: 4, 2.0: 3, 3.0: 1, 5.0: 0.2}),
            ),
        ]

        # Ante remains the same visual game and reel set. The official optimizer
        # weights ante bonus/deep-run books at 5x the Base hit rate, while cost=3
        # is included in the target payout contribution. This avoids altering the
        # underlying symbol mix just to change feature frequency.
        ante_distributions = [
            Distribution(
                criteria="wincap", quota=0.001, win_criteria=self.wincap,
                conditions=condition({self.wincap: 1}, scatter_triggers={4: 4, 5: 1}, force_wincap=True, force_freegame=True),
            ),
            Distribution(
                criteria="bonus", quota=0.20,
                conditions=condition(
                    {1.0: 2, 2.0: 3, 3.0: 5, 4.0: 5, 6.0: 4, 8.0: 3, 12.0: 1, 18.0: 0.2},
                    scatter_triggers={3: 1}, force_freegame=True,
                ),
            ),
            Distribution(
                criteria="deep_run", quota=0.20,
                conditions=condition(
                    {4.0: 2, 6.0: 3, 8.0: 4, 10.0: 4, 12.0: 3, 16.0: 2, 20.0: 1, 30.0: 0.2},
                    scatter_triggers={4: 4, 5: 1}, force_freegame=True,
                ),
            ),
            Distribution(
                criteria="0", quota=0.299, win_criteria=0.0,
                conditions=condition({0.0: 1}, force_freegame=False),
            ),
            Distribution(
                criteria="basegame", quota=0.30,
                conditions=condition({0.6: 3, 1.5: 7, 2.4: 9, 3.0: 10, 3.6: 6, 4.5: 4, 6.0: 3, 9.0: 1, 15.0: 0.2}),
            ),
        ]

        # Normal Bonus Buy: guaranteed three-scatter Bonus feature. 100x price
        # is the user's confirmed value. 10,000x remains the per-round max win.
        bonus_buy_distributions = [
            Distribution(
                criteria="wincap", quota=0.001, win_criteria=self.wincap,
                conditions=condition({self.wincap: 1}, scatter_triggers={3: 1}, force_wincap=True, force_freegame=True),
            ),
            Distribution(
                criteria="bonus", quota=0.999,
                conditions=condition(
                    {0.0: 1, 10.0: 1, 25.0: 2, 50.0: 3, 75.0: 4, 100.0: 5, 125.0: 4, 150.0: 3, 200.0: 2, 300.0: 1, 500.0: 0.3, 1000.0: 0.05},
                    scatter_triggers={3: 1}, force_freegame=True,
                ),
            ),
        ]

        # Super Bonus Buy: deep-run purchase. 500x is the owner-confirmed
        # price.
        super_bonus_distributions = [
            Distribution(
                criteria="wincap", quota=0.001, win_criteria=self.wincap,
                conditions=condition({self.wincap: 1}, scatter_triggers={4: 4, 5: 1}, force_wincap=True, force_freegame=True),
            ),
            Distribution(
                criteria="deep_run", quota=0.999,
                conditions=condition(
                    {0.0: 1, 50.0: 1, 100.0: 2, 200.0: 3, 300.0: 4, 400.0: 5, 500.0: 5, 600.0: 4, 750.0: 3, 1000.0: 2, 1500.0: 1, 3000.0: 0.2},
                    scatter_triggers={4: 4, 5: 1}, force_freegame=True,
                ),
            ),
        ]

        self.bet_modes = [
            BetMode(name="base", cost=1.0, rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=True, is_buybonus=False,
                    distributions=base_distributions),
            BetMode(name="ante", cost=3.0, rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=True, is_buybonus=False,
                    distributions=ante_distributions),
            BetMode(name="bonus", cost=100.0, rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=False, is_buybonus=True,
                    distributions=bonus_buy_distributions),
            BetMode(name="super_bonus", cost=500.0, rtp=self.rtp, max_win=self.wincap,
                    auto_close_disabled=False, is_feature=False, is_buybonus=True,
                    distributions=super_bonus_distributions),
        ]
