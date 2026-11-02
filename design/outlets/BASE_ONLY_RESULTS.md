# Positive-only base-game exact results

Every outlet prize is positive. Misses are caused only by the hit/miss draw. The candidate reach probabilities and hit rates are 30%, 15%, and 5%; every row has exact RTP 96.5%.

The 12 rows are three candidate hit rates times Variant A at 1-in-5M, 1-in-10M, and 1-in-20M top-prize paid odds plus Variant B. Variant A denominator is 60,000,000; Variant B is 300,000. The 1,000x weight is 600 for A and 3 for B.

For per-outlet top display probability p and hit probability q, paid probability at one specified outlet is q*p/5, and paid probability per spin across the five possible reached outlets is q*p. Any-row display probabilities are exact 1-(1-p)^5; reciprocal frequencies below are approximate decimal summaries. All model arithmetic uses Fraction; standard deviation and displayed reciprocal summaries are decimal output.

The 0.1x grid applies to prize and payout multipliers. A miss payout is 0.0x; no outlet table contains a zero prize.

## Full output

Command: `python base_exact.py`

```text
MODEL: positive-only prize rows; miss occurs only when route misses
VARIANT_A_DENOMINATOR=60,000,000; VARIANT_B_DENOMINATOR=300,000
All calculations exact Fractions; SD is sqrt(exact variance).
variant | table | hit rate | mean prize on hit | RTP | volatility SD | prize-by-weight pairs | top | displayed per outlet | displayed anywhere in row | paid per outlet | paid per spin | top RTP contribution | row has prize >=100x | 0.1x
A_5000000 | frequent_small | 3/10 | 193/60 | 193/200 | 22.474216488 | 31/10x:15979520; 16/5x:44019840; 1000x:600; 50000x:40 | 50000x | 1 in 1,500,000 | 0.000333333% (about 1 in 300,000.400) | 1 in 25,000,000 | 1 in 5,000,000 | 1/100 | 1pp | 0.005333220% (about 1 in 18,750.400) | YES
A_10000000 | frequent_small | 3/10 | 193/60 | 193/200 | 15.972535984 | 31/10x:5980160; 16/5x:54019220; 1000x:600; 50000x:20 | 50000x | 1 in 3,000,000 | 0.000166667% (about 1 in 600,000.400) | 1 in 50,000,000 | 1 in 10,000,000 | 1/200 | 1/2pp | 0.005166560% (about 1 in 19,355.239) | YES
A_20000000 | frequent_small | 3/10 | 193/60 | 193/200 | 11.407789236 | 31/10x:980480; 16/5x:59018910; 1000x:600; 50000x:10 | 50000x | 1 in 6,000,000 | 0.000083333% (about 1 in 1,200,000.400) | 1 in 100,000,000 | 1 in 20,000,000 | 1/400 | 1/4pp | 0.005083230% (about 1 in 19,672.531) | YES
B | frequent_small | 3/10 | 193/60 | 193/200 | 2.270199700 | 16/5x:279901; 33/10x:20096; 1000x:3 | 1000x | 1 in 100,000 | 0.004999900% (about 1 in 20,000.400) | about 1 in 1,666,666.667 | about 1 in 333,333.333 | 3/1000 | 3/10pp | 0.004999900% (about 1 in 20,000.400) | YES
A_5000000 | medium | 3/20 | 193/30 | 193/200 | 22.508449381 | 63/10x:25956480; 32/5x:34042840; 1000x:600; 50000x:80 | 50000x | 1 in 750,000 | 0.000666665% (about 1 in 150,000.400) | 1 in 25,000,000 | 1 in 5,000,000 | 1/100 | 1pp | 0.005666538% (about 1 in 17,647.459) | YES
A_10000000 | medium | 3/20 | 193/30 | 193/200 | 16.021666253 | 63/10x:5959040; 32/5x:54040320; 1000x:600; 50000x:40 | 50000x | 1 in 1,500,000 | 0.000333333% (about 1 in 300,000.400) | 1 in 50,000,000 | 1 in 10,000,000 | 1/200 | 1/2pp | 0.005333220% (about 1 in 18,750.400) | YES
A_20000000 | medium | 3/20 | 193/30 | 193/200 | 11.477183430 | 32/5x:55959700; 13/2x:4039680; 1000x:600; 50000x:20 | 50000x | 1 in 3,000,000 | 0.000166667% (about 1 in 600,000.400) | 1 in 100,000,000 | 1 in 20,000,000 | 1/400 | 1/4pp | 0.005166560% (about 1 in 19,355.239) | YES
B | medium | 3/20 | 193/30 | 193/200 | 2.599612933 | 32/5x:229805; 13/2x:70192; 1000x:3 | 1000x | 1 in 100,000 | 0.004999900% (about 1 in 20,000.400) | about 1 in 3,333,333.333 | about 1 in 666,666.667 | 3/2000 | 3/20pp | 0.004999900% (about 1 in 20,000.400) | YES
A_5000000 | high_volatility | 1/20 | 193/10 | 193/200 | 22.755009976 | 19x:5839560; 191/10x:54159600; 1000x:600; 50000x:240 | 50000x | 1 in 250,000 | 0.001999984% (about 1 in 50,000.400) | 1 in 25,000,000 | 1 in 5,000,000 | 1/100 | 1pp | 0.006999804% (about 1 in 14,286.114) | YES
A_10000000 | high_volatility | 1/20 | 193/10 | 193/200 | 16.370151039 | 191/10x:5861760; 96/5x:54137520; 1000x:600; 50000x:120 | 50000x | 1 in 500,000 | 0.000999996% (about 1 in 100,000.400) | 1 in 50,000,000 | 1 in 10,000,000 | 1/200 | 1/2pp | 0.005999856% (about 1 in 16,667.067) | YES
A_20000000 | high_volatility | 1/20 | 193/10 | 193/200 | 11.961520756 | 96/5x:35872620; 193/10x:24126720; 1000x:600; 50000x:60 | 50000x | 1 in 1,000,000 | 0.000499999% (about 1 in 200,000.400) | 1 in 100,000,000 | 1 in 20,000,000 | 1/400 | 1/4pp | 0.005499879% (about 1 in 18,182.218) | YES
B | high_volatility | 1/20 | 193/10 | 193/200 | 4.263122128 | 96/5x:29421; 193/10x:270576; 1000x:3 | 1000x | 1 in 100,000 | 0.004999900% (about 1 in 20,000.400) | 1 in 10,000,000 | 1 in 2,000,000 | 1/2000 | 1/20pp | 0.004999900% (about 1 in 20,000.400) | YES
```
