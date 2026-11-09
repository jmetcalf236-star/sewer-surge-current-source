"""Compute integer LUT weights with largest-remainder rounding to sum to 2^50.
"""

from fractions import Fraction

# Class probabilities and book counts
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)
BOOKS = (100000, 20000, 20000, 20000, 10000, 5000, 3000, 2000, 1500, 1200, 1000, 1000, 1000, 1000)
MISS_BOOKS = 100000

# Scaling factor
SCALE_2_50 = int(2 ** 50)

print("=" * 120)
print("LUT WEIGHT CALCULATION - LARGEST-REMAINDER ROUNDING")
print("=" * 120)
print()
print(f"SCALE_2_50 = {SCALE_2_50} ≈ {SCALE_2_50:.3e}")
print()

# Calculate per-book probabilities
P_MISS = Fraction(7, 10)
PER_BOOK_PROBS = [P_MISS / MISS_BOOKS]

for weight, books in zip(WEIGHTS, BOOKS):
    p_class = Fraction(3, 10) * Fraction(weight, D)
    per_book_prob = p_class / books
    PER_BOOK_PROBS.append(per_book_prob)

# Total books
TOTAL_BOOKS = MISS_BOOKS + sum(BOOKS)

# Calculate target weights for each book
target_weights = []
for per_book_prob in PER_BOOK_PROBS:
    target_weight = per_book_prob * SCALE_2_50
    target_weights.append(target_weight)

# Largest-remainder rounding
floor_weights = [int(w) for w in target_weights]
remainders = [w - int(w) for w in target_weights]

total_floor = sum(floor_weights)
remainder_budget = SCALE_2_50 - total_floor

# Sort by remainder (largest first) and allocate remainder budget
indices = list(range(len(remainders)))
indices.sort(key=lambda i: remainders[i], reverse=True)

final_weights = floor_weights.copy()
for i in indices[:remainder_budget]:
    final_weights[i] += 1

# Verify sum
total_final = sum(final_weights)
print(f"Total floor weights: {total_floor}")
print(f"Remainder budget: {remainder_budget}")
print(f"Total final weights: {total_final}")
print(f"Match 2^50: {total_final == SCALE_2_50}")
print()

# Calculate realized RTP
realized_rtp = Fraction(0, 1)
# MISS class contributes 0
# Prize classes
for i, (prize, final_weight, per_book_prob) in enumerate(zip(PRIZES, final_weights[1:], PER_BOOK_PROBS[1:])):
    realized_prob = Fraction(final_weight, SCALE_2_50)
    realized_rtp += realized_prob * Fraction(prize, 10)

target_rtp = Fraction(193, 200)
rtp_error = realized_rtp - target_rtp

print(f"Target RTP: {float(target_rtp):.10f}")
print(f"Realized RTP: {float(realized_rtp):.10f}")
print(f"RTP Error: {float(rtp_error):.10e}")
print()

# Output CSV format
print("=" * 120)
print("CSV OUTPUT FORMAT (sim_id, round_probability, payout_multiplier)")
print("=" * 120)
print()

sim_id = 0
# MISS books
for i in range(MISS_BOOKS):
    weight = final_weights[0]
    payout = 0
    print(f"{sim_id},{weight},{payout}")
    sim_id += 1

# Prize class books
for class_idx, (prize, books) in enumerate(zip(PRIZES, BOOKS)):
    weight = final_weights[class_idx + 1]
    payout = prize  # in tenths of x
    for i in range(books):
        print(f"{sim_id},{weight},{payout}")
        sim_id += 1

print()
print(f"Total simulations: {sim_id}")
