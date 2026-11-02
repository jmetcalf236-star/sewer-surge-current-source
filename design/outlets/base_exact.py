"""Exact single-table base-game model with positive prizes on every outlet.

All model probabilities, moments, weights, and RTP checks use integers or
fractions.Fraction. Standard deviation is converted to float only for sqrt and
display. Run: python design/outlets/base_exact.py
"""

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass
from fractions import Fraction

DENOMINATOR = 15_000_000
HIT_PROBABILITY = Fraction(3, 10)
TARGET_RTP = Fraction(193, 200)
MAX_WIN_TENTHS_X = 500_000
TOP_PRIZE_WEIGHT = 10
DISPLAY_COUNT = 5
CURVE_RATIO = Fraction(1_339_087_565_441_109, 1_000_000_000_000_000)
ROUNDING_RESIDUAL_TO_FIRST_PRIZE = 19
RTP_TRANSFER_1_0_TO_1_1 = 3
RTP_TRANSFER_1_1_TO_1_5 = -172_439

# The distinct value ladder is rounded to 0.1x from
# 2.0x * 25000 ** ((k / 40) ** 1.24), k=1..40, with 1.0x, 1.1x, 1.5x,
# and 2.0x anchors and an explicit 1000x prize inserted. Stored in tenths.
PRIZES_TENTHS_X = (
    10, 11, 15, 20, 22, 26, 30, 36, 43, 52, 64, 79, 98, 123, 154,
    195, 247, 314, 402, 516, 666, 861, 1118, 1455, 1902, 2492,
    3276, 4318, 5709, 7567, 10_000, 10_056, 13_397, 17_894,
    23_957, 32_150, 43_243, 58_294, 78_755, 106_625, 144_658,
    196_660, 267_889, 365_633, 500_000,
)


@dataclass(frozen=True)
class PrizeTable:
    prizes_tenths_x: tuple[int, ...]
    weights: tuple[int, ...]
    hit_probability: Fraction = HIT_PROBABILITY

    def __post_init__(self) -> None:
        if len(self.prizes_tenths_x) != len(self.weights):
            raise ValueError("prizes and weights must have equal lengths")
        if sum(self.weights) != DENOMINATOR:
            raise ValueError("weights must sum to the exact denominator")
        if any(prize < 10 for prize, weight in zip(self.prizes_tenths_x, self.weights)
               if weight > 0):
            raise ValueError("every weighted prize must be at least 1.0x")
        if any(weight <= 0 for weight in self.weights):
            raise ValueError("every listed prize must have positive weight")
        if not 0 < self.hit_probability < 1:
            raise ValueError("hit probability must be between zero and one")


def _curve_weights() -> list[int]:
    """Integer geometric-rank curve, with exact integer rounding only."""
    count = len(PRIZES_TENTHS_X)
    weights = []
    for index in range(count):
        raw = TOP_PRIZE_WEIGHT * CURVE_RATIO ** (count - 1 - index)
        weights.append(raw.numerator // raw.denominator)
    residual = DENOMINATOR - sum(weights)
    if residual != ROUNDING_RESIDUAL_TO_FIRST_PRIZE:
        raise ValueError(f"unexpected curve rounding residual: {residual}")
    weights[0] += residual
    return weights


def build_table() -> PrizeTable:
    """Build the one exact paytable, including one small RTP balancing tier."""
    weights = _curve_weights()
    target_prize_tenths_sum = DENOMINATOR * TARGET_RTP / HIT_PROBABILITY * 10
    current = sum(Fraction(prize * weight)
                  for prize, weight in zip(PRIZES_TENTHS_X, weights))
    delta = target_prize_tenths_sum - current
    # 1.0->1.1 changes the moment by one tenths-unit per transferred weight;
    # 1.1->1.5 changes it by four. divmod solves the full residual exactly.
    transfer_1_1_to_1_5, transfer_1_0_to_1_1 = divmod(delta, 4)
    if (transfer_1_1_to_1_5 != RTP_TRANSFER_1_1_TO_1_5
            or transfer_1_0_to_1_1 != RTP_TRANSFER_1_0_TO_1_1):
        raise ValueError(
            "the exact RTP balancing transfer changed: "
            f"1.0->1.1={transfer_1_0_to_1_1}, "
            f"1.1->1.5={transfer_1_1_to_1_5}"
        )
    weights[0] -= transfer_1_0_to_1_1
    weights[1] += transfer_1_0_to_1_1 - transfer_1_1_to_1_5
    weights[2] += transfer_1_1_to_1_5
    if weights[-1] != TOP_PRIZE_WEIGHT:
        raise ValueError("top prize weight changed during RTP balancing")
    if not all(weights[i] > weights[i + 1] for i in range(len(weights) - 1)):
        raise ValueError("integer prize weights are not strictly decreasing")
    return PrizeTable(PRIZES_TENTHS_X, tuple(weights))


def exact_metrics(table: PrizeTable) -> dict[str, Fraction | int | bool]:
    denominator = sum(table.weights)
    distribution = tuple(
        (prize, Fraction(weight, denominator))
        for prize, weight in zip(table.prizes_tenths_x, table.weights)
    )
    mean_prize_x = sum((Fraction(prize, 10) * probability
                        for prize, probability in distribution), Fraction(0))
    second_moment_x2 = sum((Fraction(prize * prize, 100) * probability
                            for prize, probability in distribution), Fraction(0))
    hit_rate = table.hit_probability
    rtp = hit_rate * mean_prize_x
    variance_x2 = hit_rate * second_moment_x2 - rtp * rtp
    if rtp != TARGET_RTP:
        raise ValueError(f"RTP is {rtp}, expected exactly {TARGET_RTP}")

    top_tenths = max(table.prizes_tenths_x)
    top_probability = Fraction(table.weights[-1], denominator)
    p1000 = sum((probability for prize, probability in distribution
                 if prize == 10_000), Fraction(0))
    p_ge100 = sum((probability for prize, probability in distribution
                   if prize >= 1_000), Fraction(0))
    p_pair = p1000 + top_probability
    return {
        "mean_prize_x": mean_prize_x,
        "hit_rate": hit_rate,
        "rtp": rtp,
        "variance_x2": variance_x2,
        "top_tenths_x": top_tenths,
        "top_display_per_outlet": top_probability,
        "top_display_any_row": 1 - (1 - top_probability) ** DISPLAY_COUNT,
        "top_paid_per_outlet": hit_rate * top_probability / DISPLAY_COUNT,
        "top_paid_per_spin": hit_rate * top_probability,
        "top_rtp_contribution_x": hit_rate * top_probability * Fraction(top_tenths, 10),
        "p_ge100_per_outlet": p_ge100,
        "p_ge100_any_row": 1 - (1 - p_ge100) ** DISPLAY_COUNT,
        "p_ge100_paid_per_spin": hit_rate * p_ge100,
        "p1000_per_outlet": p1000,
        "p1000_or_top_any_row": 1 - (1 - p_pair) ** DISPLAY_COUNT,
        "p1000_paid_per_spin": hit_rate * p1000,
        "p1000_or_top_paid_per_spin": hit_rate * p_pair,
        "payouts_multiple_of_0_1x": all(prize >= 10 for prize in table.prizes_tenths_x),
    }


def weighted_quantile(table: PrizeTable, probability: Fraction) -> Fraction:
    if not 0 <= probability <= 1:
        raise ValueError("quantile probability must be in [0,1]")
    cumulative = 0
    for prize, weight in zip(table.prizes_tenths_x, table.weights):
        cumulative += weight
        if Fraction(cumulative, DENOMINATOR) >= probability:
            return Fraction(prize, 10)
    return Fraction(table.prizes_tenths_x[-1], 10)


def sample_rows(table: PrizeTable, count: int = 20, seed: int = 20261102) -> tuple[tuple[int, ...], ...]:
    """Draw independent displayed prize rows using the exact integer weights."""
    rng = random.Random(seed)
    cumulative = []
    total = 0
    for weight in table.weights:
        total += weight
        cumulative.append(total)
    return tuple(
        tuple(table.prizes_tenths_x[bisect.bisect_right(cumulative, rng.randrange(DENOMINATOR))]
              for _ in range(DISPLAY_COUNT))
        for _ in range(count)
    )


def _one_in(probability: Fraction) -> str:
    inverse = 1 / probability
    if inverse.denominator == 1:
        return f"1 in {inverse.numerator:,}"
    return f"about 1 in {float(inverse):,.3f}"


def _percent(probability: Fraction) -> str:
    return f"{float(probability * 100):.9f}%"


def _format_x(value: Fraction) -> str:
    tenths = value * 10
    if tenths.denominator != 1:
        raise ValueError(f"payout is not an integer tenth: {value}")
    whole, fraction = divmod(tenths.numerator, 10)
    return f"{whole}x" if fraction == 0 else f"{whole}.{fraction}x"


def _print_table(table: PrizeTable) -> None:
    print("PRIZE_TENTHS_X | PRIZE_X | WEIGHT | DISPLAY_PROBABILITY_PER_OUTLET")
    for prize, weight in zip(table.prizes_tenths_x, table.weights):
        print(f"{prize} | {_format_x(Fraction(prize, 10))} | {weight} | {Fraction(weight, DENOMINATOR)}")


def main() -> None:
    table = build_table()
    metrics = exact_metrics(table)
    print("MODEL: one positive-only base paytable; all five outlet prizes drawn on every spin")
    print(f"DENOMINATOR={DENOMINATOR:,}; HIT_RATE=P_REACH={HIT_PROBABILITY}")
    print(f"TARGET_RTP={TARGET_RTP} ({float(TARGET_RTP * 100):.3f}%)")
    print(f"TOP_WEIGHT={table.weights[-1]}; TOP_DISPLAY_PER_OUTLET={metrics['top_display_per_outlet']}")
    print(f"TOP_PAID_PER_SPIN={metrics['top_paid_per_spin']} ({_one_in(metrics['top_paid_per_spin'])})")
    print(f"MEAN={metrics['mean_prize_x']}x ({float(metrics['mean_prize_x']):.9f}x)")
    print(f"MEDIAN={_format_x(weighted_quantile(table, Fraction(1, 2)))}")
    print(f"P90={_format_x(weighted_quantile(table, Fraction(9, 10)))}")
    print(f"P99={_format_x(weighted_quantile(table, Fraction(99, 100)))}")
    print(f"VARIANCE_X2={metrics['variance_x2']}")
    print(f"VOLATILITY_SD_X={math.sqrt(float(metrics['variance_x2'])):.9f}")
    print(f"MAX_SINGLE_PRIZE_SHARE={Fraction(max(table.weights), DENOMINATOR)} ({_percent(Fraction(max(table.weights), DENOMINATOR))})")
    print(f"LARGEST_TWO_WEIGHT_SHARE={Fraction(sum(table.weights[:2]), DENOMINATOR)} ({_percent(Fraction(sum(table.weights[:2]), DENOMINATOR))})")
    print(f"ROW_ANY_GE100_DISPLAY={metrics['p_ge100_any_row']} ({_percent(metrics['p_ge100_any_row'])}; {_one_in(metrics['p_ge100_any_row'])})")
    print(f"GE100_PAID_PER_SPIN={metrics['p_ge100_paid_per_spin']} ({_one_in(metrics['p_ge100_paid_per_spin'])})")
    print(f"ROW_1000_OR_50000_DISPLAY={metrics['p1000_or_top_any_row']} ({_percent(metrics['p1000_or_top_any_row'])}; {_one_in(metrics['p1000_or_top_any_row'])})")
    print(f"1000_DISPLAY_PER_OUTLET={metrics['p1000_per_outlet']} ({_one_in(metrics['p1000_per_outlet'])})")
    print(f"1000_PAID_PER_SPIN={metrics['p1000_paid_per_spin']} ({_one_in(metrics['p1000_paid_per_spin'])})")
    print(f"50000_DISPLAY_PER_OUTLET={metrics['top_display_per_outlet']} ({_one_in(metrics['top_display_per_outlet'])})")
    print(f"50000_DISPLAY_ANY_ROW={metrics['top_display_any_row']} ({_percent(metrics['top_display_any_row'])}; {_one_in(metrics['top_display_any_row'])})")
    print(f"50000_PAID_PER_OUTLET={metrics['top_paid_per_outlet']} ({_one_in(metrics['top_paid_per_outlet'])})")
    print(f"50000_PAID_PER_SPIN={metrics['top_paid_per_spin']} (exactly 1 in 5,000,000)")
    print(f"1000_OR_50000_PAID_PER_SPIN={metrics['p1000_or_top_paid_per_spin']} ({_one_in(metrics['p1000_or_top_paid_per_spin'])})")
    print(f"50000_RTP_CONTRIBUTION={metrics['top_rtp_contribution_x']}x ({metrics['top_rtp_contribution_x'] * 100} percentage points)")
    print(f"PAYOUTS_MULTIPLE_OF_0_1X={metrics['payouts_multiple_of_0_1x']}")
    print("\nFULL PRIZE/WEIGHT TABLE")
    _print_table(table)
    print("\n20 SAMPLE INDEPENDENT DISPLAYED PRIZE ROWS (seed=20261102; tenths units shown as x)")
    for index, row in enumerate(sample_rows(table), start=1):
        print(f"{index:02d}: " + ", ".join(_format_x(Fraction(prize, 10)) for prize in row))


if __name__ == "__main__":
    main()
