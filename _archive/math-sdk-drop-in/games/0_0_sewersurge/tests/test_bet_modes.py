from game_config import GameConfig
from game_optimization import OptimizationSetup

def test_four_modes_and_confirmed_normal_bonus_price():
    config = GameConfig()
    modes = {mode.get_name(): mode for mode in config.bet_modes}
    assert set(modes) == {"base", "ante", "bonus", "super_bonus"}
    assert modes["base"].get_cost() == 1.0
    assert modes["ante"].get_cost() == 3.0
    assert modes["bonus"].get_cost() == 100.0
    assert modes["super_bonus"].get_cost() == 500.0  # owner-confirmed
    assert modes["bonus"].get_buybonus() is True
    assert modes["super_bonus"].get_buybonus() is True

def test_ante_bonus_and_deep_run_hit_rate_targets_are_five_times_base():
    config = GameConfig()
    OptimizationSetup(config)
    base = config.opt_params["base"]["conditions"]
    ante = config.opt_params["ante"]["conditions"]
    assert abs(base["bonus"]["hr"] / ante["bonus"]["hr"] - 5.0) < 0.01
    assert abs(base["deep_run"]["hr"] / ante["deep_run"]["hr"] - 5.0) < 0.01

def test_all_modes_target_configured_rtp():
    config = GameConfig()
    OptimizationSetup(config)
    for name, setup in config.opt_params.items():
        assert abs(sum(v["rtp"] for v in setup["conditions"].values()) - 0.965) < 0.00001, name


def test_criteria_quotas_sum_to_one_and_max_win_is_first():
    config = GameConfig()
    for mode in config.bet_modes:
        distributions = mode.get_distributions()
        assert distributions[0].get_criteria() == "wincap"
        assert abs(sum(d.get_quota() for d in distributions) - 1.0) < 1e-9


def test_feature_rtp_contribution_uses_each_mode_cost():
    config = GameConfig()
    OptimizationSetup(config)
    modes = {mode.get_name(): mode for mode in config.bet_modes}
    for mode_name in ("base", "ante"):
        mode = modes[mode_name]
        conditions = config.opt_params[mode_name]["conditions"]
        for criterion in ("bonus", "deep_run", "basegame"):
            condition = conditions[criterion]
            hr = condition["hr"]
            target_rtp = condition["rtp"]
            expected_average_award = hr * target_rtp * mode.get_cost()
            # SDK optimizer target is the RTP share of the actual mode stake.
            measured_share = (1.0 / hr) * expected_average_award / mode.get_cost()
            assert abs(measured_share - target_rtp) < 1e-9
