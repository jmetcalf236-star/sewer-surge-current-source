"""Compute tail decoy placement for 1000x, 5000x, 50000x prizes.
"""

from fractions import Fraction

# Class probabilities and book counts
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)
BOOKS = (100000, 20000, 20000, 20000, 10000, 5000, 3000, 2000, 1500, 1200, 1000, 1000, 1000, 1000)
MISS_BOOKS = 100000

# Tail prizes of interest
TAIL_PRIZES = [1000, 5000, 50000]  # in tenths: 10000, 50000, 500000

print("=" * 120)
print("TAIL DECOY PLACEMENT ANALYSIS")
print("=" * 120)
print()

# For each class, compute expected number of books with each tail prize as a decoy
# Each book has 5 decoy positions (all outlets on miss, 4 non-reached outlets on hit)

print("Expected number of books displaying each tail prize as a decoy (pure random draws):")
print(f"{'Class':<12} {'Books':<10} {'Decoy Slots':<12} {'P(1000x)':<12} {'E(1000x)':<12} {'P(5000x)':<12} {'E(5000x)':<12} {'P(50000x)':<12} {'E(50000x)':<12}")
print("-" * 120)

total_expected_1000x = 0
total_expected_5000x = 0
total_expected_50000x = 0

# MISS class: 5 decoy slots per book
p_1000x = Fraction(WEIGHTS[9], D)  # weight for 1000x
p_5000x = Fraction(WEIGHTS[10], D)  # weight for 5000x
p_50000x = Fraction(WEIGHTS[12], D)  # weight for 50000x

e_1000x = MISS_BOOKS * 5 * p_1000x
e_5000x = MISS_BOOKS * 5 * p_5000x
e_50000x = MISS_BOOKS * 5 * p_50000x

total_expected_1000x += e_1000x
total_expected_5000x += e_5000x
total_expected_50000x += e_50000x

print(f"{'MISS':<12} {MISS_BOOKS:<10} {MISS_BOOKS*5:<12} {float(p_1000x):<12.10f} {float(e_1000x):<12.2f} {float(p_5000x):<12.10f} {float(e_5000x):<12.2f} {float(p_50000x):<12.10f} {float(e_50000x):<12.2f}")

# Prize classes: 4 decoy slots per book (one outlet is the reached outlet with the prize itself)
for prize, weight, books in zip(PRIZES, WEIGHTS, BOOKS):
    e_1000x = books * 4 * p_1000x
    e_5000x = books * 4 * p_5000x
    e_50000x = books * 4 * p_50000x
    
    total_expected_1000x += e_1000x
    total_expected_5000x += e_5000x
    total_expected_50000x += e_50000x
    
    prize_str = f"{prize/10:.1f}x"
    print(f"{prize_str:<12} {books:<10} {books*4:<12} {float(p_1000x):<12.10f} {float(e_1000x):<12.2f} {float(p_5000x):<12.10f} {float(e_5000x):<12.2f} {float(p_50000x):<12.10f} {float(e_50000x):<12.2f}")

print("-" * 120)
print(f"{'TOTAL':<12} {sum(BOOKS)+MISS_BOOKS:<10} {'':<12} {'':<12} {float(total_expected_1000x):<12.2f} {'':<12} {float(total_expected_5000x):<12.2f} {'':<12} {float(total_expected_50000x):<12.2f}")
print()

# Spec values: P(prize shown anywhere on the row)
print("Spec values: P(prize shown anywhere on the row)")
for tail_prize, tail_weight in [(1000, WEIGHTS[9]), (5000, WEIGHTS[10]), (50000, WEIGHTS[12])]:
    p_shown = Fraction(tail_weight, D)
    print(f"  {tail_prize}x: P(shown) = {float(p_shown):.10f} (1 in {D/tail_weight:.0f})")
print()

# Realized frequency if exactly expected number of books contain the decoy
print("Realized display frequency if exactly expected number of books contain the decoy:")
total_decoy_slots = MISS_BOOKS * 5 + sum(b * 4 for b in BOOKS)
for tail_prize, expected in [(1000, total_expected_1000x), (5000, total_expected_5000x), (50000, total_expected_50000x)]:
    realized_p = Fraction(int(expected), total_decoy_slots)
    spec_p = Fraction(WEIGHTS[PRIZES.index(tail_prize * 10)], D)
    error = realized_p - spec_p
    print(f"  {tail_prize}x: realized = {float(realized_p):.10f}, spec = {float(spec_p):.10f}, error = {float(error):.10e}")
print()

# Quantization error analysis
print("Quantization error analysis:")
print(f"Total decoy slots: {total_decoy_slots:,}")
for tail_prize, expected in [(1000, total_expected_1000x), (5000, total_expected_5000x), (50000, total_expected_50000x)]:
    print(f"  {tail_prize}x: expected = {float(expected):.2f}, integer = {int(expected)}, truncation error = {expected - int(expected):.2f}")
print()

# Stratified allocation proposal
print("=" * 120)
print("STRATIFIED ALLOCATION PROPOSAL")
print("=" * 120)
print()

# For each tail prize, allocate exact integer number of books to contain it as a decoy
# Target: realized frequency within 0.1% of spec

for tail_prize, tail_weight in [(1000, WEIGHTS[9]), (5000, WEIGHTS[10]), (50000, WEIGHTS[12])]:
    spec_p = Fraction(tail_weight, D)
    target_count = int(spec_p * total_decoy_slots)
    
    # Allocate proportionally across classes based on their decoy slot count
    print(f"{tail_prize}x decoy allocation:")
    print(f"  Target count: {target_count} (spec_p = {float(spec_p):.10f})")
    print(f"  Realized P: {Fraction(target_count, total_decoy_slots):.10f}")
    print(f"  Error: {float(Fraction(target_count, total_decoy_slots) - spec_p):.10e}")
    print()
    
    # Allocate to MISS class first (has most slots)
    miss_slots = MISS_BOOKS * 5
    miss_allocation = int(target_count * Fraction(miss_slots, total_decoy_slots))
    print(f"  MISS class: {miss_allocation} / {miss_slots} slots ({miss_allocation/MISS_BOOKS:.2f} per book)")
    
    remaining = target_count - miss_allocation
    prize_slots = sum(b * 4 for b in BOOKS)
    
    # Allocate to prize classes proportionally
    for prize, books in zip(PRIZES, BOOKS):
        class_slots = books * 4
        class_allocation = int(remaining * Fraction(class_slots, prize_slots))
        if class_allocation > 0:
            print(f"  {prize/10:.1f}x class: {class_allocation} / {class_slots} slots ({class_allocation/books:.2f} per book)")
    
    print()
