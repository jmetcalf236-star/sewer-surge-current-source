"""Authoritative Sewer Surge round generation for Stake Engine Math SDK."""
from __future__ import annotations

import hashlib
import random
from contextlib import contextmanager
from typing import Any, Iterator

from game_override import GameStateOverride
from src.calculations.statistics import get_random_outcome
from src.events.events import reveal_event, set_total_event, set_win_event
from rules_validation import validate_round_payload


class GameState(GameStateOverride):
    """One deterministic, server-authored Sewer Surge book."""

    def reset_seed(self, sim: int = 0, seed_override=None) -> None:
        # The SDK supplies a deterministic simulation seed. Hash a game/version
        # namespace plus that value, then seed the SDK's shared Python RNG.
        source = sim if seed_override is None else seed_override
        digest = hashlib.sha256(f"sewer-surge:v1:{source}".encode("utf-8")).digest()
        self.seed_commitment = digest.hex()
        # Keep retry bookkeeping in the game layer. The pinned SDK commit does
        # not expose repeat_count on GeneralGameState.
        self._round_retry_index = 0
        # Older SDK GameState.reset_seed accepts only sim; newer snapshots may
        # accept an override. Reset SDK bookkeeping first, then seed the shared
        # Python RNG with our namespaced SHA-256 digest for deterministic replay.
        super().reset_seed(sim)
        random.seed(int.from_bytes(digest[:8], "big", signed=False))

    @contextmanager
    def _rng_substream(self, label: str, attempt: int = 0) -> Iterator[None]:
        """Temporarily isolate one deterministic RNG stream from all other work.

        The SDK helpers use Python's module-level random generator. Saving and
        restoring its state lets the board solver and payout sampler each use a
        seed derived independently from the simulation seed. Variable route
        search cannot consume random draws that shift the payout distribution.
        """
        previous_state = random.getstate()
        material = f"{self.seed_commitment}:{self.betmode}:{self.criteria}:{self._round_retry_index}:{attempt}:{label}"
        digest = hashlib.sha256(material.encode("utf-8")).digest()
        random.seed(int.from_bytes(digest[:8], "big", signed=False))
        try:
            yield
        finally:
            random.setstate(previous_state)

    def reset_book(self) -> None:
        super().reset_book()
        self.pipe_rotations = [[0 for _ in range(5)] for _ in range(5)]  # [column][row]
        self.inlet = 0
        self.scatter_count = 0
        self.scatter_tier = "none"
        self.payout_multiplier = 0.0

    def assign_special_sym_function(self) -> None:
        # W and S receive their SDK special flags from Config.special_symbols.
        # There are intentionally no multiplier or symbol-side payout functions.
        self.special_symbol_functions = {}

    @staticmethod
    def _base_openings(symbol: str) -> set[str]:
        return {
            "I": {"E", "W"},
            "L": {"S", "E"},
            "T": {"E", "W", "S"},
            "X": {"N", "E", "S", "W"},
            "W": {"N", "E", "S", "W"},
            "S": set(),
        }[symbol]

    @classmethod
    def _has_west_opening(cls, symbol: str, rotation: int) -> bool:
        if symbol == "S":
            return False
        if symbol == "W":
            return True
        order = ["N", "E", "S", "W"]
        return any(order[(order.index(side) + rotation) % 4] == "W" for side in cls._base_openings(symbol))

    @classmethod
    def _rotated_openings(cls, symbol: str, rotation: int) -> set[str]:
        order = ["N", "E", "S", "W"]
        return {
            order[(order.index(side) + rotation) % 4]
            for side in cls._base_openings(symbol)
        }

    @classmethod
    def _rotations_for_connection(cls, symbol: str, entry: str, exit_side: str) -> list[int]:
        if symbol in {"S"}:
            return []
        rotations = []
        for rotation in range(1 if symbol == "W" else 4):
            openings = cls._rotated_openings(symbol, rotation)
            if entry in openings and exit_side in openings:
                rotations.append(rotation)
        return rotations

    def _find_solvable_route(self) -> tuple[int, list[tuple[int, int, int]]] | None:
        """Find a west-to-east route with at least one interactive junction.

        Search is server-side and only sets initial pipe rotations/inlet metadata.
        It does not inspect or alter the round payout.
        """
        opposite = {"N": "S", "E": "W", "S": "N", "W": "E"}
        step = {"E": (1, 0), "N": (0, -1), "S": (0, 1)}
        start_rows = list(range(5))
        random.shuffle(start_rows)
        exit_order = ["E", "N", "S"]

        for inlet_row in start_rows:
            visited: set[tuple[int, int]] = set()

            def search(
                row: int,
                col: int,
                entry: str,
                has_junction: bool,
            ) -> list[tuple[int, int, int]] | None:
                if (row, col) in visited:
                    return None
                symbol = self.board[col][row].name
                if symbol == "S":
                    return None
                visited.add((row, col))
                directions = exit_order.copy()
                random.shuffle(directions)
                for exit_side in directions:
                    rotations = self._rotations_for_connection(symbol, entry, exit_side)
                    if not rotations:
                        continue
                    random.shuffle(rotations)
                    dx, dy = step[exit_side]
                    next_col, next_row = col + dx, row + dy
                    for rotation in rotations:
                        junction_here = len(self._rotated_openings(symbol, rotation)) > 2
                        if exit_side == "E" and col == 4:
                            if has_junction or junction_here:
                                visited.remove((row, col))
                                return [(row, col, rotation)]
                            continue
                        if not (0 <= next_col < 5 and 0 <= next_row < 5):
                            continue
                        child = search(
                            next_row,
                            next_col,
                            opposite[exit_side],
                            has_junction or junction_here,
                        )
                        if child is not None:
                            visited.remove((row, col))
                            return [(row, col, rotation), *child]
                visited.remove((row, col))
                return None

            # Search from west-edge entry. Requiring one T/X/W on the route
            # guarantees at least one branchable junction for the player.
            route = search(inlet_row, 0, "W", False)
            if route:
                for row, col, rotation in route:
                    self.pipe_rotations[col][row] = rotation
                return inlet_row, route
        return None

    def _configure_interactive_junction(self, route: list[tuple[int, int, int]]) -> bool:
        """Orient one off-route neighbour so a route junction has a real branch.

        A T/X/W symbol alone is not enough: its alternative port must connect
        to an adjacent pipe in the final, serialized board. This makes the
        branch control visible and usable in the frontend.
        """
        opposite = {"N": "S", "E": "W", "S": "N", "W": "E"}
        step = {"E": (1, 0), "N": (0, -1), "S": (0, 1)}
        route_positions = {(row, col) for row, col, _ in route}

        for index, (row, col, rotation) in enumerate(route):
            symbol = self.board[col][row].name
            if symbol not in {"T", "X", "W"}:
                continue
            openings = self._rotated_openings(symbol, rotation)
            if index == 0:
                entry = "W"
            else:
                previous_row, previous_col, _ = route[index - 1]
                if previous_col < col:
                    entry = "W"
                elif previous_col > col:
                    entry = "E"
                elif previous_row < row:
                    entry = "N"
                else:
                    entry = "S"
            if index == len(route) - 1:
                exit_side = "E"
            else:
                next_row, next_col, _ = route[index + 1]
                if next_col > col:
                    exit_side = "E"
                elif next_col < col:
                    exit_side = "W"
                elif next_row < row:
                    exit_side = "N"
                else:
                    exit_side = "S"

            for side in ("E", "N", "S"):
                if side not in openings or side in {entry, exit_side}:
                    continue
                if side == "E" and col == 4:
                    return True  # second valid choice is the east outlet
                dx, dy = step[side]
                next_col, next_row = col + dx, row + dy
                if not (0 <= next_col < 5 and 0 <= next_row < 5):
                    continue
                if (next_row, next_col) in route_positions:
                    continue
                neighbour_symbol = self.board[next_col][next_row].name
                candidate_rotations = [
                    candidate
                    for candidate in range(1 if neighbour_symbol == "W" else 4)
                    if opposite[side] in self._rotated_openings(neighbour_symbol, candidate)
                ]
                if not candidate_rotations:
                    continue
                self.pipe_rotations[next_col][next_row] = random.choice(candidate_rotations)
                return True
        return False

    def _assign_pipe_rotations_and_inlet(self) -> bool:
        # Wild is a universal, non-rotatable connector; scatter is not pipe.
        for col in range(5):
            for row in range(5):
                symbol = self.board[col][row].name
                self.pipe_rotations[col][row] = 0 if symbol in {"W", "S"} else random.randrange(4)

        result = self._find_solvable_route()
        if result is None:
            return False
        self.inlet, self.route_path = result
        return self._configure_interactive_junction(self.route_path)

    def _get_scatter_tier(self, count: int) -> str:
        if count >= 4:
            return "deep-run"
        if count == 3:
            return "bonus"
        return "none"

    def _build_row_major_board(self) -> list[list[dict[str, Any]]]:
        return [
            [
                {
                    "t": self.board[col][row].name,
                    "r": self.pipe_rotations[col][row],
                    "s": self.board[col][row].name == "S",
                }
                for col in range(5)
            ]
            for row in range(5)
        ]

    def _emit_sewer_events(self) -> None:
        board_rows = self._build_row_major_board()
        payload = {
            "board": board_rows,
            "inlet": self.inlet,
            "scatterCount": self.scatter_count,
            "scatterTier": self.scatter_tier,
            "waterEntry": "west",
            "waterExit": "east",
            "routeAuthority": "visual-only",
            "schemaVersion": 1,
        }
        validate_round_payload(
            {
                **payload,
                "payoutMultiplier": self.payout_multiplier,
            },
            max_win=self.config.wincap,
        )

        # The ordinary reveal event remains present for SDK/RGS compatibility.
        reveal_event(self)
        self.book.add_event(
            {
                "index": len(self.book.events),
                "type": "sewerBoard",
                **payload,
            }
        )
        if self.scatter_tier != "none":
            self.record(
                {
                    "kind": self.scatter_count,
                    "symbol": "scatter",
                    "gametype": self.gametype,
                    "sewerTier": self.scatter_tier,
                }
            )
            self.book.add_event(
                {
                    "index": len(self.book.events),
                    "type": "sewerFeature",
                    "feature": self.scatter_tier,
                    "scatterCount": self.scatter_count,
                    "routeAuthority": "visual-only",
                }
            )

    def _select_authoritative_payout(self) -> float:
        conditions = self.get_current_distribution_conditions()
        if "payout_weights" not in conditions:
            raise RuntimeError(f"Missing payout_weights for criteria={self.criteria}")
        # This stream is independent of board/reel generation and the variable-
        # length route solver. The attempt index is the accepted/rejected round
        # retry count, so rejections still produce deterministic fresh samples.
        with self._rng_substream("payout"):
            amount = float(get_random_outcome(conditions["payout_weights"]))
        amount = round(amount, 1)
        if amount < 0 or amount > self.config.wincap:
            raise ValueError(f"Payout outside allowed range: {amount}")
        return amount

    def check_repeat(self) -> None:
        if not self.repeat:
            expected = {
                "0": "none",
                "basegame": "none",
                "bonus": "bonus",
                "deep_run": "deep-run",
                # A normal Bonus Buy reaches the win cap inside the normal tier.
                "wincap": "bonus" if self.betmode == "bonus" else "deep-run",
            }.get(self.criteria)
            if expected is None or self.scatter_tier != expected:
                self.repeat = True
        super().check_repeat()

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        self.reset_seed(sim, simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            route_found = False
            # Board symbols are visual puzzle pieces. Reject a board that has
            # no left-to-right route with a branchable junction; payout
            # selection remains downstream and independent of this search.
            for _attempt in range(100):
                # Isolate the entire visual board puzzle search from payout RNG.
                with self._rng_substream("board", _attempt):
                    self.draw_board(emit_event=False)
                    route_found = self._assign_pipe_rotations_and_inlet()
                if route_found:
                    break
            if not route_found:
                raise RuntimeError("Unable to draw a solvable 5x5 sewer board after 100 attempts")
            self.scatter_count = self.count_special_symbols("scatter")
            self.scatter_tier = self._get_scatter_tier(self.scatter_count)
            self.triggered_freegame = self.scatter_tier != "none"
            self.payout_multiplier = self._select_authoritative_payout()
            self._emit_sewer_events()

            # Every Sewer Surge award is booked as the result of this one
            # server-side round. It is never recomputed from route interaction.
            # A feature is still one pre-calculated RGS outcome, not a sequence
            # of free spins. Assign its entire award to the SDK's freegame ledger
            # so the SDK can distinguish trigger/base reveal from feature value.
            # The basegame reveal itself carries no additional payout.
            self.win_manager.update_spinwin(self.payout_multiplier)
            self.win_manager.update_gametype_wins(
                self.config.freegame_type if self.scatter_tier != "none" else self.config.basegame_type
            )
            self.book.add_event(
                {
                    "index": len(self.book.events),
                    "type": "sewerAward",
                    "amount": int(round(self.payout_multiplier * 100)),
                    "payoutMultiplier": int(round(self.payout_multiplier * 100)),
                    "scatterTier": self.scatter_tier,
                    "maxWinCapped": self.payout_multiplier >= self.config.wincap,
                }
            )
            # Follow the SDK convention: emit wincap before setWin; the
            # standard set_win_event helper intentionally suppresses setWin
            # once the win cap has been reached.
            self.evaluate_wincap()
            set_win_event(self)
            set_total_event(self)
            self.evaluate_finalwin()
            self.check_repeat()
            if self.repeat:
                self._round_retry_index += 1

        self.imprint_wins()

    def run_freespin(self) -> None:
        """SDK abstract hook; Sewer Surge features are resolved in run_spin().

        This game does not run classic free-spin sequences. The Bonus/Deep Run
        event and authoritative award are emitted during run_spin, so calling
        this hook would indicate a caller incorrectly tried to re-enter the
        classic free-spin lifecycle.
        """
        raise RuntimeError(
            "Sewer Surge Bonus and Deep Run are single-round book features; "
            "they must be resolved by run_spin(), not run_freespin()."
        )
