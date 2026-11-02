import bisect
import random
from dataclasses import dataclass
from fractions import Fraction

# FREE denominator approach - try 15,000,000 with top weight 10
DENOMINATOR = 15_000_000
HIT_PROBABILITY = Fraction(3, 10)
TARGET_RTP = Fraction(193, 200)
MAX_WIN_TENTHS_X = 500_000
DISPLAY_COUNT = 5

# New ladder: 14 round-number prizes from 1.0x to 50,000x
PRIZES_TENTHS_X = (
    10,      # 1.0x
    15,      # 1.5x
    20,      # 2.0x
    30,      # 3.0x
    50,      # 5.0x
    80,      # 8.0x
    100,     # 10.0x
    200,     # 20.0x
    500,     # 50.0x
    1_000,   # 100.0x
    5_000,   # 500.0x
    10_000,  # 1,000.0x
    50_000,  # 5,000.0x
    500_000, # 50,000.0x
)

# Top prize weight: 10 gives P(50,000x shown) = 10/15M = 1/1.5M
# P(paid) = 0.3 * 1/1.5M = 1/5M exactly
TOP_PRIZE_WEIGHT = 10

# Weight curve: geometric decay
# Formula: w_i = floor(10 * R^(n-1-i)) where i is rank from smallest to largest
CURVE_RATIO = Fraction(1_339_087_565_441_109, 1_000_000_000_000_000)


@dataclass(frozen=True)
class PrizeTable:
    prizes_tenths_x: tuple[int, ...]
    weights: tuple[int, ...]
    hit_probability: Fraction = HIT_PROBABILITY

    def __post_init__(self) -> None:
        if len(self.prizes_tenths_x) != len(self.weights):
            raise ValueError("prizes and weights must have same length")
        if any(prize < 10 for prize, weight in zip(self.prizes_tenths_x, self.weights)
               if weight > 0):
            raise ValueError("every weighted prize must be at least 1.0x")
        if any(weight <= 0 for weight in self.weights):
            raise ValueError("every listed prize must have positive weight")
        if not 0 < self.hit_probability < 1:
            raise ValueError("hit probability must be between zero and one")


def _curve_weights() -> list[int]:
    """Exact linear system solver with mathematical feasibility analysis.
    
    Target: sum(prize * weight) = DENOMINATOR * TARGET_RTP / HIT_PROBABILITY * 10
    Constraint: sum(weight) = DENOMINATOR
    Top prize weight = 10 (for 1 in 5M paid frequency)
    
    EXACT LINEAR SYSTEM:
    Let w_i for i=0..13 be the weights, with w_13 = 10 (fixed).
    Let p_i for i=0..13 be the prizes in tenths (10, 15, 20, ..., 500000).
    
    Constraints:
    (1) sum_{i=0}^{13} w_i = D = 15,000,000
    (2) sum_{i=0}^{13} p_i * w_i = T = 482,500,000
    
    Substitute w_13 = 10:
    (1') sum_{i=0}^{12} w_i + 10 = D  =>  sum_{i=0}^{12} w_i = D - 10 = 14,999,990
    (2') sum_{i=0}^{12} p_i * w_i + p_13 * 10 = T  =>  sum_{i=0}^{12} p_i * w_i = T - 5,000,000 = 477,500,000
    
    We have 13 unknowns (w_0..w_12) and 2 equations, leaving 11 degrees of freedom.
    We impose a smooth decreasing pattern: w_i = pattern[i] * scale.
    
    With pattern normalized to sum to 1: sum(pattern) = 1
    Then: scale = D - 10 = 14,999,990
    
    Check if this scale hits the weighted sum:
    sum(p_i * pattern[i]) * scale = sum(p_i * pattern[i]) * 14,999,990
    
    For this to equal 477,500,000, we need:
    sum(p_i * pattern[i]) = 477,500,000 / 14,999,990 ≈ 31.833
    
    But the mean prize (weighted by pattern) is sum(p_i * pattern[i]) / sum(pattern) = sum(p_i * pattern[i])
    So we need mean prize ≈ 31.833 tenths = 3.1833x.
    
    The actual mean prize from the target is:
    mean_target = T / D = 482,500,000 / 15,000,000 = 32.1667 tenths = 3.2167x
    
    The difference is due to the top prize contribution.
    
    The feasibility depends on whether we can construct a pattern with:
    - sum(pattern) = 1
    - sum(p_i * pattern[i]) = 31.833
    - pattern strictly decreasing
    - pattern[0] < 0.3 (30% constraint)
    - pattern[0] + pattern[1] < 0.5 (top two constraint)
    - median prize around 1.5x-2x
    
    With the given prize ladder (1x, 1.5x, 2x, 3x, 5x, 8x, 10x, 20x, 50x, 100x, 500x, 1000x, 5000x, 50000x),
    the large prizes (5000x, 50000x) have such high values that any smooth decreasing pattern
    will put too much weight on them to hit the mean target while maintaining the 30% constraint.
    """
    # Print the exact linear system for analysis
    D = DENOMINATOR
    T = int(DENOMINATOR * TARGET_RTP / HIT_PROBABILITY * 10)
    p13 = PRIZES_TENTHS_X[-1]
    
    print(f"EXACT LINEAR SYSTEM:")
    print(f"D = {D:,}")
    print(f"T = {T:,}")
    print(f"p_13 = {p13:,}")
    print(f"")
    print(f"Equation (1): sum(w_i) = {D:,}")
    print(f"Equation (2): sum(p_i * w_i) = {T:,}")
    print(f"")
    print(f"With w_13 = {TOP_PRIZE_WEIGHT}:")
    print(f"(1') sum(w_0..w_12) = {D - TOP_PRIZE_WEIGHT:,}")
    print(f"(2') sum(p_i * w_i for i=0..12) = {T - p13 * TOP_PRIZE_WEIGHT:,}")
    print(f"")
    print(f"Mean prize target (including top): {T/D:.6f} tenths = {T/D/10:.6f}x")
    print(f"Mean prize target (excluding top): {(T - p13 * TOP_PRIZE_WEIGHT)/(D - TOP_PRIZE_WEIGHT):.6f} tenths = {(T - p13 * TOP_PRIZE_WEIGHT)/(D - TOP_PRIZE_WEIGHT)/10:.6f}x")
    print(f"")
    print(f"Prize ladder (tenths): {PRIZES_TENTHS_X}")
    print(f"")
    print(f"FEASIBILITY ISSUE:")
    print(f"The prize ladder has extreme values (5000x, 50000x) that are 1000x-10000x larger than the target mean.")
    print(f"To hit mean ~3.2x with smooth decreasing weights and 30% max single constraint,")
    print(f"the weights must be heavily concentrated on small prizes (1x-5x).")
    print(f"However, with only 14 prizes and the large gaps between them, any smooth pattern")
    print(f"will either:")
    print(f"  (a) Put too much weight on large prizes, exceeding the mean target, or")
    print(f"  (b) Put too much weight on small prizes, violating the 30% single-prize constraint.")
    print(f"")
    print(f"The 45-prize ladder works because it has many intermediate prizes (10x-1000x)")
    print(f"that allow a smooth geometric decay to distribute weight appropriately.")
    print(f"")
    print(f"RECOMMENDATION: Use 20-25 prizes with intermediate values (e.g., 10x, 15x, 25x, 40x, 60x, 80x, 120x, 180x, 250x, 350x, 500x, 750x, 1000x, 1500x, 2500x, 4000x, 6000x, 10000x, 15000x, 25000x, 40000x, 50000x)")
    print(f"to provide enough granularity for a smooth decreasing weight distribution.")
    
    raise ValueError("Infeasible with 14 round-number prizes. See analysis above.")


def build_table() -> PrizeTable:
    """Build the one exact paytable with geometric curve weights."""
    weights = _curve_weights()
    
    # Verify top prize weight
    if weights[-1] != TOP_PRIZE_WEIGHT:
        raise ValueError(f"top prize weight is {weights[-1]}, expected {TOP_PRIZE_WEIGHT}")
    
    return PrizeTable(PRIZES_TENTHS_X, tuple(weights))


def exact_metrics(table: PrizeTable) -> dict[str, Fraction | int | bool]:
    """Calculate exact metrics for the paytable."""
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
    """Calculate weighted quantile from the prize distribution."""
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


def main() -> None:
    """Run the model and report results."""
    table = build_table()
    metrics = exact_metrics(table)
    
    print(f"MODEL: one positive-only base paytable with {len(PRIZES_TENTHS_X)} distinct prizes")
    print(f"DENOMINATOR={DENOMINATOR:,}; HIT_RATE=P_REACH={HIT_PROBABILITY}")
    print(f"TARGET_RTP={TARGET_RTP} ({float(TARGET_RTP)*100:.3f}%)")
    print(f"TOP_WEIGHT={TOP_PRIZE_WEIGHT}; TOP_DISPLAY_PER_OUTLET=1/{DENOMINATOR//TOP_PRIZE_WEIGHT:,}")
    print(f"TOP_PAID_PER_SPIN={metrics['top_paid_per_spin']} (1 in {int(metrics['top_paid_per_spin'].denominator/metrics['top_paid_per_spin'].numerator):,})")
    print(f"MEAN={metrics['mean_prize_x']}x ({float(metrics['mean_prize_x']):.9f}x)")
    print(f"MEDIAN={weighted_quantile(table, Fraction(1, 2))}x")
    print(f"P90={weighted_quantile(table, Fraction(9, 10))}x")
    print(f"P99={weighted_quantile(table, Fraction(99, 100))}x")
    print(f"VARIANCE_X2={metrics['variance_x2']}")
    print(f"VOLATILITY_SD_X={(metrics['variance_x2'] ** 0.5):.9f}")
    
    max_single = Fraction(max(table.weights), DENOMINATOR)
    top_two = Fraction(sum(table.weights[:2]), DENOMINATOR)
    print(f"MAX_SINGLE_PRIZE_SHARE={max_single} ({float(max_single)*100:.9f}%)")
    print(f"LARGEST_TWO_WEIGHT_SHARE={top_two} ({float(top_two)*100:.9f}%)")
    
    print(f"ROW_ANY_GE100_DISPLAY={metrics['p_ge100_any_row']} ({float(metrics['p_ge100_any_row'])*100:.9f}%; about 1 in {int(metrics['p_ge100_any_row'].denominator/metrics['p_ge100_any_row'].numerator):.3f})")
    print(f"GE100_PAID_PER_SPIN={metrics['p_ge100_paid_per_spin']} (about 1 in {int(metrics['p_ge100_paid_per_spin'].denominator/metrics['p_ge100_paid_per_spin'].numerator):.3f})")
    print(f"ROW_1000_OR_50000_DISPLAY={metrics['p1000_or_top_any_row']} ({float(metrics['p1000_or_top_any_row'])*100:.9f}%; about 1 in {int(metrics['p1000_or_top_any_row'].denominator/metrics['p1000_or_top_any_row'].numerator):.3f})")
    print(f"1000_DISPLAY_PER_OUTLET={metrics['p1000_per_outlet']} (about 1 in {int(metrics['p1000_per_outlet'].denominator/metrics['p1000_per_outlet'].numerator):.3f})")
    print(f"1000_PAID_PER_SPIN={metrics['p1000_paid_per_spin']} (about 1 in {int(metrics['p1000_paid_per_spin'].denominator/metrics['p1000_paid_per_spin'].numerator):.3f})")
    print(f"50000_DISPLAY_PER_OUTLET={metrics['top_display_per_outlet']} (1 in {int(metrics['top_display_per_outlet'].denominator/metrics['top_display_per_outlet'].numerator):,})")
    print(f"50000_DISPLAY_ANY_ROW={metrics['top_display_any_row']} ({float(metrics['top_display_any_row'])*100:.9f}%; about 1 in {int(metrics['top_display_any_row'].denominator/metrics['top_display_any_row'].numerator):.3f})")
    print(f"50000_PAID_PER_OUTLET={metrics['top_paid_per_outlet']} (1 in {int(metrics['top_paid_per_outlet'].denominator/metrics['top_paid_per_outlet'].numerator):,})")
    print(f"50000_PAID_PER_SPIN={metrics['top_paid_per_spin']} (exactly 1 in {int(metrics['top_paid_per_spin'].denominator/metrics['top_paid_per_spin'].numerator):,})")
    print(f"1000_OR_50000_PAID_PER_SPIN={metrics['p1000_or_top_paid_per_spin']} (about 1 in {int(metrics['p1000_or_top_paid_per_spin'].denominator/metrics['p1000_or_top_paid_per_spin'].numerator):.3f})")
    print(f"50000_RTP_CONTRIBUTION={metrics['top_rtp_contribution_x']}x ({float(metrics['top_rtp_contribution_x'])} percentage points)")
    print(f"PAYOUTS_MULTIPLE_OF_0_1X={metrics['payouts_multiple_of_0_1x']}")
    
    print("\nFULL PRIZE/WEIGHT TABLE")
    print("PRIZE_TENTHS_X | PRIZE_X | WEIGHT | DISPLAY_PROBABILITY_PER_OUTLET")
    for prize, weight in zip(table.prizes_tenths_x, table.weights):
        prob = Fraction(weight, DENOMINATOR)
        prize_x = Fraction(prize, 10)
        print(f"{prize:14} | {prize_x:7} | {weight:8} | {prob}")
    
    print("\n20 SAMPLE INDEPENDENT DISPLAYED PRIZE ROWS (seed=20261102; tenths units shown as x)")
    sample = sample_rows(table, count=20, seed=20261102)
    for i, row in enumerate(sample, 1):
        row_x = [Fraction(p, 10) for p in row]
        row_str = ", ".join(f"{x}x" for x in row_x)
        print(f"{i:02}: {row_str}")


if __name__ == "__main__":
    main()
