"""Legacy all-mode feasibility Monte Carlo for the earlier outlets proposal.

Run: python design/outlets/feasibility.py [--rounds 1000000] [--seed 20261101]
Only the Python standard library is required. Results are observations, not math
books and not a proposed production configuration.

Its zero-prize base table and 10,000x cap are superseded for Base-only table
selection by BASE_GAME_SPEC.md and base_exact.py. Do not use this legacy script
to evaluate the positive-only Base model.
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

from flow import Board, COLS, ROWS, board_from_outlet_rows, compute_payout

# Prize values are tenths of x; weights sum to 100,000. Their exact mean is
# 321.75 tenths (= 32.175x). Includes the illustrative 2x, 5x, and 1,000x prizes.
# Every outlet prize is drawn independently before routing on every spin.
PRIZES_TENTHS = (0, 20, 50, 100, 200, 300, 400, 500, 1_000, 2_000, 5_000, 10_000)
PRIZE_WEIGHTS = (27_805, 2_000, 2_000, 18_200, 15_000, 10_000, 8_000, 7_000,
                 5_000, 4_000, 895, 100)
assert sum(PRIZE_WEIGHTS) == 100_000

# Super valve type weights; valves appear on 75% of reached outlet paths.
VALVE_VALUES = (2, 3, 5, 10)
VALVE_WEIGHTS = (4_236, 2_000, 2_000, 1_764)
assert sum(VALVE_WEIGHTS) == 10_000

MAX_ROUND_TENTHS = 100_000  # 10,000x measured against the base-game wager.
TARGET_RTP = 0.965
BONUS_SPLIT_FREQUENCY = 0.499805749806
SUPER_SPLIT_FREQUENCY = 0.85
SUPER_VALVE_FREQUENCY = 0.749940194838
BASE_BONUS_RATE = 0.001  # exactly 3 scatters per base round
BASE_SUPER_RATE = 0.0001  # 4 scatters: 0.00008; 5 scatters: 0.00002
MODE_CONFIG = {
    "base": {"cost": 1, "stake_scale": 1, "bonus_rate": BASE_BONUS_RATE,
             "super_rate": BASE_SUPER_RATE},
    "ante": {"cost": 3, "stake_scale": 3, "bonus_rate": 5 * BASE_BONUS_RATE,
             "super_rate": 5 * BASE_SUPER_RATE},
    "buy_bonus": {"cost": 100, "stake_scale": 1, "bonus_rate": None,
                  "super_rate": None},
    "super_buy": {"cost": 500, "stake_scale": 1, "bonus_rate": None,
                  "super_rate": None},
}


def weighted_pick(rng: random.Random, values, weights):
    ticket = rng.randrange(sum(weights))
    for value, weight in zip(values, weights):
        if ticket < weight:
            return value
        ticket -= weight
    raise AssertionError("weights did not cover the draw")


def draw_prize_row(rng: random.Random) -> tuple[int, ...]:
    """Draw every row prize independently, without inspecting board outcomes."""
    return tuple(weighted_pick(rng, PRIZES_TENTHS, PRIZE_WEIGHTS) for _ in range(ROWS))


def draw_outlet_rows(rng: random.Random, split_frequency: float) -> tuple[int, ...]:
    first = rng.randrange(ROWS)
    extra = tuple(row for row in range(ROWS)
                  if row != first and rng.random() < split_frequency)
    return tuple(sorted((first, *extra)))


def draw_valves(rng: random.Random, rows: tuple[int, ...]) -> dict[int, int]:
    return {
        row: (weighted_pick(rng, VALVE_VALUES, VALVE_WEIGHTS)
              if rng.random() < SUPER_VALVE_FREQUENCY else 1)
        for row in rows
    }


def empty_board() -> Board:
    return Board(tuple(tuple(None for _ in range(COLS)) for _ in range(ROWS)))


def feature_payout(rng: random.Random, *, super_feature: bool) -> int:
    # Prize row is an independent per-spin draw, not conditioned on the board.
    prizes = draw_prize_row(rng)
    split_frequency = SUPER_SPLIT_FREQUENCY if super_feature else BONUS_SPLIT_FREQUENCY
    rows = draw_outlet_rows(rng, split_frequency)
    valves = draw_valves(rng, rows) if super_feature else None
    board = board_from_outlet_rows(rows, rng=rng, valves_by_row=valves)
    payout, _trace = compute_payout(
        board, prizes, split=True, cap=MAX_ROUND_TENTHS
    )
    return payout


def ordinary_payout(rng: random.Random, route_frequency: float) -> int:
    # Even dead-end rounds receive the same independent five-prize display draw.
    prizes = draw_prize_row(rng)
    if rng.random() >= route_frequency:
        # An unconnected inlet is a dead end, with no outlet paid.
        return 0
    row = rng.randrange(ROWS)
    board = board_from_outlet_rows((row,), rng=rng)
    payout, _trace = compute_payout(board, prizes, split=False, rng=rng)
    return payout


@dataclass
class Stats:
    rounds: int = 0
    hit: int = 0
    max_wins: int = 0
    total_return: float = 0.0
    total_return_sq: float = 0.0
    feature_zero: int = 0

    def add(self, payout_tenths: int, cost: int, *, feature: bool) -> None:
        normalized = payout_tenths / (10 * cost)
        self.rounds += 1
        self.hit += payout_tenths > 0
        self.max_wins += payout_tenths >= MAX_ROUND_TENTHS
        self.total_return += normalized
        self.total_return_sq += normalized * normalized
        self.feature_zero += feature and payout_tenths == 0

    def report(self) -> dict[str, float | int]:
        mean = self.total_return / self.rounds
        variance = max(0.0, self.total_return_sq / self.rounds - mean * mean)
        return {
            "rounds": self.rounds,
            "RTP_percent": mean * 100,
            "hit_rate_percent": self.hit * 100 / self.rounds,
            "volatility_sd_x_per_wager": math.sqrt(variance),
            "max_win_count": self.max_wins,
            "max_win_frequency": self.rounds / self.max_wins if self.max_wins else None,
            "feature_zero_count": self.feature_zero,
        }


def simulate_mode(name: str, rounds: int, seed: int) -> Stats:
    cfg = MODE_CONFIG[name]
    rng = random.Random(seed)
    stats = Stats()

    if name in ("buy_bonus", "super_buy"):
        is_super = name == "super_buy"
        for _ in range(rounds):
            payout = feature_payout(rng, super_feature=is_super)
            stats.add(payout, cfg["cost"], feature=True)
        return stats

    bonus_rate = cfg["bonus_rate"]
    super_rate = cfg["super_rate"]
    prize_mean = (sum(v * w for v, w in zip(PRIZES_TENTHS, PRIZE_WEIGHTS))
                  / sum(PRIZE_WEIGHTS)) / 10
    bonus_outlets = 1 + 4 * BONUS_SPLIT_FREQUENCY
    super_outlets = 1 + 4 * SUPER_SPLIT_FREQUENCY
    expected_bonus = bonus_outlets * prize_mean
    valve_mean_if_present = sum(v * w for v, w in zip(VALVE_VALUES, VALVE_WEIGHTS)) / sum(VALVE_WEIGHTS)
    expected_super = super_outlets * prize_mean * (
        1 + SUPER_VALVE_FREQUENCY * (valve_mean_if_present - 1)
    )
    feature_part = bonus_rate * expected_bonus + super_rate * expected_super
    ordinary_mean_needed = (TARGET_RTP - feature_part) / (1 - bonus_rate - super_rate)
    route_frequency = ordinary_mean_needed / prize_mean
    if not 0 <= route_frequency <= 1:
        raise ValueError(f"derived route frequency outside [0,1] for {name}: {route_frequency}")

    for _ in range(rounds):
        draw = rng.random()
        if draw < bonus_rate:
            raw = feature_payout(rng, super_feature=False)
            feature = True
        elif draw < bonus_rate + super_rate:
            raw = feature_payout(rng, super_feature=True)
            feature = True
        else:
            raw = ordinary_payout(rng, route_frequency)
            feature = False
        # Ante costs 3x; its same game outcomes scale with its 3x stake.
        payout = min(raw * cfg["stake_scale"], MAX_ROUND_TENTHS)
        stats.add(payout, cfg["cost"], feature=feature)
    stats.route_frequency = route_frequency
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20261101)
    args = parser.parse_args()
    if args.rounds < 1_000_000:
        parser.error("at least 1,000,000 rounds per mode are required")

    print(f"seed={args.seed}; rounds_per_mode={args.rounds}; cap={MAX_ROUND_TENTHS / 10:.0f}x base wager")
    print("prize_table_x=" + ",".join(
        f"{v / 10:g}:{w / 1000:g}%" for v, w in zip(PRIZES_TENTHS, PRIZE_WEIGHTS)
    ))
    print("valves=" + ",".join(
        f"x{v}:{w / 100:g}%" for v, w in zip(VALVE_VALUES, VALVE_WEIGHTS)
    ) + f"; placement frequency={SUPER_VALVE_FREQUENCY:.1%} per reached Super outlet path; multiply every valve traversed")
    print(f"split_frequency_per_additional_outlet: Bonus={BONUS_SPLIT_FREQUENCY:.6f}; Super={SUPER_SPLIT_FREQUENCY:.3f}")
    print(f"natural_trigger_rates: base Bonus={BASE_BONUS_RATE:.6%}, Super={BASE_SUPER_RATE:.6%}; ante=5x")
    print("mode,rounds,RTP%,hit%,sd_x_per_wager,maxwin_count,maxwin_frequency,feature_zero_count,derived_route_frequency")
    for index, name in enumerate(MODE_CONFIG):
        stats = simulate_mode(name, args.rounds, args.seed + index)
        report = stats.report()
        route = getattr(stats, "route_frequency", "n/a")
        freq = report["max_win_frequency"]
        print(",".join((
            name, str(report["rounds"]), f'{report["RTP_percent"]:.6f}',
            f'{report["hit_rate_percent"]:.6f}',
            f'{report["volatility_sd_x_per_wager"]:.6f}',
            str(report["max_win_count"]), f'{freq:.3f}' if freq else "not_observed",
            str(report["feature_zero_count"]),
            f"{route:.8f}" if isinstance(route, float) else route,
        )))
    print("Note: max_win_frequency is rounds per observed 10,000x payout; not_observed means zero events in this sample.")


if __name__ == "__main__":
    main()
