"""Policy A: 5000x and 50000x appear ONLY on the outlet that pays them.
Prizes <= 1000x may appear as decoys with proportional allocation.
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

# Tail prizes that CAN appear as decoys (<= 1000x)
ALLOWED_DECOY_PRIZES = [500, 1000]  # in tenths: 5000, 10000
ALLOWED_DECOY_WEIGHTS = [300, 90]
ALLOWED_DECOY_PROBS = [Fraction(w, D) for w in ALLOWED_DECOY_WEIGHTS]

# Prizes that NEVER appear as decoys (only on paying outlet)
FORBIDDEN_DECOY_PRIZES = [5000, 50000]

print("=" * 120)
print("POLICY A: 5000x AND 50000x ONLY ON PAYING OUTLET")
print("=" * 120)
print()
print("Rules:")
print("- 5000x and 50000x appear ONLY on the outlet that pays them (never as decoys)")
print("- Prizes <= 1000x may appear as decoys with proportional allocation across classes")
print()

# Expected decoy slots per spin (4.7)
EXPECTED_DECOY_SLOTS = 5 * Fraction(7, 10) + 4 * Fraction(3, 10)  # = 4.7

print(f"Expected decoy slots per spin: {float(EXPECTED_DECOY_SLOTS)}")
print()

# Spin-level decoy-display targets for 500x/1000x
print("=" * 120)
print("SPIN-LEVEL DECOY-DISPLAY TARGETS (500x, 1000x)")
print("=" * 120)
print()

spin_targets = {}
for prize, prob in zip(ALLOWED_DECOY_PRIZES, ALLOWED_DECOY_PROBS):
    spin_target = prob * EXPECTED_DECOY_SLOTS
    spin_targets[prize] = spin_target
    print(f"  {prize}x: {float(spin_target):.10e} (1 in {1/float(spin_target):.0f})")
print()

# Calculate contribution per book with decoy
print("Contribution per book with decoy:")
print(f"  MISS book: {float(5 * PER_BOOK_WEIGHTS['MISS']):.10e}")
for class_name, per_book_weight in PER_BOOK_WEIGHTS.items():
    if class_name == "MISS":
        continue
    print(f"  {class_name} book: {float(4 * per_book_weight):.10e}")
print()

# Proportional allocation for 500x/1000x
print("=" * 120)
print("PROPORTIONAL ALLOCATION FOR 500x/1000x")
print("=" * 120)
print()

for tail_prize, spin_target in spin_targets.items():
    print(f"{tail_prize}x:")
    
    # Calculate proportional allocation based on contribution
    total_capacity = 5 * PER_BOOK_WEIGHTS["MISS"] * BOOKS["MISS"]
    for class_name, books in BOOKS.items():
        if class_name == "MISS":
            continue
        total_capacity += 4 * PER_BOOK_WEIGHTS[class_name] * books
    
    # Allocate proportionally
    miss_fraction = (5 * PER_BOOK_WEIGHTS["MISS"] * BOOKS["MISS"]) / total_capacity
    miss_target = spin_target * miss_fraction
    miss_books = int(miss_target / (5 * PER_BOOK_WEIGHTS["MISS"]))
    
    print(f"  MISS: target={float(miss_target):.10e}, books={miss_books}")
    
    prize_allocations = []
    for class_name, books in BOOKS.items():
        if class_name == "MISS":
            continue
        class_fraction = (4 * PER_BOOK_WEIGHTS[class_name] * books) / total_capacity
        class_target = spin_target * class_fraction
        class_books = int(class_target / (4 * PER_BOOK_WEIGHTS[class_name]))
        
        if class_books > 0:
            prize_allocations.append((class_name, class_books))
            print(f"  {class_name}: target={float(class_target):.10e}, books={class_books}")
    
    # Calculate realized frequency
    realized = miss_books * 5 * PER_BOOK_WEIGHTS["MISS"]
    for class_name, class_books in prize_allocations:
        realized += class_books * 4 * PER_BOOK_WEIGHTS[class_name]
    
    total_books = miss_books + sum(b for _, b in prize_allocations)
    relative_error = abs(realized - spin_target) / spin_target
    
    print(f"  Total books: {total_books}")
    print(f"  Realized: {float(realized):.10e}, Target: {float(spin_target):.10e}")
    print(f"  Relative error: {float(relative_error):.10e}")
    print()

# Conditional probabilities for policy A
print("=" * 120)
print("CONDITIONAL PROBABILITIES (POLICY A)")
print("=" * 120)
print()

SCALE_2_50 = int(2 ** 50)
class_lut_weights = {}
for class_name, per_book_weight in PER_BOOK_WEIGHTS.items():
    class_lut_weights[class_name] = per_book_weight * BOOKS[class_name]

total_lut_weight = sum(class_lut_weights.values())

# Build allocation for 500x/1000x
policy_allocation = {
    500: {
        "MISS": 0,
        "1.0x": 20,
        "1.5x": 4,
        "2.0x": 4,
        "3.0x": 4,
        "5.0x": 2,
        "8.0x": 1,
        "10.0x": 1,
        "20.0x": 1,
        "50.0x": 1,
        "100.0x": 1,
        "500.0x": 1,
        "1000.0x": 1,
        "5000.0x": 1,
        "50000.0x": 1,
    },
    1000: {
        "MISS": 0,
        "1.0x": 6,
        "1.5x": 1,
        "2.0x": 1,
        "3.0x": 1,
        "5.0x": 1,
        "8.0x": 1,
        "10.0x": 1,
        "20.0x": 1,
        "50.0x": 1,
        "100.0x": 1,
        "500.0x": 1,
        "1000.0x": 1,
        "5000.0x": 1,
        "50000.0x": 1,
    },
}

for tail_prize, allocation in policy_allocation.items():
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

# Effect on P(displayed anywhere) for 5000x/50000x
print("=" * 120)
print("EFFECT ON P(DISPLAYED ANYWHERE) FOR 5000x/50000x")
print("=" * 120)
print()

print("Under Policy A:")
print("- 5000x and 50000x NEVER appear as decoys")
print("- They only appear on the outlet that pays them")
print("- P(5000x displayed anywhere) = P(5000x awarded) = 0.0000024 (1 in 416,667)")
print("- P(50000x displayed anywhere) = P(50000x awarded) = 0.0000002 (1 in 5,000,000)")
print()

print("Under the original design (with decoys):")
print("- P(5000x displayed anywhere) would include decoy appearances")
print("- P(5000x displayed anywhere) ≈ 0.0000376 (1 in 26,596)")
print("- P(50000x displayed anywhere) ≈ 0.00000313 (1 in 319,149)")
print()

print("Reduction in display frequency:")
print("- 5000x: reduced by factor of ~14 (from 1 in 26,596 to 1 in 416,667)")
print("- 50000x: reduced by factor of ~16 (from 1 in 319,149 to 1 in 5,000,000)")
print()

# Spoiler effect and reveal order
print("=" * 120)
print("SPOILER EFFECT AND REVEAL ORDER")
print("=" * 120)
print()

print("Spoiler effect:")
print("- If the prize row is revealed all at once before the water animation,")
print("  players can immediately see if they won 5000x/50000x")
print("- This reduces suspense and excitement")
print()

print("Proposed reveal order:")
print("- Prize values are revealed AS WATER ARRIVES at each outlet")
print("- The row fills from left to right as the water flows")
print("- The final outlet (the one that pays) is revealed last")
print("- This maintains suspense because the winning prize is not known until the end")
print()

print("Rules text:")
print('"Prizes shown on outlets are illustrative of the pre-determined result;')
print('5000x and 50,000x are displayed only when awarded."')
print()
