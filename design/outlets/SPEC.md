# Sewer Surge: East Outlets Redesign (Design Study)

This is a proposed model only. Nothing in this directory changes the live game,
its math, SDK, configuration, books, validation, or RGS contract.

> **Status:** This is the earlier multi-mode exploration. Its zero-prize outlet
> row, bonus modes, and 10,000× cap are superseded for Base by
> [`BASE_GAME_SPEC.md`](BASE_GAME_SPEC.md) and [`BASE_ONLY_RESULTS.md`](BASE_ONLY_RESULTS.md).
> Do not use this file's prize table or base hit-rate model to choose the Base
> table; the current proposal has positive prizes on every outlet and misses only
> when the route ends at a dead end.

## Rules

- The board is 5 rows × 5 columns. Water enters at the west port of row 2.
- Pipe ports before rotation match the existing rules: `I = E/W`, `L = S/E`,
  `T = E/W/S`, and `X = N/E/S/W`. `rotation` is clockwise, 0–3 quarter turns.
- An outlet is the east port of the pipe in column 4 for the corresponding row.
  Pipes connect only when adjacent ports face each other. An open port facing an
  empty cell or the wrong direction is a dead end.
- Every spin independently draws and displays five row prizes from the one fixed
  weighted table below. The prize draw never depends on the board, the flow, a
  scatter, or whether the result wins.
- Base uses one stream. At a T/X it chooses one connected continuation uniformly;
  an east outlet pays its row prize, and a dead end pays zero. It never pays more
  than one outlet.
- Bonus is one feature: exactly 3 natural scatters or Buy Bonus. At each T/X,
  water splits into all connected branches. Every reached east outlet pays its
  displayed prize once. Buy Bonus uses the same board, prize, and flow distribution
  as a natural Bonus.
- Super is one feature: 4 or 5 natural scatters or Super Buy. The stream splits
  more often and more widely than in Bonus. A multiplier valve may be present on
  a pipe; each branch multiplies through every valve it actually passes. For
  each outlet, multiply all valve factors on that outlet's selected path, then
  multiply by that row's displayed prize. Super Buy uses the same distribution as
  natural Super.
- The total across all reached outlets is capped at 10,000× the base-game wager
  per round. The cap is applied after summing the outlet awards. Ante awards scale
  with its 3× wager before this cap. Buy prices are 100× and 500× base wager.
- All prizes and payouts are integer tenths of x. Valve factors are integers, so
  products and sums remain in 0.1× increments; the payout granularity does not
  block this design. The cap is exactly 100,000 tenths of x.
- Target RTP is 96.5% for each mode, measured against that mode's total cost:
  Base 1×, Ante 3×, Buy Bonus 100×, Super Buy 500×. Ante's 3× cost scales its
  award; its 3-scatter and 4–5-scatter trigger probabilities are 5× base rates.

## Concrete design parameters tested

Prize values are shown in x. The integer weights sum to 100,000.

| Prize | Weight | Probability |
|---:|---:|---:|
| 0× | 27,805 | 27.805% |
| 2× | 2,000 | 2.000% |
| 5× | 2,000 | 2.000% |
| 10× | 18,200 | 18.200% |
| 20× | 15,000 | 15.000% |
| 30× | 10,000 | 10.000% |
| 40× | 8,000 | 8.000% |
| 50× | 7,000 | 7.000% |
| 100× | 5,000 | 5.000% |
| 200× | 4,000 | 4.000% |
| 500× | 895 | 0.895% |
| 1,000× | 100 | 0.100% |

The exact prize mean is 32.175×. The flow constructor always includes one outlet.
In Bonus, each of the four additional outlets is connected independently with
probability 0.499805749806 (2.999222999 expected total outlets). This is solved
from `(1 + 4p) × 32.175 = 96.5`, rather than fitted to simulation output. In Super
the additional-outlet probability is 0.85 (4.4 expected outlets), so it branches
more often and more widely than Bonus. Natural and bought versions of each tier
share the same feature distribution.

For each reached Super outlet path, a valve is placed on that outlet pipe with
probability 0.749940194838. If present, its type weights (out of 10,000) are x2:
4,236; x3: 2,000; x5: 2,000; x10: 1,764. The no-valve outcome has factor 1. A
stream multiplies through every valve it passes after a split; separate branches
accrue their own products. The placement frequency makes the theoretical
uncapped Super feature mean 482.5× with this table and the 4.4 expected outlets.
The flow function supports multiple valves on any path.

Natural trigger schedule per spin:

| Mode | Exactly 3 scatters / Bonus | 4 scatters / Super | 5 scatters / Super |
|---|---:|---:|---:|
| Base | 0.100% | 0.008% | 0.002% |
| Ante | 0.500% | 0.040% | 0.010% |

Thus Bonus probability is 0.1% Base / 0.5% Ante; Super is 0.01% Base / 0.05%
Ante. Purchased features force the same corresponding feature distribution.

The base/ante ordinary-route frequencies in the Monte Carlo are analytically
derived to offset the natural-feature EV at the target RTP, rather than manually
adjusted after seeing sample output. The candidate values and observed sample
results are printed by `python design/outlets/feasibility.py`.

## Data model

Canonical design-study round record (all amounts in tenths of base-wager x unless
the field explicitly says otherwise):

```json
{
  "mode": "base | ante | buy_bonus | super_buy",
  "wagerCostBaseX": 1,
  "scatterCount": 0,
  "feature": "none | bonus | super",
  "prizeRowTenthsX": [0, 100, 200, 300, 400],
  "board": {
    "rows": 5,
    "columns": 5,
    "inlet": {"row": 2, "column": 0, "side": "W"},
    "cells": [[null, {"type": "L", "rotation": 1, "valve": 1}]],
    "outlets": [{"row": 0, "column": 4, "side": "E"}]
  },
  "flow": {"reachedOutletRows": [0], "illustrativeOnly": true},
  "payoutTenthsX": 0
}
```

`cells` is exactly 5×5 in an actual record; null denotes an empty cell. `type` is
I/L/T/X, `rotation` is 0–3 clockwise turns, and `valve` is an integer product
factor (1 means no valve). `prizeRowTenthsX` always has five nonnegative integer
entries and is sampled before and independently of board resolution. The record
does not accept `routeChoice`: the player never selects a branch. Scatter count
determines the feature tier, not the payout. The board/flow can illustrate a
book result but must not override its authoritative payout.

Suggested event sequence (names are design vocabulary, not a change to the live
RGS contract):

```json
{"type":"outletPrizes","prizesTenthsXByRow":[20,50,100,10000,0]}
{"type":"sewerBoard","inlet":{"row":2,"side":"W"},"cells":"5x5 I/L/T/X cells"}
{"type":"sewerFeature","feature":"bonus","scatterCount":3}
{"type":"sewerFlow","reachedOutletRows":[0,3],"valveProductsByRow":{"0":1,"3":1}}
{"type":"sewerAward","payoutTenthsX":10020}
{"type":"setTotalWin","payoutTenthsX":10020}
{"type":"finalWin","payoutTenthsX":10020}
```

There is no feature event for 0–2 scatters. `sewerFlow` is derived from the board
and contains no player choice. `outletPrizes` is drawn regardless of flow or win.
All payout-bearing events must agree after applying the cap.

## Pure payout computation

`flow.py` models port rotation, reciprocal adjacency, west-inlet tracing,
single-stream junction choice, split reachability, path valve products, and the
total cap. `compute_payout(board, prizes_by_row, split, cap)` returns integer
tenths of x and a flow trace. For a split feature, the simulator chooses a
deterministic shortest path for each reached outlet (N/E/S/W tie-break) to define
which valves multiply on that outlet. A production event should serialize those
same path semantics or use a strictly acyclic board so there is no ambiguity.

Let `R` be the reached outlet rows, `P[r]` the independent row prize, and `V[r]`
the product of valve factors along the defined path (1 in Base/Bonus):

```text
raw_round_payout_tenths = sum(P[r] * V[r] for r in R)
round_payout_tenths = min(raw_round_payout_tenths, 100_000)
Base:       R = the one outlet selected by the single stream, or empty on dead end
Bonus/Super: R = every east outlet reachable through reciprocal ports
```

The functions in `flow.py` are pure apart from the explicit RNG passed to
single-stream branch selection and board generation. They do not access files,
network, game state, or external services.

## Feasibility interpretation

The proposal's uncapped expectations are Bonus = 96.5× and Super = 482.5×. That
gives purchased RTPs of 96.5% at 100× and 96.5% at 500×. Natural rates are low
enough that the base and ante ordinary-route frequency can fill the remainder to
96.5% in expectation. A 500× prize with a 10× valve reaches 5,000× on one outlet;
two such outlets reach the 10,000× round cap. Thus the cap is mathematically
reachable. It is not promised on any spin. Monte Carlo output reports the sampled
hit, volatility, and cap frequency; zero observed caps in a finite sample must be
reported as not observed, not as impossible.

## Design risks

- **Near-miss/decoy presentation:** prize indicators must be drawn independently
  and never imply that a near outlet almost paid. Avoid emphasizing unreachable
  high values as if they were skill targets.
- **Zero-paying features:** the 0× prize has 30.105% weight. A feature can reach
  outlets and still pay zero, especially when all reached rows draw zero. Rules
  and feature-entry UI must not imply a guaranteed win.
- **Buy-price honesty:** disclose 100× / 500× cost before confirmation, show the
  same feature rules as natural triggers, and don't suggest the purchase improves
  a particular prize draw. Recheck RTP from exact generated books before launch.
- **Board/payout disagreement:** the board is illustrative. If UI animates a route
  or valve product that differs from the payout function/book, users may infer a
  false result. Define tie-breaking, cycles, valve application, rounding, and cap
  order in the event contract and test every serialized board against it.
- **Cap units:** this study assumes 10,000× of the base-game wager in every mode.
  If the intended cap is 10,000× each mode's total wager, Ante and bought modes
  need different cap semantics and the feasibility result changes.
- **Sampling error:** one million rounds is a feasibility sample, not an audit.
  Heavy-tail Super outcomes make observed RTP/max-win frequency noisy. Validate
  final distributions with exact enumeration/large books and the production math
  audit before making a compliance or RTP claim.
