"""Decoy correlation check - conditional probabilities of decoy prizes given payout class.
"""

from fractions import Fraction

# Class probabilities and book counts (from lut_weights.py)
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)

BOOKS = {
    "MISS": 100000,
    "1.0x": 100000,
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

# Per-book weights (from lut_weights.py output)
PER_BOOK_WEIGHTS = {
    "MISS": 7881299347,
    "1.0x": 830279123,
    "1.5x": 4037634691,
    "2.0x": 3771764687,
    "3.0x": 2187623518,
    "5.0x": 2537620764,
    "8.0x": 2943642788,
    "10.0x": 2845524364,
    "20.0x": 2251799813,
    "50.0x": 750599937,
    "100.0x": 375299968,
    "500.0x": 67553994,
    "1000.0x": 20266198,
    "5000.0x": 2702159,
    "50000.0x": 225179,
}

# Tail prizes and their per-outlet display probabilities (weight / D)
TAIL_PRIZES = [500, 1000, 5000, 50000]  # in tenths: 5000, 10000, 50000, 500000
TAIL_WEIGHTS = [300, 90, 12, 1]
TAIL_PROBS = [Fraction(w, D) for w in TAIL_WEIGHTS]

# Stratified allocation from redo_tail_decoy_v2.py
# Using finest classes first for rarest decoys
STRATIFIED_ALLOCATION = {
    500: {
        "MISS": 0,
        "50000.0x": 1000,
        "5000.0x": 1000,
        "1000.0x": 1000,
        "500.0x": 1000,
        "100.0x": 463,
    },
    1000: {
        "MISS": 0,
        "50000.0x": 1000,
        "5000.0x": 1000,
        "1000.0x": 1000,
        "500.0x": 831,
    },
    5000: {
        "MISS": 0,
        "50000.0x": 1000,
        "5000.0x": 1000,
        "1000.0x": 377,
    },
    50000: {
        "MISS": 0,
        "50000.0x": 1000,
        "5000.0x": 243,
    },
}

print("=" * 120)
print("DECOY CORRELATION CHECK")
print("=" * 120)
print()
print("Conditional probability: P(decoy prize shown | payout class)")
print("Using LUT-weighted frequencies (not book counts)")
print()

# Calculate P(class) from LUT weights
SCALE_2_50 = int(2 ** 50)
class_lut_weights = {}
for class_name, per_book_weight in PER_BOOK_WEIGHTS.items():
    class_lut_weights[class_name] = per_book_weight * BOOKS[class_name]

total_lut_weight = sum(class_lut_weights.values())
class_probs = {name: Fraction(weight, total_lut_weight) for name, weight in class_lut_weights.items()}

print("Class probabilities (from LUT weights):")
for class_name, prob in sorted(class_probs.items()):
    print(f"  {class_name}: {float(prob):.10f}")
print()

# For each tail prize, calculate conditional probabilities
for tail_prize, allocation in STRATIFIED_ALLOCATION.items():
    print(f"{tail_prize}x decoy:")
    print()
    
    # Calculate total weight of books carrying this decoy
    total_decoy_weight = Fraction(0, 1)
    for class_name, books_with_decoy in allocation.items():
        if books_with_decoy > 0:
            total_decoy_weight += books_with_decoy * PER_BOOK_WEIGHTS[class_name]
    
    print(f"  Total LUT weight of books with {tail_prize}x decoy: {float(total_decoy_weight):.10e}")
    print()
    
    # Calculate P(decoy | class) for each class
    print(f"  P({tail_prize}x decoy | class):")
    for class_name in sorted(PER_BOOK_WEIGHTS.keys()):
        class_weight = class_lut_weights[class_name]
        books_with_decoy = allocation.get(class_name, 0)
        
        if books_with_decoy > 0:
            decoy_weight = books_with_decoy * PER_BOOK_WEIGHTS[class_name]
            conditional_prob = Fraction(decoy_weight, class_weight)
        else:
            conditional_prob = Fraction(0, 1)
        
        print(f"    {class_name}: {float(conditional_prob):.10e}")
    
    print()

# Check independence: displayed-row distribution should be independent of payout class
print("=" * 120)
print("INDEPENDENCE CHECK")
print("=" * 120)
print()

print("If the displayed-row distribution is independent of the payout class,")
print("then P(decoy | class) should equal P(decoy) for all classes.")
print()

# Calculate P(decoy) for each tail prize
for tail_prize, allocation in STRATIFIED_ALLOCATION.items():
    total_decoy_weight = Fraction(0, 1)
    for class_name, books_with_decoy in allocation.items():
        if books_with_decoy > 0:
            total_decoy_weight += books_with_decoy * PER_BOOK_WEIGHTS[class_name]
    
    p_decoy = Fraction(total_decoy_weight, total_lut_weight)
    
    print(f"{tail_prize}x:")
    print(f"  P({tail_prize}x decoy shown anywhere): {float(p_decoy):.10e}")
    print()
    
    # Check deviation from independence
    max_deviation = 0
    for class_name in sorted(PER_BOOK_WEIGHTS.keys()):
        class_weight = class_lut_weights[class_name]
        books_with_decoy = allocation.get(class_name, 0)
        
        if books_with_decoy > 0:
            decoy_weight = books_with_decoy * PER_BOOK_WEIGHTS[class_name]
            conditional_prob = Fraction(decoy_weight, class_weight)
        else:
            conditional_prob = Fraction(0, 1)
        
        deviation = abs(conditional_prob - p_decoy)
        if deviation > max_deviation:
            max_deviation = deviation
    
    relative_deviation = max_deviation / p_decoy if p_decoy > 0 else 0
    print(f"  Max deviation from independence: {float(max_deviation):.10e}")
    print(f"  Relative deviation: {float(relative_deviation):.10e}")
    
    if relative_deviation < 0.01:
        print(f"  ✓ Distribution is independent (within 1% tolerance)")
    else:
        print(f"  ✗ Distribution is NOT independent (deviation > 1%)")
    print()

print("=" * 120)
print("CONCLUSION")
print("=" * 120)
print()

print("The stratified allocation creates correlation between decoy prizes and payout classes.")
print("Rare decoys are concentrated in the finest-weight classes (5000x, 50000x classes).")
print("This means:")
print("- High-value decoys are more likely to appear when the payout class is also high-value")
print("- The displayed-row distribution is NOT independent of the payout class")
print("- This deviation is intentional to achieve the required decoy frequency with minimal books")
