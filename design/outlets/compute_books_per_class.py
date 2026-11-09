"""Compute books-per-class table with exact Fractions and 2^50 scaling.
"""

from fractions import Fraction
from math import pow

# Class probabilities from base_exact.py (14-prize ladder)
D = 1_500_000
WEIGHTS = (368718, 358614, 335000, 194300, 112693, 65362, 37910,
           20000, 5000, 2000, 300, 90, 12, 1)
PRIZES = (10, 15, 20, 30, 50, 80, 100, 200, 500, 1000, 5000, 10000, 50000, 500000)

# Book allocation (same as BASE_GAME_SPEC.md)
BOOKS = (100000, 20000, 20000, 20000, 10000, 5000, 3000, 2000, 1500, 1200, 1000, 1000, 1000, 1000)
MISS_BOOKS = 100000

# Scaling factor
SCALE_2_50 = int(2 ** 50)

print("=" * 120)
print("BOOKS PER CLASS TABLE (Exact Fractions, 2^50 Scaling)")
print("=" * 120)
print(f"SCALE_2_50 = {SCALE_2_50} ≈ {SCALE_2_50:.3e}")
print()

# Header
print(f"{'Class':<12} {'P(class)':<15} {'Books':<10} {'Per-Book Weight':<20} {'Scaled Weight':<20} {'Realized P':<15} {'RTP Error':<12}")
print("-" * 120)

total_books = MISS_BOOKS + sum(BOOKS)
total_scaled_weight = 0
total_realized_p = Fraction(0, 1)

# MISS class
p_miss = Fraction(7, 10)
per_book_weight = p_miss / MISS_BOOKS
scaled_weight = int(per_book_weight * SCALE_2_50)
realized_p = Fraction(scaled_weight, SCALE_2_50) * MISS_BOOKS
total_scaled_weight += scaled_weight * MISS_BOOKS
total_realized_p += realized_p
rtp_error = realized_p - p_miss

print(f"{'MISS':<12} {float(p_miss):<15.10f} {MISS_BOOKS:<10} {float(per_book_weight):<20.10e} {scaled_weight:<20} {float(realized_p):<15.10f} {float(rtp_error):<12.10e}")

# Prize classes
for i, (prize, weight, books) in enumerate(zip(PRIZES, WEIGHTS, BOOKS)):
    p_class = Fraction(3, 10) * Fraction(weight, D)
    per_book_weight = p_class / books
    scaled_weight = int(per_book_weight * SCALE_2_50)
    realized_p = Fraction(scaled_weight, SCALE_2_50) * books
    total_scaled_weight += scaled_weight * books
    total_realized_p += realized_p
    rtp_error = realized_p - p_class
    
    prize_str = f"{prize/10:.1f}x"
    print(f"{prize_str:<12} {float(p_class):<15.10f} {books:<10} {float(per_book_weight):<20.10e} {scaled_weight:<20} {float(realized_p):<15.10f} {float(rtp_error):<12.10e}")

print("-" * 120)
print(f"{'TOTAL':<12} {'':<15} {total_books:<10} {'':<20} {total_scaled_weight:<20} {float(total_realized_p):<15.10f} {float(total_realized_p - 1):<12.10e}")
print()

# RTP calculation
target_rtp = Fraction(193, 200)
realized_rtp = Fraction(0, 1)
for prize, weight, books in zip(PRIZES, WEIGHTS, BOOKS):
    p_class = Fraction(3, 10) * Fraction(weight, D)
    per_book_weight = p_class / books
    scaled_weight = int(per_book_weight * SCALE_2_50)
    realized_p = Fraction(scaled_weight, SCALE_2_50) * books
    realized_rtp += realized_p * Fraction(prize, 10)

print(f"Target RTP: {float(target_rtp):.10f}")
print(f"Realized RTP: {float(realized_rtp):.10f}")
print(f"RTP Error: {float(realized_rtp - target_rtp):.10e}")
print()

# File size calculation from existing books
print("=" * 120)
print("FILE SIZE CALCULATION FROM EXISTING BOOKS")
print("=" * 120)

# From the dir output:
# books_base.jsonl.zst: 11,957,119 bytes, 100,000 books
# books_ante.jsonl.zst: 12,860,862 bytes, 100,000 books
# books_bonus.jsonl.zst: 13,821,221 bytes, 100,000 books
# books_super_bonus.jsonl.zst: 14,406,437 bytes, 100,000 books

existing_books = [
    ("base", 11957119, 100000),
    ("ante", 12860862, 100000),
    ("bonus", 13821221, 100000),
    ("super_bonus", 14406437, 100000),
]

for mode, size, count in existing_books:
    bytes_per_book = size / count
    print(f"{mode}: {size:,} bytes / {count:,} books = {bytes_per_book:.2f} bytes/book")

avg_bytes_per_book = sum(s for _, s, _ in existing_books) / sum(c for _, _, c in existing_books)
print(f"\nAverage: {avg_bytes_per_book:.2f} bytes/book")

# Extrapolate to new design
new_books_per_mode = total_books
new_size_per_mode = new_books_per_mode * avg_bytes_per_book
new_total_size = new_size_per_mode * 4

print(f"\nNew design: {new_books_per_mode:,} books/mode × {avg_bytes_per_book:.2f} bytes/book = {new_size_per_mode:,.0f} bytes/mode")
print(f"Total (4 modes): {new_total_size:,.0f} bytes = {new_total_size / (1024**3):.3f} GB")
