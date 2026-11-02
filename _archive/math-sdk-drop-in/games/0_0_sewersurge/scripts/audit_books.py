#!/usr/bin/env python3
"""Independent structural audit for Sewer Surge SDK-generated JSONL books.

This supplements (never replaces) the Math SDK's official RGS verification.
It accepts raw JSONL books or SDK .jsonl.zst books when zstandard is installed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import TextIO

from rules_validation import has_west_to_east_route

SYMBOLS = {"I", "L", "T", "X", "W", "S"}
MAX_WIN_CENTS = 1_000_000
MODE_COSTS = {"base": 1.0, "ante": 3.0, "bonus": 100.0, "super_bonus": 500.0}


def infer_bet_cost(path: Path, explicit_cost: float | None) -> float:
    if explicit_cost is not None:
        if explicit_cost <= 0:
            raise SystemExit("--bet-cost must be positive")
        return explicit_cost
    name = path.name
    for mode, cost in MODE_COSTS.items():
        if name.startswith(f"books_{mode}."):
            return cost
    raise SystemExit("Cannot infer bet cost from filename; pass --bet-cost")


def open_books(path: Path) -> TextIO:
    if path.suffix == ".zst":
        try:
            import zstandard as zstd
        except ImportError as exc:
            raise SystemExit("Install the Math SDK requirements (zstandard) to audit .zst books") from exc
        raw = path.open("rb")
        reader = zstd.ZstdDecompressor().stream_reader(raw)
        import io
        return io.TextIOWrapper(reader, encoding="utf-8")
    return path.open("r", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", type=Path, help="SDK books_<mode>.jsonl or .jsonl.zst")
    parser.add_argument("--bet-cost", type=float, default=None, help="mode cost in base-bet units")
    args = parser.parse_args()
    bet_cost = infer_bet_cost(args.book, args.bet_cost)
    if not args.book.is_file():
        raise SystemExit(f"Book file not found: {args.book}")

    tiers: Counter[str] = Counter()
    count = 0
    total_cents = 0
    max_cents = 0

    with open_books(args.book) as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                book = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON at line {line_number}: {exc}") from exc

            events = book.get("events")
            if not isinstance(events, list):
                raise SystemExit(f"Book {book.get('id', line_number)}: events must be an array")
            board_event = next((e for e in events if e.get("type") == "sewerBoard"), None)
            award_event = next((e for e in events if e.get("type") == "sewerAward"), None)
            final_event = next((e for e in reversed(events) if e.get("type") == "finalWin"), None)
            if board_event is None or award_event is None:
                raise SystemExit(f"Book {book.get('id', line_number)}: missing sewerBoard/sewerAward")

            board = board_event.get("board")
            if not isinstance(board, list) or len(board) != 5 or any(not isinstance(row, list) or len(row) != 5 for row in board):
                raise SystemExit(f"Book {book.get('id', line_number)}: board must be 5x5")

            scatter_count = 0
            for row in board:
                for cell in row:
                    if cell.get("t") not in SYMBOLS:
                        raise SystemExit(f"Book {book.get('id', line_number)}: unknown symbol")
                    rotation = cell.get("r")
                    if type(rotation) is not int or rotation not in range(4):
                        raise SystemExit(f"Book {book.get('id', line_number)}: invalid rotation")
                    if cell["t"] in {"W", "S"} and rotation != 0:
                        raise SystemExit(f"Book {book.get('id', line_number)}: wild/scatter rotated")
                    if cell.get("s") is not (cell["t"] == "S"):
                        raise SystemExit(f"Book {book.get('id', line_number)}: scatter flag mismatch")
                    scatter_count += int(cell["t"] == "S")

            expected_tier = "deep-run" if scatter_count >= 4 else "bonus" if scatter_count == 3 else "none"
            if board_event.get("scatterCount") != scatter_count or board_event.get("scatterTier") != expected_tier:
                raise SystemExit(f"Book {book.get('id', line_number)}: scatter count/tier mismatch")
            if board_event.get("routeAuthority") != "visual-only":
                raise SystemExit(f"Book {book.get('id', line_number)}: route authority must be visual-only")
            if board_event.get("schemaVersion") != 1:
                raise SystemExit(f"Book {book.get('id', line_number)}: unsupported schema version")
            if board_event.get("waterEntry") != "west" or board_event.get("waterExit") != "east":
                raise SystemExit(f"Book {book.get('id', line_number)}: water direction is invalid")
            if any(key in board_event for key in ("routeChoice", "branchChoice", "selectedBranch")):
                raise SystemExit(f"Book {book.get('id', line_number)}: route choice must not be serialized")
            inlet = board_event.get("inlet")
            if type(inlet) is not int or inlet not in range(5) or board[inlet][0]["t"] == "S":
                raise SystemExit(f"Book {book.get('id', line_number)}: invalid west inlet")
            base_openings = {
                "I": {"E", "W"}, "L": {"S", "E"}, "T": {"E", "W", "S"},
                "X": {"N", "E", "S", "W"}, "W": {"N", "E", "S", "W"}, "S": set(),
            }
            directions = ["N", "E", "S", "W"]
            inlet_cell = board[inlet][0]
            west_openings = {
                directions[(directions.index(side) + inlet_cell["r"]) % 4]
                for side in base_openings[inlet_cell["t"]]
            }
            if "W" not in west_openings:
                raise SystemExit(f"Book {book.get('id', line_number)}: inlet pipe has no west-facing port")
            if not has_west_to_east_route(board, inlet):
                raise SystemExit(f"Book {book.get('id', line_number)}: no connected west-to-east route")

            payout = book.get("payoutMultiplier")
            if type(payout) is not int or payout < 0 or payout > MAX_WIN_CENTS or payout % 10:
                raise SystemExit(f"Book {book.get('id', line_number)}: payout outside cap/0.1x step")
            if award_event.get("amount") != payout or award_event.get("payoutMultiplier") != payout:
                raise SystemExit(f"Book {book.get('id', line_number)}: sewerAward payout mismatch")
            if award_event.get("scatterTier") != expected_tier:
                raise SystemExit(f"Book {book.get('id', line_number)}: award tier mismatch")
            if award_event.get("maxWinCapped") is not (payout == MAX_WIN_CENTS):
                raise SystemExit(f"Book {book.get('id', line_number)}: maxWinCapped flag mismatch")
            feature_events = [e for e in events if e.get("type") == "sewerFeature"]
            if expected_tier == "none":
                if feature_events:
                    raise SystemExit(f"Book {book.get('id', line_number)}: unexpected sewerFeature event")
            elif len(feature_events) != 1 or feature_events[0].get("feature") != expected_tier:
                raise SystemExit(f"Book {book.get('id', line_number)}: sewerFeature event/tier mismatch")
            if final_event is None or final_event.get("amount") != payout:
                raise SystemExit(f"Book {book.get('id', line_number)}: finalWin mismatch")
            cap_events = [e for e in events if e.get("type") == "wincap"]
            if payout == MAX_WIN_CENTS:
                if len(cap_events) != 1 or cap_events[0].get("amount") != MAX_WIN_CENTS:
                    raise SystemExit(f"Book {book.get('id', line_number)}: max-win book must contain SDK wincap event")
                if any(e.get("type") == "setWin" for e in events):
                    raise SystemExit(f"Book {book.get('id', line_number)}: SDK wincap book must suppress setWin")
            elif cap_events:
                raise SystemExit(f"Book {book.get('id', line_number)}: unexpected wincap event below max win")

            tiers[expected_tier] += 1
            total_cents += payout
            max_cents = max(max_cents, payout)
            count += 1

    if count == 0:
        raise SystemExit("No books found")

    raw_rtp = total_cents / (count * 100 * bet_cost)
    print(f"PASS: {count:,} SDK books audited")
    print(f"Scatter tiers: {dict(tiers)}")
    print(f"Mode cost: {bet_cost:g}x")
    print(f"Raw sample RTP relative to mode cost (not optimized/certified): {raw_rtp:.4%}")
    print(f"Maximum sample payout: {max_cents / 100:,.1f}x (cap {MAX_WIN_CENTS / 100:,.0f}x)")
    print("Checks: 5x5 board, symbols/rotations, west inlet, connected east outlet, scatter tiers, visual-only authority, award/finalWin cents, official wincap event and 0.1x increments")


if __name__ == "__main__":
    main()
