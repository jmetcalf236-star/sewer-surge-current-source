# Sewer Surge Base: positive-prize outlets

Design study only. No production game, SDK, math, configuration, audit,
frontend, book, LUT, or RGS file is changed.

## Final base-game rules

- The board is 5×5. Water enters west at cell `(2,0)`. The east side has one
  outlet per row, indexed `0` through `4`.
- Every spin displays five independently drawn prizes. Every outlet prize is at
  least `1.0×`; there is no zero-prize symbol. The prize row is drawn on wins
  and losses, independently of the hit/miss result.
- The route reaches an outlet with probability `3/10`, which is also the hit
  rate. Otherwise the water ends at a dead end and the payout is zero.
- On a hit, choose one of the five outlets uniformly. The payout is the prize
  displayed at that outlet. Base never splits the water.
- The one paytable has a 50,000× outlet prize. It is paid exactly 1 in 5,000,000
  spins. There are no 1-in-10M or 1-in-20M table variants.
- Target RTP is exactly `193/200 = 96.5%`. All prize and payout multipliers use
  tenths of x.

## Prize ladder and weight curve

The denominator is `D = 15,000,000`. Weights are integer counts over D. The
45 prize values are positive and distinct, from 1.0× to 50,000×. The value
ladder is formed from anchors 1.0×, 1.1×, 1.5×, and 2.0×, then 40 values
rounded half-up to the nearest 0.1× from
`2.0 × 25000^((k/40)^1.24)` for `k=1..40`, with an exact 1,000× prize inserted
and the list sorted. The resulting integer-tenths values are in
[`base_exact.py`](base_exact.py).

Weights follow a decreasing geometric curve by prize rank. For index `i=0..44`
in ascending prize order, the raw integer weight is

```text
u_i = floor(10 × R^(44-i))
R   = 1339087565441109 / 1000000000000000
```

The top prize weight is therefore 10 and the denominator is 15,000,000, giving
`P(50,000× shown at a specified outlet)=1/1,500,000`. Flooring the curve leaves
19 counts; those are added to the 1.0× weight so the weights sum to D.

The raw curve's prize-weighted tenths sum is 483,189,753; the exact target is
482,500,000. One small balancing tier, 1.1×, allows an exact integer transfer
without changing the denominator or top-prize odds. Let
`delta = target - raw = -689,753 = 3 + 4×(-172,439)`. Apply these transfers:

- move 3 counts from 1.0× to 1.1×;
- move -172,439 counts from 1.1× to 1.5× (equivalently move 172,439 counts
  back from 1.5× to 1.1×).

The final weights remain strictly decreasing. The highest single weight is
25.32244% of displayed prizes; the largest two sum to 45.3821933%. The table's
median is 1.5×. Exact mean is `193/60 = 3.216666…×`, P90 is 3.6×, and P99 is
19.5×. The full prize/weight pairs and exact results are in
[`BASE_ONLY_RESULTS.md`](BASE_ONLY_RESULTS.md).

## Exact generation order and book event

The book is outcome-authoritative. The frontend animates its route and displays
its payout; it does not choose or recalculate a different outcome.

1. Draw `hit` with exact probability `3/10`; otherwise draw a miss with
   probability `7/10`.
2. Independently draw five prizes from the fixed paytable, one for each outlet.
   Do this for hits and misses alike. Never condition or reroll this row based
   on the hit result, board, outlet, or payout.
3. On a hit, choose `reachedOutlet` uniformly from rows `0..4`. On a miss,
   record `reachedOutlet: null`.
4. Construct the 5×5 board after those draws. A hit board has one simple,
   unambiguous reciprocal-port path from `(2,0)` to `(reachedOutlet,4)`. A miss
   board has one path from the inlet to a non-outlet dead end. Use `I` and `L`
   along the active path; disconnected cells may be empty or decorative pipes.
   Reject any generated board that traces differently from the recorded result.

The event fields are:

```json
{
  "type": "outletResult",
  "hit": true,
  "prizeRow": [20, 10, 11, 22, 22],
  "reachedOutlet": 0,
  "pathCells": [[2,0], [2,1], [1,1], [1,2], [0,2], [0,3], [0,4]],
  "payout": 20
}
```

All prize and payout numbers are integer tenths of the base-wager multiple:
`20` means 2.0×. `prizeRow` must have five positive entries. A hit has outlet
index 0–4 and a path ending at column 4 in that row. A miss has a null outlet
and a path ending at a dead end. `payout` equals `prizeRow[reachedOutlet]` on a
hit and 0 on a miss.

## Frontend and audit validation

The frontend and audit recompute the outcome independently from the board and
row. They must:

1. Validate board dimensions, legal pipe types and rotations, west inlet,
   reciprocal adjacent ports, and path coordinates.
2. Trace from `(2,0)`. Require a single unambiguous stream with no repeated
   active cell. On a hit, require exactly one east outlet and match its row to
   `reachedOutlet`; on a miss, require no reached east outlet and a dead end.
3. Compare the traced ordered cells with `pathCells`.
4. Recompute `payout = prizeRow[reachedOutlet]` on a hit, otherwise 0. Require
   exact equality with the event payout and the final book award after unit
   conversion. Reject any mismatch; do not repair it or silently prefer a field.
5. Validate the prize-row distribution and its independence from hit/miss in
   the generated and optimized books.

Because every outlet prize is positive, `hit` must exactly equal whether the
recomputed payout is nonzero. No player route choice is part of this event.

## Payout-class design and LUT weights

The book library uses payout classes, not enumerated joint prize-row classes.
Each book contains:

- **Payout class**: miss (0x) or one of the ladder prizes (1.0x, 1.5x, 2.0x, ..., 50,000x)
- **Pipe board**: a 5×5 board with a single unambiguous stream ending at the reached outlet (on a hit) or a dead end (on a miss)
- **Displayed 5-prize row**: the reached outlet equals the payout class value; all other outlets (all five on a miss) are decoys drawn independently from the prize distribution at generation time

### Target class probabilities

Let `w_j` be the integer weight of prize `j` from the paytable, with `D = 15,000,000`.
The payout class probabilities are:

```text
P(miss class) = 7/10
P(payout = prize_j class) = (3/10) × (w_j / D)
```

For the 45-prize ladder with weights from [`base_exact.py`](base_exact.py), this gives:
- Miss class: 70.0%
- 1.0x class: 25.32244%
- 1.5x class: 20.05975%
- 2.0x class: 10.54573%
- ... (see full table in [`BASE_ONLY_RESULTS.md`](BASE_ONLY_RESULTS.md))
- 50,000x class: 0.0000667% (1 in 1,500,000 displayed, 1 in 5,000,000 paid)

The LUT weights are per payout class, not per joint prize-row class. The SDK optimizer
assigns integer weights to individual books within each class to hit these target
class probabilities.

### Statistical audit plan

**Chi-square test of decoy prizes per class**:
- For each payout class, collect the observed frequency of each prize value in the decoy positions.
- Compare to the expected distribution from the paytable weights using a chi-square goodness-of-fit test.
- Threshold: χ² < critical value at α = 0.001 with (k-1) degrees of freedom, where k = number of prizes.
- Reject if p-value < 0.001.

**Test displayed-row distribution on hit vs miss**:
- Collect the empirical distribution of prize rows on hits and on misses separately.
- Use a two-sample Kolmogorov-Smirnov test to compare the two distributions.
- Threshold: KS statistic < critical value at α = 0.001.
- Reject if p-value < 0.001 (indicates dependence between hit/miss and row distribution).

**Test reached outlet uniformity**:
- On hits, collect the frequency of each reached outlet (rows 0-4).
- Compare to uniform distribution (20% each) using a chi-square test.
- Threshold: χ² < critical value at α = 0.001 with 4 degrees of freedom.
- Reject if p-value < 0.001.

### Books per class

To ensure the rarest classes have enough different boards and decoy rows:

- **Rarest classes**: 1000x, 5000x, 50000x (display probabilities ~0.01%, 0.001%, 0.000067%)
- **Minimum books per rare class**: 1,000 different books to ensure decoy variety
- **Common classes**: 1.0x, 1.5x, 2.0x (display probabilities 25.3%, 20.1%, 10.5%)
- **Minimum books per common class**: 100 different books (variety less critical due to high frequency)

**Total books per mode estimate**:
- 42 prize classes × 100 books = 4,200 books (common)
- 3 rare classes × 1,000 books = 3,000 books
- 1 miss class × 500 books = 500 books
- **Total: ~7,700 books per mode**

This is operationally practical and provides sufficient statistical power for the audit tests.

## Exact measures and 0.1× rule

Let `X` be one prize drawn at the uniformly reached outlet, `q=3/10`, and `Y`
the round payout multiplier:

```text
P(hit) = P(reach an outlet) = q
P(Y > 0) = q
P(miss) = P(Y = 0) = 7/10
Y = X if hit, otherwise 0
RTP = E[Y] = q × E[X] = 193/200
E[X | hit] = (193/200) / (3/10) = 193/60
Var(Y) = q × E[X²] - (193/200)²
P(50,000× paid) = q × P(50,000× shown at the selected outlet) = 1/5,000,000
```

The 0.1× rule applies to every outlet prize and the payout multiplier. Hit/miss
probabilities, book weights, and event frequencies are rational counts, not
payout amounts. A miss payout is 0.0×; zero is never an outlet prize. Currency
unit rounding remains governed by the existing RGS accounting rules and is not
changed by this design study.
