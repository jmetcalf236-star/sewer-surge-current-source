"""Strict validation for Sewer Surge custom Math SDK book payloads."""
from __future__ import annotations

import math

VALID_PIPE_TYPES = {"I", "L", "T", "X", "W", "S"}
MAX_ROWS = 5
MAX_COLS = 5


def scatter_tier(count: int) -> str:
    if type(count) is not int or count < 0:
        raise ValueError("scatter count must be a non-negative integer")
    if count >= 4:
        return "deep-run"
    if count == 3:
        return "bonus"
    return "none"


def find_west_to_east_route(board: list[list[dict]], inlet: int) -> list[tuple[int, int]] | None:
    """Find a simple eastward route with at least one connected branch point."""
    base_openings = {
        "I": {"E", "W"}, "L": {"S", "E"}, "T": {"E", "W", "S"},
        "X": {"N", "E", "S", "W"}, "W": {"N", "E", "S", "W"}, "S": set(),
    }
    directions = ["N", "E", "S", "W"]
    opposite = {"N": "S", "E": "W", "S": "N", "W": "E"}
    step = {"N": (0, -1), "E": (1, 0), "S": (0, 1)}

    def ports(cell: dict) -> set[str]:
        return {directions[(directions.index(side) + cell["r"]) % 4] for side in base_openings[cell["t"]]}

    visited: set[tuple[int, int]] = set()
    path: list[tuple[int, int]] = []

    def search(row: int, col: int, entry: str, has_branch: bool) -> list[tuple[int, int]] | None:
        position = (row, col)
        if position in visited:
            return None
        current_ports = ports(board[row][col])
        if entry not in current_ports:
            return None
        visited.add(position)
        path.append(position)

        outgoing: list[str] = []
        for direction in current_ports - {entry}:
            if direction == "W":
                continue
            if direction == "E" and col == MAX_COLS - 1:
                outgoing.append(direction)
                continue
            dx, dy = step[direction]
            next_col, next_row = col + dx, row + dy
            if 0 <= next_col < MAX_COLS and 0 <= next_row < MAX_ROWS:
                if opposite[direction] in ports(board[next_row][next_col]):
                    outgoing.append(direction)

        branch_here = len(outgoing) > 1
        has_branch = has_branch or branch_here
        for direction in outgoing:
            if direction == "E" and col == MAX_COLS - 1:
                if has_branch:
                    return path.copy()
                continue
            dx, dy = step[direction]
            next_col, next_row = col + dx, row + dy
            result = search(next_row, next_col, opposite[direction], has_branch)
            if result is not None:
                return result

        path.pop()
        visited.remove(position)
        return None

    return search(inlet, 0, "W", False)


def has_west_to_east_route(board: list[list[dict]], inlet: int) -> bool:
    """Return whether a west-to-east route exists under the game movement rules."""
    return find_west_to_east_route(board, inlet) is not None


def validate_round_payload(payload: dict, max_win: float = 10_000.0) -> None:
    """Reject malformed/non-authoritative round data before adding custom events."""
    if not isinstance(payload, dict):
        raise ValueError("Round payload must be an object")
    if payload.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    if payload.get("waterEntry") != "west" or payload.get("waterExit") != "east":
        raise ValueError("water must enter west and exit east")
    if payload.get("routeAuthority") != "visual-only":
        raise ValueError("routeAuthority must remain visual-only")

    board = payload.get("board")
    if not isinstance(board, list) or len(board) != MAX_ROWS:
        raise ValueError("board must be five rows")
    if any(not isinstance(row, list) or len(row) != MAX_COLS for row in board):
        raise ValueError("board must be a 5x5 row-major grid")

    scatters = 0
    for row in board:
        for cell in row:
            if not isinstance(cell, dict):
                raise ValueError("each board cell must be an object")
            symbol = cell.get("t")
            rotation = cell.get("r")
            if symbol not in VALID_PIPE_TYPES:
                raise ValueError(f"unknown symbol: {symbol!r}")
            if type(rotation) is not int or rotation not in (0, 1, 2, 3):
                raise ValueError("rotation must be an integer in [0, 3]")
            if symbol in {"W", "S"} and rotation != 0:
                raise ValueError("wild and scatter symbols are not rotatable")
            is_scatter = cell.get("s")
            if not isinstance(is_scatter, bool):
                raise ValueError("scatter flag must be boolean")
            if is_scatter != (symbol == "S"):
                raise ValueError("scatter flag must agree with symbol S")
            scatters += int(is_scatter)

    inlet = payload.get("inlet")
    if type(inlet) is not int or inlet < 0 or inlet >= MAX_ROWS:
        raise ValueError("inlet must identify a row from 0 to 4")
    inlet_cell = board[inlet][0]
    if inlet_cell["t"] == "S":
        raise ValueError("inlet cannot start on a scatter tile")

    # The selected left-edge inlet must physically expose a west-facing port.
    # Rotation is clockwise in quarter-turns, matching GameState's board logic.
    base_openings = {
        "I": {"E", "W"},
        "L": {"S", "E"},
        "T": {"E", "W", "S"},
        "X": {"N", "E", "S", "W"},
        "W": {"N", "E", "S", "W"},
        "S": set(),
    }
    directions = ["N", "E", "S", "W"]
    rotated_openings = {
        directions[(directions.index(side) + inlet_cell["r"]) % 4]
        for side in base_openings[inlet_cell["t"]]
    }
    if "W" not in rotated_openings:
        raise ValueError("inlet pipe must expose a west-facing opening")
    route = find_west_to_east_route(board, inlet)
    if route is None:
        raise ValueError("initial pipe rotations must connect west inlet to east outlet through a connected branchable junction")

    count = payload.get("scatterCount")
    if type(count) is not int or count != scatters:
        raise ValueError("scatterCount does not match board")
    tier = payload.get("scatterTier")
    if tier != scatter_tier(scatters):
        raise ValueError("scatterTier does not match scatter count")

    payout = payload.get("payoutMultiplier")
    if isinstance(payout, bool) or not isinstance(payout, (int, float)) or not math.isfinite(payout):
        raise ValueError("payoutMultiplier must be a finite number")
    if payout < 0 or payout > max_win:
        raise ValueError("payoutMultiplier outside allowed range")
    if round(float(payout) * 10) != float(payout) * 10:
        raise ValueError("payoutMultiplier must use 0.1x increments")
