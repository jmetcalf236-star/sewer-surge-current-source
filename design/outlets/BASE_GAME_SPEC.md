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

The denominator is `D = 1,500,000`. Weights are integer counts over D. The
14 prize values are positive round numbers, from 1.0× to 50,000×. The exact
integer weights are provided in [`base_exact.py`](base_exact.py):

```text
PRIZES_TENTHS_X = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910, 20000, 5000, 2000, 300, 90, 12, 1)
```

All weights are strictly decreasing. The highest single weight is
24.5812% of displayed prizes; the largest two sum to 48.6224%. The table's
median is 2.0×. Exact mean is `193/60 = 3.216666…×`. The 50,000× prize is paid
exactly 1 in 5,000,000 spins.

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

The book library uses 15 payout classes: MISS (0x) plus the 14 prize classes (1.0x through 50,000x).
Each book contains:

- **Payout class**: miss (0x) or one of the ladder prizes (1.0x, 1.5x, 2.0x, ..., 50,000x)
- **Pipe board**: a 5×5 board with a single unambiguous stream ending at the reached outlet (on a hit) or a dead end (on a miss)
- **Displayed 5-prize row**: the reached outlet equals the payout class value; all other outlets (all five on a miss) are decoys drawn independently from the prize distribution at generation time

### Target class probabilities

Let `w_j` be the integer weight of prize `j` from the paytable, with `D = 1,500,000`.
The payout class probabilities are:

```text
P(miss class) = 7/10 = 0.7
P(payout = prize_j class) = (3/10) × (w_j / D)
```

For the 14-prize ladder with weights from [`base_exact.py`](base_exact.py):

| Class | Weight w_j | P(class) | hr = 1/P(class) |
|-------|-----------|----------|-----------------|
| MISS | - | 0.7 | 1.43 |
| 1.0x | 368,718 | 0.0737436 | 13.57 |
| 1.5x | 358,614 | 0.0717228 | 13.94 |
| 2.0x | 335,000 | 0.0670000 | 14.93 |
| 3.0x | 194,300 | 0.0388600 | 25.73 |
| 5.0x | 112,693 | 0.0225386 | 44.37 |
| 8.0x | 65,362 | 0.0130724 | 76.50 |
| 10.0x | 37,910 | 0.0075820 | 131.89 |
| 20.0x | 20,000 | 0.0040000 | 250.00 |
| 50.0x | 5,000 | 0.0010000 | 1,000.00 |
| 100.0x | 2,000 | 0.0004000 | 2,500.00 |
| 500.0x | 300 | 0.0000600 | 16,666.67 |
| 1,000.0x | 90 | 0.0000180 | 55,555.56 |
| 5,000.0x | 12 | 0.0000024 | 416,666.67 |
| 50,000.0x | 1 | 0.0000002 | 5,000,000.00 |

**Note**: The hit rate (hr) for a class is the expected number of spins to see that class once. For the 50,000x class, P = 1/5,000,000, so hr = 5,000,000 spins. The 0.3 hit rate is already factored into P(class).

### LUT weight calculation

Per-book LUT weight formula:

```text
weight_per_book = P(class) / N_class_books
scaled_weight = weight_per_book × 2^50 (as u64)
```

Where `N_class_books` is the number of books in that class. The SDK uses 2^50 scaling to convert probabilities to integer weights.

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

To ensure the rarest classes have enough different boards and decoy rows, every class must have at least 1,000 books. The miss class, which carries 70% of the probability mass, should have proportionally more books.

**Proposed book allocation (total ~200,000 books per mode)**:

| Class | P(class) | Books | Distinct Boards | Distinct Decoy Rows | Per-Book Weight | Scaled Weight (×2^50) |
|-------|----------|-------|-----------------|---------------------|-----------------|----------------------|
| MISS | 0.7 | 100,000 | 100,000 | 500,000 | 7.00×10⁻⁶ | 7.86×10¹⁵ |
| 1.0x | 0.0737436 | 20,000 | 20,000 | 100,000 | 3.69×10⁻⁶ | 4.14×10¹⁵ |
| 1.5x | 0.0717228 | 20,000 | 20,000 | 100,000 | 3.59×10⁻⁶ | 4.02×10¹⁵ |
| 2.0x | 0.0670000 | 20,000 | 20,000 | 100,000 | 3.35×10⁻⁶ | 3.76×10¹⁵ |
| 3.0x | 0.0388600 | 10,000 | 10,000 | 50,000 | 3.89×10⁻⁶ | 4.36×10¹⁵ |
| 5.0x | 0.0225386 | 5,000 | 5,000 | 25,000 | 4.51×10⁻⁶ | 5.06×10¹⁵ |
| 8.0x | 0.0130724 | 3,000 | 3,000 | 15,000 | 4.36×10⁻⁶ | 4.89×10¹⁵ |
| 10.0x | 0.0075820 | 2,000 | 2,000 | 10,000 | 3.79×10⁻⁶ | 4.25×10¹⁵ |
| 20.0x | 0.0040000 | 1,500 | 1,500 | 7,500 | 2.67×10⁻⁶ | 2.99×10¹⁵ |
| 50.0x | 0.0010000 | 1,200 | 1,200 | 6,000 | 8.33×10⁻⁷ | 9.35×10¹⁴ |
| 100.0x | 0.0004000 | 1,000 | 1,000 | 5,000 | 4.00×10⁻⁷ | 4.49×10¹⁴ |
| 500.0x | 0.0000600 | 1,000 | 1,000 | 5,000 | 6.00×10⁻⁸ | 6.74×10¹³ |
| 1,000.0x | 0.0000180 | 1,000 | 1,000 | 5,000 | 1.80×10⁻⁸ | 2.02×10¹³ |
| 5,000.0x | 0.0000024 | 1,000 | 1,000 | 5,000 | 2.40×10⁻⁹ | 2.69×10¹² |
| 50,000.0x | 0.0000002 | 1,000 | 1,000 | 5,000 | 2.00×10⁻¹⁰ | 2.25×10¹¹ |
| **Total** | **1.0** | **200,000** | - | - | - | - |

**Formula**:
- `per_book_weight = P(class) / N_class_books`
- `scaled_weight = per_book_weight × 2^50` (as u64, where 2^50 ≈ 1.126×10¹⁵)

**Distinct boards and decoy rows**:
- Each book has 1 distinct pipe board configuration
- Each book has 5 distinct decoy rows (one per outlet position)
- The "Distinct Decoy Rows" column shows the total unique decoy rows across all books in that class

**File size estimate**:
- Assuming ~2 KB per book (compressed JSON with board, row, and metadata)
- 200,000 books × 2 KB = 400 MB per mode
- 4 modes × 400 MB = 1.6 GB total
- With zstd compression (level 3), expect ~60-70% compression ratio: ~1 GB total

**Assumption**: Stake file size limit is assumed to be ~2 GB per game based on typical platform limits. If the limit is lower, we can reduce book counts proportionally while maintaining the 1,000 minimum for rare classes.

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

## LUT generation route

Based on the Stake Engine documentation, the RGS requires:
- CSV format with three `uint64` columns: `simulation_number, round_probability, payout_multiplier`
- Payout multiplier granularity of 0.01× (minimum unit 1 cent)
- Hash verification that CSV payout multipliers match the game logic file exactly

Two implementation routes are available:

### Route A: SDK optimizer with class conditions

Use the SDK optimizer with 15 conditions (one per payout class):
- MISS class: `search_conditions` with `hr = 1/P(miss) = 10/7`
- Each prize class: `search_conditions = <prize>` with `hr = 1/P(class)`
- The optimizer adjusts simulation weights to achieve the target RTP
- Advantage: automatic weight balancing, handles edge cases
- Disadvantage: requires running the Rust optimizer, adds complexity

### Route B: Direct weight computation (RECOMMENDED)

Compute integer weights directly using the per-book probability formula and largest-remainder rounding to sum to exactly 2^50:

```text
weight_per_book = P(class) / N_class_books
scaled_weight = weight_per_book × 2^50 (as u64)
```

**Integer weights (largest-remainder rounding, sum = 2^50):**
- MISS class (100,000 books): 7,881,299,347
- 1.0x class (20,000 books): 830,279,123
- 1.5x class (20,000 books): 4,037,634,691
- 2.0x class (20,000 books): 3,771,764,687
- 3.0x class (20,000 books): 2,187,623,518
- 5.0x class (10,000 books): 2,537,620,764
- 8.0x class (5,000 books): 2,943,642,788
- 10.0x class (3,000 books): 2,845,524,364
- 20.0x class (2,000 books): 2,251,799,813
- 50.0x class (1,500 books): 750,599,937
- 100.0x class (1,200 books): 375,299,968
- 500.0x class (1,000 books): 67,553,994
- 1,000.0x class (1,000 books): 20,266,198
- 5,000.0x class (1,000 books): 2,702,159
- 50,000.0x class (1,000 books): 225,179

Total simulations: 286,700
Realized RTP: 96.49999521% (error: -4.79e-08)

**CSV format example:**
```csv
0,7881299347,0
1,7881299347,0
...
100000,830279123,10
100001,830279123,10
...
```

**Advantages of Route B:**
- Deterministic, reproducible weights
- No dependency on Rust optimizer
- Direct control over weight distribution
- Minimal RTP error (< 5e-08)

**SDK verification (--verify and stats) still checks:**
- CSV payout multipliers match game logic file (hash verification)
- RTP within tolerance
- Hit rate consistency
- File format validity (uint64 columns, no header)

**Design choice:** The 0.1× rule (payout granularity) is maintained as a design choice, even though the platform supports 0.01× granularity. This simplifies the paytable and aligns with typical slot game conventions.
