#!/usr/bin/env python3
"""Audit generated Sewer Surge books and weighted lookup tables for all four modes."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
from collections import Counter
from pathlib import Path

from rules_validation import find_west_to_east_route

GAME_DIR = Path(__file__).resolve().parents[1]
LIBRARY_DIR = GAME_DIR / "library"
BOOK_DIR = LIBRARY_DIR / "books"
COMPRESSED_BOOK_DIR = LIBRARY_DIR / "books_compressed"
LOOKUP_DIR = LIBRARY_DIR / "lookup_tables"
COSTS = {"base": 1.0, "ante": 3.0, "bonus": 100.0, "super_bonus": 500.0}
VALID_PIPES = {"I", "L", "T", "X", "W", "S"}
SCATTER_TIERS = {0: "none", 1: "none", 2: "none", 3: "bonus", 4: "deep-run", 5: "deep-run"}
MAX_WIN = 10_000.0


def load_books(mode: str) -> tuple[list[dict], str]:
    plain = BOOK_DIR / f"books_{mode}.jsonl"
    compressed = COMPRESSED_BOOK_DIR / f"books_{mode}.jsonl.zst"
    books: list[dict] = []

    if plain.exists():
        with plain.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    books.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"{plain.name}:{line_no}: invalid JSON: {exc}") from exc
        return books, str(plain)

    if compressed.exists():
        try:
            import zstandard as zstd
        except ImportError as exc:
            raise RuntimeError("Compressed books found but the pinned `zstandard` package is unavailable") from exc
        with compressed.open("rb") as source:
            with zstd.ZstdDecompressor().stream_reader(source) as reader:
                with io.TextIOWrapper(reader, encoding="utf-8") as handle:
                    for line_no, line in enumerate(handle, 1):
                        if not line.strip():
                            continue
                        try:
                            books.append(json.loads(line))
                        except json.JSONDecodeError as exc:
                            raise RuntimeError(f"{compressed.name}:{line_no}: invalid JSON: {exc}") from exc
        return books, str(compressed)

    raise RuntimeError(f"Missing books for {mode}: expected {plain} or {compressed}")


def read_lookup_table(
    mode: str,
    cost: float,
    target_rtp: float,
    tolerance: float,
    book_payouts: dict[int, float],
    book_tiers: dict[int, str],
) -> dict:
    optimized = LOOKUP_DIR / f"lookUpTable_{mode}_0.csv"
    unoptimized = LOOKUP_DIR / f"lookUpTable_{mode}.csv"
    source = optimized if optimized.exists() else unoptimized if unoptimized.exists() else None
    if source is None:
        return {"status": "missing", "path": None, "weighted_rtp_percent": None, "hit_rate_percent": None, "feature_rate_percent": None, "bonus_rate_percent": None, "deep_run_rate_percent": None, "rows": 0, "errors": ["lookup table file is missing"]}

    weights: dict[int, float] = {}
    total_weight = 0.0
    weighted_payout = 0.0
    hit_weight = 0.0
    max_win_weight = 0.0
    tier_weights: Counter[str] = Counter()
    errors: list[str] = []
    rows = 0

    with source.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if len(row) < 3:
                continue
            try:
                sim_id = int(float(row[0]))
                weight = float(row[1])
                payout = float(row[2])
            except (TypeError, ValueError):
                # Ignore an optional header row.
                continue
            if sim_id in weights:
                errors.append(f"duplicate simulation id {sim_id} in LUT")
                continue
            if weight < 0 or payout < 0:
                errors.append(f"negative weight/payout in LUT row {row}")
                continue
            if sim_id not in book_payouts:
                errors.append(f"LUT id {sim_id} has no matching book")
            elif not math.isclose(payout, book_payouts[sim_id], abs_tol=1e-8):
                errors.append(f"LUT payout for id {sim_id} differs from book payout")
            weights[sim_id] = weight
            rows += 1
            total_weight += weight
            weighted_payout += weight * payout
            if payout > 0:
                hit_weight += weight
            if payout >= MAX_WIN:
                max_win_weight += weight
            tier_weights[book_tiers.get(sim_id, "unknown")] += weight

    missing_book_ids = set(book_payouts) - set(weights)
    if missing_book_ids:
        errors.append(f"{len(missing_book_ids)} books are missing from LUT")

    if rows == 0 or total_weight <= 0:
        return {"status": "invalid", "path": str(source), "weighted_rtp_percent": None, "hit_rate_percent": None, "feature_rate_percent": None, "bonus_rate_percent": None, "deep_run_rate_percent": None, "rows": rows, "errors": errors or ["empty LUT/zero total weight"]}

    weighted_rtp = 100.0 * weighted_payout / (total_weight * cost)
    hit_rate = 100.0 * hit_weight / total_weight
    bonus_rate = 100.0 * tier_weights["bonus"] / total_weight
    deep_rate = 100.0 * tier_weights["deep-run"] / total_weight
    feature_rate = bonus_rate + deep_rate
    max_win_frequency = total_weight / max_win_weight if max_win_weight > 0 else None
    status = "optimized" if source == optimized else "unoptimized"
    warnings = []
    if hit_rate < 5.0:
        warnings.append("weighted non-zero hit rate is below the 5% guideline")
    if max_win_frequency is None:
        warnings.append("optimized distribution has no weighted 10,000x outcome")
    elif max_win_frequency > 10_000_000:
        warnings.append("10,000x outcome is rarer than the typical 1-in-10,000,000 guideline")
    return {
        "status": status,
        "path": str(source),
        "rows": rows,
        "total_weight": total_weight,
        "weighted_rtp_percent": round(weighted_rtp, 6),
        "hit_rate_percent": round(hit_rate, 6),
        "bonus_rate_percent": round(bonus_rate, 6),
        "deep_run_rate_percent": round(deep_rate, 6),
        "feature_rate_percent": round(feature_rate, 6),
        "max_win_weighted_probability_percent": round(100.0 * max_win_weight / total_weight, 9),
        "max_win_expected_frequency_in_rounds": round(max_win_frequency, 3) if max_win_frequency is not None else None,
        "max_win_within_typical_1_in_10m_guideline": max_win_frequency is not None and max_win_frequency <= 10_000_000,
        "statistical_warnings": warnings,
        "target_rtp_percent": target_rtp,
        "target_tolerance_percentage_points": tolerance,
        "rtp_within_tolerance": abs(weighted_rtp - target_rtp) <= tolerance,
        "errors": errors,
    }


def audit_mode(mode: str, cost: float, target_rtp: float, tolerance: float) -> dict:
    books, book_source = load_books(mode)
    if not books:
        raise RuntimeError(f"No generated books for {mode}")

    tiers: Counter[str] = Counter()
    max_payout = 0.0
    wincap_count = 0
    branchable_count = 0
    total_payout = 0.0
    nonzero_book_count = 0
    unique_payouts: set[float] = set()
    errors: list[str] = []
    book_payouts: dict[int, float] = {}
    book_tiers: dict[int, str] = {}

    for book in books:
        book_id = book.get("id")
        if not isinstance(book_id, int):
            errors.append(f"book has invalid/missing integer id: {book_id!r}")
            continue
        if book_id in book_payouts:
            errors.append(f"duplicate book id {book_id}")
            continue

        events = book.get("events")
        if not isinstance(events, list):
            errors.append(f"book {book_id}: events is not a list")
            continue
        board_event = next((event for event in events if event.get("type") == "sewerBoard"), None)
        feature_event = next((event for event in events if event.get("type") == "sewerFeature"), None)
        award_event = next((event for event in events if event.get("type") == "sewerAward"), None)
        final_event = next((event for event in reversed(events) if event.get("type") == "finalWin"), None)
        total_event = next((event for event in reversed(events) if event.get("type") == "setTotalWin"), None)
        cap_events = [event for event in events if event.get("type") == "wincap"]

        if not all((board_event, feature_event, award_event, final_event, total_event)):
            errors.append(f"book {book_id}: missing required Sewer/SDK event")
            continue

        board = board_event.get("board")
        if not isinstance(board, list) or len(board) != 5 or any(not isinstance(row, list) or len(row) != 5 for row in board):
            errors.append(f"book {book_id}: board is not 5x5")
            continue

        scatter_count = 0
        for row in board:
            for cell in row:
                if cell.get("t") not in VALID_PIPES:
                    errors.append(f"book {book_id}: invalid pipe symbol")
                    break
                if cell.get("r") not in (0, 1, 2, 3):
                    errors.append(f"book {book_id}: invalid rotation")
                if cell.get("t") in {"W", "S"} and cell.get("r") != 0:
                    errors.append(f"book {book_id}: W/S symbol was rotated")
                if cell.get("t") == "S":
                    scatter_count += 1

        if scatter_count != board_event.get("scatterCount"):
            errors.append(f"book {book_id}: scatter count differs from board")
        expected_tier = SCATTER_TIERS.get(scatter_count, "invalid")
        if board_event.get("scatterTier") != expected_tier or feature_event.get("scatterTier") != expected_tier:
            errors.append(f"book {book_id}: scatter tier mismatch")
        if feature_event.get("scatterCount") != scatter_count:
            errors.append(f"book {book_id}: sewerFeature scatter count differs from board")
        tiers[expected_tier] += 1
        book_tiers[book_id] = expected_tier

        inlet = board_event.get("inlet")
        if not isinstance(inlet, int) or not 0 <= inlet < 5:
            errors.append(f"book {book_id}: invalid inlet")
        else:
            route = find_west_to_east_route(board, inlet)
            if route is None:
                errors.append(f"book {book_id}: no eastward route with a connected branch")
            else:
                branchable_count += 1

        if board_event.get("routeAuthority") != "visual-only":
            errors.append(f"book {book_id}: route authority is not visual-only")
        if any(key in board_event for key in ("routeChoice", "branchChoice", "selectedBranches")):
            errors.append(f"book {book_id}: player route choice serialized into outcome")

        payout = float(book.get("payoutMultiplier", -1))
        book_payouts[book_id] = payout
        unique_payouts.add(payout)
        if payout > 0:
            nonzero_book_count += 1
        total_payout += payout
        max_payout = max(max_payout, payout)
        if payout < 0 or payout > MAX_WIN:
            errors.append(f"book {book_id}: payout outside 0..10000x")
        if not math.isclose(payout * 10, round(payout * 10), abs_tol=1e-7):
            errors.append(f"book {book_id}: payout is not in 0.1x increments")

        amount = int(round(payout * 100))
        if award_event.get("amount") != amount or award_event.get("payoutMultiplier") != payout:
            errors.append(f"book {book_id}: sewerAward payout mismatch")
        if total_event.get("amount") != amount or final_event.get("amount") != amount:
            errors.append(f"book {book_id}: SDK final/total win mismatch")
        if payout == MAX_WIN:
            wincap_count += 1
            if len(cap_events) != 1 or cap_events[0].get("amount") != int(MAX_WIN * 100):
                errors.append(f"book {book_id}: max win missing matching wincap event")
        elif cap_events:
            errors.append(f"book {book_id}: unexpected wincap event")
        if award_event.get("maxWinCapped") != (payout == MAX_WIN):
            errors.append(f"book {book_id}: maxWinCapped flag mismatch")

    raw_rtp = 100.0 * total_payout / (len(books) * cost)
    lut = read_lookup_table(mode, cost, target_rtp, tolerance, book_payouts, book_tiers)
    return {
        "mode": mode,
        "cost_multiplier": cost,
        "book_source": book_source,
        "books": len(books),
        "scatter_tiers": dict(tiers),
        "books_with_connected_branchable_route": branchable_count,
        "max_payout_x": max_payout,
        "wincap_books": wincap_count,
        "nonzero_payout_books": nonzero_book_count,
        "unique_payout_multipliers": len(unique_payouts),
        "raw_unoptimized_rtp_percent": round(raw_rtp, 6),
        "lookup_table": lut,
        "structural_failures": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-optimized-lut", action="store_true")
    parser.add_argument("--target-rtp", type=float, default=96.5)
    parser.add_argument("--tolerance", type=float, default=0.5)
    parser.add_argument("--ante-feature-ratio-tolerance", type=float, default=0.10,
                        help="Relative tolerance around the configured 5x Ante/Base feature frequency target")
    args = parser.parse_args()

    results = [audit_mode(mode, cost, args.target_rtp, args.tolerance) for mode, cost in COSTS.items()]
    failures = sum(len(item["structural_failures"]) + len(item["lookup_table"].get("errors", [])) for item in results)
    missing_luts = [item["mode"] for item in results if item["lookup_table"]["status"] != "optimized"]
    out_of_range = [
        item["mode"] for item in results
        if item["lookup_table"].get("status") == "optimized"
        and not item["lookup_table"].get("rtp_within_tolerance", False)
    ]

    base_rate = results[0]["lookup_table"].get("feature_rate_percent")
    ante_rate = results[1]["lookup_table"].get("feature_rate_percent")
    ratio = None
    ratio_pass = None
    if base_rate is not None and ante_rate is not None and base_rate > 0:
        ratio = ante_rate / base_rate
        ratio_pass = abs(ratio - 5.0) <= 5.0 * args.ante_feature_ratio_tolerance

    optimized_pass = failures == 0 and not missing_luts and not out_of_range and ratio_pass is True
    output = {
        "classification": "optimized math/LUT audit passed" if optimized_pass else "debug/unoptimized sample or incomplete optimized audit",
        "optimized_math_audit_pass": optimized_pass,
        "math_sdk": "local extracted SDK workspace snapshot; clean exact-pin runtime test still required",
        "target_rtp_percent": args.target_rtp,
        "rtp_tolerance_percentage_points": args.tolerance,
        "ante_base_feature_frequency_ratio": ratio,
        "ante_base_feature_frequency_ratio_target": 5.0,
        "ante_base_feature_frequency_ratio_tolerance_relative": args.ante_feature_ratio_tolerance,
        "ante_base_feature_frequency_ratio_pass": ratio_pass,
        "books_per_mode": {item["mode"]: item["books"] for item in results},
        "total_books": sum(item["books"] for item in results),
        "structural_and_lut_failures": failures,
        "modes_missing_optimized_lut": missing_luts,
        "optimized_lut_rtp_out_of_tolerance": out_of_range,
        "modes": results,
    }
    output_path = Path(os.environ.get("SEWER_SURGE_AUDIT_OUTPUT", str(GAME_DIR / "smoke-results-latest.json")))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))

    if failures:
        return 1
    if args.require_optimized_lut and (missing_luts or out_of_range or ratio_pass is not True):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
