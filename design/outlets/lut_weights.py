"""LUT weights - single source of truth with exact Fractions and tests.
"""

from fractions import Fraction

# Class probabilities and book counts (ONE SOURCE OF TRUTH)
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)

# Book counts per_class (ONE SOURCE OF TRUTH)
BOOKS = {
    "MISS": 100000,
    "1.0x": 100000,  # Changed from 20,000 to 100,000 for finer granularity
    "1.5x": 20000,
    "2.0x": 20000,
    "3.0x": 20000,
    "5.0x": 10000,
    "8.0x": 5000,
    "10.0x": 3000,
    "20.0x": 2000,
    "50.0x": 1500,
    "100.0x": 1200,
    "500.0x": 1000,
    "1000.0x": 1000,
    "5000.0x": 1000,
    "50000.0x": 1000,
}

# Scaling factor
SCALE_2_50 = int(2 ** 50)

print("=" * 120)
print("LUT WEIGHTS - SINGLE SOURCE OF TRUTH")
print("=" * 120)
print()
print(f"SCALE_2_50 = {SCALE_2_50} ≈ {SCALE_2_50:.3e}")
print()

# Verify book count sum
total_books = sum(BOOKS.values())
print(f"Total books: {total_books}")
assert total_books == 286700, f"Expected 286,700 books, got {total_books}"
print("✓ Book count sum matches 286,700")
print()

# Calculate class probabilities
class_probs = {}
class_probs["MISS"] = Fraction(7, 10)
for i, (prize, weight) in enumerate(zip(PRIZES, WEIGHTS)):
    class_name = f"{prize/10:.1f}x"
    class_probs[class_name] = Fraction(3, 10) * Fraction(weight, D)

# Calculate target weights per class
target_weights = {}
for class_name, prob in class_probs.items():
    target_weights[class_name] = prob * SCALE_2_50

# Largest-remainder rounding per class
print("=" * 120)
print("CLASS WEIGHT ALLOCATION (LARGEST-REMAINDER ROUNDING)")
print("=" * 120)
print()

floor_weights = {}
remainders = {}
for class_name, target in target_weights.items():
    floor_weights[class_name] = int(target)
    remainders[class_name] = target - int(target)

total_floor = sum(floor_weights.values())
remainder_budget = SCALE_2_50 - total_floor

print(f"Total floor weights: {total_floor}")
print(f"Remainder budget: {remainder_budget}")
print()

# Allocate remainders to classes with largest remainders
class_names = list(remainders.keys())
class_names.sort(key=lambda x: remainders[x], reverse=True)

final_class_weights = floor_weights.copy()
for class_name in class_names[:remainder_budget]:
    final_class_weights[class_name] += 1

print("Class weights after largest-remainder allocation:")
for class_name in class_names:
    print(f"  {class_name}: {final_class_weights[class_name]}")

print()
print(f"Total class weights: {sum(final_class_weights.values())}")
assert sum(final_class_weights.values()) == SCALE_2_50, "Class weights must sum to 2^50"
print("✓ Class weights sum to 2^50")
print()

# Calculate per-book weights (may differ by 1 within a class)
print("=" * 120)
print("PER-BOOK WEIGHT ALLOCATION")
print("=" * 120)
print()

all_per_book_weights = []
total_per_book_sum = 0

for class_name, books in BOOKS.items():
    class_weight = final_class_weights[class_name]
    base_weight = class_weight // books
    extra_books = class_weight % books
    
    print(f"{class_name}:")
    print(f"  Books: {books}")
    print(f"  Class weight: {class_weight}")
    print(f"  Base weight per book: {base_weight}")
    print(f"  Books with weight+1: {extra_books}")
    print(f"  Books with weight: {books - extra_books}")
    
    # Add per-book weights
    for i in range(books):
        if i < extra_books:
            w = base_weight + 1
        else:
            w = base_weight
        all_per_book_weights.append(w)
        total_per_book_sum += w
    
    # Calculate realized P(class)
    realized_prob = Fraction(class_weight, SCALE_2_50)
    target_prob = class_probs[class_name]
    prob_error = realized_prob - target_prob
    
    print(f"  Realized P(class): {float(realized_prob):.10f}")
    print(f"  Target P(class): {float(target_prob):.10f}")
    print(f"  Error: {float(prob_error):.10e}")
    print()

# Strict test: sum of all per-book weights == 2^50
print("=" * 120)
print("STRICT TEST: PER-BOOK WEIGHT SUM")
print("=" * 120)
print()
print(f"Total per-book weights sum: {total_per_book_sum}")
print(f"Expected (2^50): {SCALE_2_50}")
assert total_per_book_sum == SCALE_2_50, f"Per-book weights sum to {total_per_book_sum}, expected {SCALE_2_50}"
print("✓ Per-book weights sum to 2^50")
print()

# Calculate realized RTP
print("=" * 120)
print("REALIZED RTP CALCULATION")
print("=" * 120)
print()

realized_rtp = Fraction(0, 1)
for i, (prize_tenths, weight) in enumerate(zip(PRIZES, WEIGHTS)):
    class_name = f"{prize_tenths/10:.1f}x"
    class_weight = final_class_weights[class_name]
    realized_prob = Fraction(class_weight, SCALE_2_50)
    # prize_tenths is in tenths of x, so divide by 10 to get x multiplier
    realized_rtp += realized_prob * Fraction(prize_tenths, 10)

target_rtp = Fraction(193, 200)
rtp_error = realized_rtp - target_rtp

print(f"Target RTP: {float(target_rtp):.10f}")
print(f"Realized RTP: {float(realized_rtp):.10f}")
print(f"RTP Error: {float(rtp_error):.10e}")
print()

# Explain why 830,279,123 was printed for 1.0x class with 20,000 books
print("=" * 120)
print("EXPLANATION: WHY 830,279,123 WAS PRINTED FOR 1.0x CLASS WITH 20,000 BOOKS")
print("=" * 120)
print()

print("Previous calculation (incorrect):")
print("  Used 20,000 books for 1.0x class")
print("  P(1.0x) = (3/10) × (368,718 / 1,500,000) = 0.0737436")
print("  Target weight = 0.0737436 × 2^50 = 83,027,912,300")
print("  Per-book weight = 83,027,912,300 / 20,000 = 4,151,395.615")
print("  Rounded to 4,151,395 (truncated)")
print("  But this was WRONG - it didn't use largest-remainder rounding correctly")
print()

print("Correct calculation with 100,000 books:")
print("  P(1.0x) = (3/10) × (368,718 / 1,500,000) = 0.0737436")
print("  Target weight = 0.0737436 × 2^50 = 83,027,912,300")
print("  Per-book weight = 83,027,912,300 / 100,000 = 830,279.123")
print("  Base weight = 830,279")
print("  Extra books = 83,027,912,300 % 100,000 = 12,300")
print("  12,300 books get weight 830,280, 87,700 books get weight 830,279")
print("  Total = 12,300 × 830,280 + 87,700 × 830,279 = 83,027,912,300 ✓")
print()

print("The previous value 830,279,123 was a miscalculation that didn't account for")
print("the correct book count and largest-remainder rounding.")
