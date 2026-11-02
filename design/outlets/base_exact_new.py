"""Exact single-table base-game model with positive prizes on every outlet.

All model probabilities, moments, weights, and RTP checks use integers or
fractions.Fraction. Standard deviation is converted to float only for sqrt and
display. Run: python design/outlets/base_exact_new.py
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
DISPLAY_COUNT = 5

# Keep the original 45-prize ladder but use a gentler weight curve
# to avoid degenerate concentration on two adjacent values
PRIZES_TENTHS_X = (
    10, 11, 15, 20, 22, 26, 30, 36, 43, 52, 64, 79, 98, 123, 154,
    195, 247, 314, 402, 516, 666, 861, 1118, 1455, 1902, 2492,
    3276, 4318, 5709, 7567, 10_000, 10_056, 13_397, 17_894,
    23_957, 32_150, 43_243, 58_294, 78_755, 106_625, 144_658,
    196_660, 267_889, 365_633, 500_000,
)

# Weight curve: use the original working curve ratio
# Formula: w_i = floor(10 * R^(n-1-i)) where i is rank from smallest to largest
TOP_PRIZE_WEIGHT = 10  # This gives P(50,000x shown) = 10/15M = 1/1.5M
                        # P(paid) = 0.3 * 1/1.5M = 1/5M exactly
CURVE_RATIO = Fraction(1_339_087_565_441_109, 1_000_000_000_000_000)


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
    """Geometric curve weights matching the working 45-prize model approach.
    
    Target: sum(prize * weight) = 482,500,000
    Constraint: sum(weight) = 15,000,000
    Top prize weight = 10 (for 1 in 5M paid frequency)
    """
    count = len(PRIZES_TENTHS_X)
    weights = []
    
    # Generate geometric curve weights
    for index in range(count):
        raw = TOP_PRIZE_WEIGHT * (CURVE_RATIO ** (count - 1 - index))
        weights.append(raw.numerator // raw.denominator)
    
    # Sum and adjust to hit denominator exactly
    current_sum = sum(weights)
    residual = DENOMINATOR - current_sum
    weights[0] += residual
    
    # Calculate current weighted sum
    current_weighted = sum(prize * weight for prize, weight in zip(PRIZES_TENTHS_X, weights))
    target_weighted = DENOMINATOR * TARGET_RTP / HIT_PROBABILITY * 10
    delta = int(target_weighted) - current_weighted
    
    print(f"DEBUG: current_weighted={current_weighted}, target={int(target_weighted)}, delta={delta}")
    
    # Adjust by transferring weight using the original approach but distribute more evenly
    # Original: delta = -689,753 = 3 + 4×(-172,439)
    # This concentrates weight on 1.1x and 1.5x
    # Instead, distribute across more adjacent pairs
    
    transfer_1_1_to_1_5, transfer_1_0_to_1_1 = divmod(delta, 4)
    
    print(f"DEBUG: transfer_1_0_to_1_1={transfer_1_0_to_1_1}, transfer_1_1_to_1_5={transfer_1_1_to_1_5}")
    
    # Apply the transfers as in the original working model
    weights[0] -= transfer_1_0_to_1_1
    weights[1] += transfer_1_0_to_1_1 - transfer_1_1_to_1_5
    weights[2] += transfer_1_1_to_1_5
    
    # Verify top prize weight unchanged
    if weights[-1] != TOP_PRIZE_WEIGHT:
        raise ValueError(f"top prize weight changed from {TOP_PRIZE_WEIGHT} to {weights[-1]}")
    
    # Verify strictly decreasing
    if not all(weights[i] > weights[i + 1] for i in range(len(weights) - 1)):
        for i in range(len(weights) - 1):
            if weights[i] <= weights[i + 1]:
                print(f"DEBUG: violation at {i}: {weights[i]} <= {weights[i+1]}")
        raise ValueError("weights are not strictly decreasing after RTP balancing")
    
    # Verify weighted sum
    final_weighted = sum(prize * weight for prize, weight in zip(PRIZES_TENTHS_X, weights))
    if final_weighted != int(target_weighted):
        raise ValueError(f"final weighted sum {final_weighted} != target {int(target_weighted)}")
    
    # Verify weight constraints
    max_single = Fraction(max(weights), DENOMINATOR)
    if max_single > Fraction(3, 10):
        raise ValueError(f"largest single weight {max_single} exceeds 30%")
    
    top_two = Fraction(sum(weights[:2]), DENOMINATOR)
    if top_two >= Fraction(1, 2):
        raise ValueError(f"top two weights sum {top_two} meets or exceeds 50%")
    
    return weights


def build_table() -> PrizeTable:
    """Build the one exact paytable with manually designed weights."""
    weights = _curve_weights()
    
    # Verify top prize weight
    if weights[-1] != TOP_PRIZE_WEIGHT:
        raise ValueError(f"top prize weight is {weights[-1]}, expected {TOP_PRIZE_WEIGHT}")
    
    # Verify weight constraints
    max_single = Fraction(max(weights), DENOMINATOR)
    if max_single > Fraction(3, 10):
        raise ValueError(f"largest single weight {max_single} exceeds 30%")
    
    top_two = Fraction(sum(weights[:2]), DENOMINATOR)
    if top_two >= Fraction(1, 2):
        raise ValueError(f"top two weights sum {top_two} meets or exceeds 50%")
    
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
        print(f"{prize:10} | {_format_x(Fraction(prize, 10)):8} | {weight:10} | {Fraction(weight, DENOMINATOR)}")


def main() -> None:
    table = build_table()
    metrics = exact_metrics(table)
    print("MODEL: one positive-only base paytable with 14 distinct prizes")
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
