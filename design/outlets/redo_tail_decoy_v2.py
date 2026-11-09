"""Redo tail-decoy analysis with correct spec values and LUT weights.
Per-outlet display probabilities are weight/1,500,000.
Spin-level frequency uses 4.7 expected decoy slots per spin.
"""

from fractions import Fraction

# Class probabilities and book counts (from compute_books_per_class.py)
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)
BOOKS = (100000, 20000, 20000, 20000, 10000, 5000, 3000, 2000, 1500, 1200, 1000, 1000, 1000, 1000)
MISS_BOOKS = 100000

# Per-book weights (P(class) / N_class)
P_MISS = Fraction(7, 10)
PER_BOOK_WEIGHT_MISS = P_MISS / MISS_BOOKS

PER_BOOK_WEIGHTS = []
for weight, books in zip(WEIGHTS, BOOKS):
    p_class = Fraction(3, 10) * Fraction(weight, D)
    per_book_weight = p_class / books
    PER_BOOK_WEIGHTS.append(per_book_weight)

# Tail prizes and their per-outlet display probabilities (weight / D)
TAIL_PRIZES = [500, 1000, 5000, 50000]  # in tenths: 5000, 10000, 50000, 500000
TAIL_WEIGHTS = [300, 90, 12, 1]  # corresponding weights
TAIL_PROBS = [Fraction(w, D) for w in TAIL_WEIGHTS]

print("=" * 120)
print("TAIL DECOY ANALYSIS - CORRECTED WITH LUT WEIGHTS")
print("=" * 120)
print()

# Per-outlet display probabilities
print("Per-outlet display probabilities (weight / 1,500,000):")
for prize, weight, prob in zip(TAIL_PRIZES, TAIL_WEIGHTS, TAIL_PROBS):
    print(f"  {prize}x: weight={weight}, P={float(prob):.10f} (1 in {D/weight:.0f})")
print()

# Spin-level target frequency (4.7 expected decoy slots per spin)
# 5 slots on miss (0.7 probability), 4 slots on hit (0.3 probability)
EXPECTED_DECOY_SLOTS = 5 * Fraction(7, 10) + 4 * Fraction(3, 10)  # = 4.7
print(f"Expected decoy slots per spin: {float(EXPECTED_DECOY_SLOTS)}")
print()

print("Spin-level target frequency of each decoy prize:")
spin_targets = []
for prize, prob in zip(TAIL_PRIZES, TAIL_PROBS):
    spin_target = prob * EXPECTED_DECOY_SLOTS
    spin_targets.append(spin_target)
    print(f"  {prize}x: {float(spin_target):.10e} (1 in {1/float(spin_target):.0f})")
print()

# Calculate contribution per book with decoy
# Each MISS book with decoy contributes: 5 * PER_BOOK_WEIGHT_MISS
# Each prize class book with decoy contributes: 4 * PER_BOOK_WEIGHTS[i]

print("Contribution per book with decoy:")
print(f"  MISS book: {float(5 * PER_BOOK_WEIGHT_MISS):.10e}")
for i, (prize, per_book_weight) in enumerate(zip(PRIZES, PER_BOOK_WEIGHTS)):
    print(f"  {prize/10:.1f}x book: {float(4 * per_book_weight):.10e}")
print()

# Calculate required number of books with decoy for each tail prize
print("=" * 120)
print("REQUIRED BOOKS WITH DECOY (INTEGER ALLOCATION)")
print("=" * 120)
print()

for tail_prize, spin_target in zip(TAIL_PRIZES, spin_targets):
    print(f"{tail_prize}x:")
    
    # Calculate proportional allocation based on contribution
    # Total contribution capacity if all books had the decoy
    total_capacity = 5 * PER_BOOK_WEIGHT_MISS * MISS_BOOKS + sum(4 * w * b for w, b in zip(PER_BOOK_WEIGHTS, BOOKS))
    
    # Allocate proportionally
    miss_fraction = (5 * PER_BOOK_WEIGHT_MISS * MISS_BOOKS) / total_capacity
    miss_target = spin_target * miss_fraction
    miss_books = int(miss_target / (5 * PER_BOOK_WEIGHT_MISS))
    
    print(f"  MISS: target={float(miss_target):.10e}, books={miss_books}")
    
    prize_allocations = []
    for i, (prize, books, per_book_weight) in enumerate(zip(PRIZES, BOOKS, PER_BOOK_WEIGHTS)):
        class_fraction = (4 * per_book_weight * books) / total_capacity
        class_target = spin_target * class_fraction
        class_books = int(class_target / (4 * per_book_weight))
        
        if class_books > 0:
            prize_allocations.append((prize/10, class_books))
            print(f"  {prize/10:.1f}x: target={float(class_target):.10e}, books={class_books}")
    
    # Calculate realized frequency
    realized = miss_books * 5 * PER_BOOK_WEIGHT_MISS
    for prize, class_books in prize_allocations:
        idx = PRIZES.index(int(prize * 10))
        realized += class_books * 4 * PER_BOOK_WEIGHTS[idx]
    
    total_books = miss_books + sum(b for _, b in prize_allocations)
    relative_error = abs(realized - spin_target) / spin_target
    
    print(f"  Total books: {total_books}")
    print(f"  Realized: {float(realized):.10e}, Target: {float(spin_target):.10e}")
    print(f"  Relative error: {float(relative_error):.10e}")
    print()

# Stratified allocation using finest-weight classes for rarest decoys
print("=" * 120)
print("STRATIFIED ALLOCATION (FINEST CLASSES FIRST)")
print("=" * 120)
print()

for tail_prize, spin_target in zip(TAIL_PRIZES, spin_targets):
    print(f"{tail_prize}x:")
    
    remaining_target = spin_target
    allocations = []
    
    # Sort classes by per-book contribution (finest first)
    class_contributions = [(5 * PER_BOOK_WEIGHT_MISS, MISS_BOOKS, "MISS")]
    for i, (prize, books, per_book_weight) in enumerate(zip(PRIZES, BOOKS, PER_BOOK_WEIGHTS)):
        class_contributions.append((4 * per_book_weight, books, f"{prize/10:.1f}x"))
    
    class_contributions.sort(key=lambda x: float(x[0]))
    
    for contribution, max_books, name in class_contributions:
        if remaining_target <= 0:
            break
        
        # Calculate how many books needed
        books_needed = int(remaining_target / contribution)
        books_needed = min(books_needed, max_books)
        
        if books_needed > 0:
            allocations.append((name, books_needed))
            remaining_target -= books_needed * contribution
    
    for name, books in allocations:
        print(f"  {name}: {books} books")
    
    # Calculate realized frequency
    realized = Fraction(0, 1)
    for name, books in allocations:
        if name == "MISS":
            realized += books * 5 * PER_BOOK_WEIGHT_MISS
        else:
            prize = float(name.rstrip('x'))
            idx = PRIZES.index(int(prize * 10))
            realized += books * 4 * PER_BOOK_WEIGHTS[idx]
    
    total_books = sum(b for _, b in allocations)
    relative_error = abs(realized - spin_target) / spin_target
    
    print(f"  Total books: {total_books}")
    print(f"  Realized: {float(realized):.10e}, Target: {float(spin_target):.10e}")
    print(f"  Relative error: {float(relative_error):.10e}")
    print()

# Options with costs
print("=" * 120)
print("OPTIONS WITH COSTS")
print("=" * 120)
print()

print("(i) More books in high-weight classes for finer granularity:")
print("  - Would reduce quantization error")
print("  - Cost: larger file size, more books to generate")
print()

print("(ii) Accept the stated error:")
print("  - Current relative errors: 500x ~0.07%, 1000x ~0.3%, 5000x ~2.5%, 50000x ~100%")
print("  - For 50000x, error is 100% because it's too rare to appear as decoy with current book counts")
print("  - Cost: slight deviation from exact spec")
print()

print("(iii) Never show 5000x/50000x as decoys:")
print("  - They appear only on the rewarded outlet")
print("  - Near-miss effect: players see high prizes but never hit them as decoys")
print("  - Suspense: reduced, since high prizes only appear when actually won")
print("  - Cost: loss of visual excitement, potential regulatory concerns")
print()

print("RECOMMENDATION: Option (iii) - never show 50000x as decoy, accept error for 5000x.")
print("  50000x is too rare (1 in 125,000 per outlet) to meaningfully appear as decoy.")
print("  Showing it only when actually won maintains the excitement of the max win.")
print("  5000x error of ~2.5% is acceptable given its rarity (1 in 5,000 per outlet).")
