"""Pure, deterministic sewer-pipe flow and outlet-payout model.

Coordinates are (row, column), with row 0 at the top.  Rotation is clockwise,
in quarter turns, and uses the current Sewer Surge port definitions:
I=E/W, L=S/E, T=E/W/S, X=N/E/S/W before rotation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Mapping, Sequence

ROWS = 5
COLS = 5
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
DIRS = (NORTH, EAST, SOUTH, WEST)
DELTAS = {NORTH: (-1, 0), EAST: (0, 1), SOUTH: (1, 0), WEST: (0, -1)}
OPPOSITE = {NORTH: SOUTH, EAST: WEST, SOUTH: NORTH, WEST: EAST}
BASE_PORTS = {
    "I": EAST | WEST,
    "L": SOUTH | EAST,
    "T": EAST | WEST | SOUTH,
    "X": NORTH | EAST | SOUTH | WEST,
}


def rotate_ports(ports: int, rotation: int) -> int:
    """Rotate a four-bit N/E/S/W port mask clockwise by 0..3 quarter turns."""
    result = ports
    for _ in range(rotation % 4):
        result = ((result << 1) & 0b1111) | ((result >> 3) & 1)
    return result


def ports_for(tile_type: str, rotation: int = 0) -> int:
    if tile_type not in BASE_PORTS:
        raise ValueError(f"unsupported pipe type: {tile_type!r}")
    return rotate_ports(BASE_PORTS[tile_type], rotation)


@dataclass(frozen=True)
class Pipe:
    tile_type: str
    rotation: int = 0
    valve: int = 1

    @property
    def ports(self) -> int:
        return ports_for(self.tile_type, self.rotation)


@dataclass(frozen=True)
class Board:
    """A 5x5 board. None is an empty cell; valve is an integer multiplier."""
    cells: tuple[tuple[Pipe | None, ...], ...]
    inlet_row: int = 2

    def __post_init__(self) -> None:
        if len(self.cells) != ROWS or any(len(row) != COLS for row in self.cells):
            raise ValueError("board must be exactly 5x5")
        if not 0 <= self.inlet_row < ROWS:
            raise ValueError("inlet row must be 0..4")


@dataclass(frozen=True)
class FlowResult:
    reached_outlets: tuple[int, ...]
    visited: frozenset[tuple[int, int]]
    path_by_outlet: Mapping[int, tuple[tuple[int, int], ...]]
    dead_end: bool


def _connected_neighbors(board: Board, row: int, col: int):
    pipe = board.cells[row][col]
    if pipe is None:
        return
    for direction in DIRS:
        if not pipe.ports & direction:
            continue
        dr, dc = DELTAS[direction]
        nr, nc = row + dr, col + dc
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            continue
        neighbor = board.cells[nr][nc]
        if neighbor is not None and neighbor.ports & OPPOSITE[direction]:
            yield (nr, nc), direction


def trace_flow(board: Board, *, split: bool, rng=None) -> FlowResult:
    """Trace the west inlet.

    Split mode visits every connected branch. Single-stream mode follows one
    random connected continuation at T/X junctions (pass a seeded RNG for
    reproducible tests). An east outlet is reached only at column 4 with E open.
    For split mode, path_by_outlet is the shortest connected path, with N/E/S/W
    tie-breaking. This path is also the authoritative path for valve products.
    """
    start = (board.inlet_row, 0)
    first = board.cells[start[0]][start[1]]
    if first is None or not first.ports & WEST:
        return FlowResult((), frozenset(), {}, True)

    if not split:
        if rng is None:
            import random
            rng = random.Random(0)
        current = start
        incoming = WEST
        visited: set[tuple[int, int]] = set()
        path = []
        while current not in visited:
            row, col = current
            pipe = board.cells[row][col]
            if pipe is None:
                break
            visited.add(current)
            path.append(current)
            if col == COLS - 1 and pipe.ports & EAST:
                return FlowResult((row,), frozenset(visited), {row: tuple(path)}, False)
            choices = []
            for neighbor, direction in _connected_neighbors(board, row, col):
                if direction == incoming:
                    continue
                if neighbor not in visited:
                    choices.append((neighbor, OPPOSITE[direction]))
            if not choices:
                return FlowResult((), frozenset(visited), {}, True)
            current, incoming = rng.choice(choices)
        return FlowResult((), frozenset(visited), {}, True)

    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    outlets: dict[int, tuple[tuple[int, int], ...]] = {}
    while queue:
        current = queue.popleft()
        row, col = current
        pipe = board.cells[row][col]
        if pipe is None:
            continue
        if col == COLS - 1 and pipe.ports & EAST:
            path = []
            cursor: tuple[int, int] | None = current
            while cursor is not None:
                path.append(cursor)
                cursor = parent[cursor]
            outlets[row] = tuple(reversed(path))
        for neighbor, _direction in _connected_neighbors(board, row, col):
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)
    return FlowResult(
        tuple(sorted(outlets)), frozenset(parent), outlets, not bool(outlets)
    )


def compute_payout(
    board: Board,
    prizes_by_row: Sequence[int],
    *,
    split: bool,
    cap: int = 100_000,
    rng=None,
) -> tuple[int, FlowResult]:
    """Return capped payout in tenths of x plus the flow trace.

    Prize inputs and valve multipliers are represented in 0.1x units / integer
    factors respectively. Every reached outlet is paid once. The cap applies to
    the total round payout after summing outlets.
    """
    if len(prizes_by_row) != ROWS:
        raise ValueError("exactly five outlet prizes are required")
    if cap < 0 or any(prize < 0 for prize in prizes_by_row):
        raise ValueError("prizes and cap must be nonnegative")
    flow = trace_flow(board, split=split, rng=rng)
    total = 0
    for outlet_row in flow.reached_outlets:
        path = flow.path_by_outlet[outlet_row]
        product = 1
        for row, col in path:
            pipe = board.cells[row][col]
            if pipe is not None:
                product *= pipe.valve
        total += prizes_by_row[outlet_row] * product
    return min(total, cap), flow


def board_from_outlet_rows(
    outlet_rows: Sequence[int], *, rng, valves_by_row: Mapping[int, int] | None = None
) -> Board:
    """Generate a connected, reciprocal-port network from the west inlet to rows.

    Each outlet gets a randomized monotone path from (2,0) to (row,4). The union
    is encoded using only I/L/T/X pipe symbols and their quarter-turns. This is a
    design-study board constructor, not the game's production board generator.
    """
    valves_by_row = valves_by_row or {}
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    active: set[tuple[int, int]] = set()
    start = (2, 0)
    for target_row in outlet_rows:
        if not 0 <= target_row < ROWS:
            raise ValueError("outlet rows must be 0..4")
        row, col = start
        path = [start]
        while (row, col) != (target_row, COLS - 1):
            options = []
            if col < COLS - 1:
                options.append((row, col + 1))
            if row < target_row:
                options.append((row + 1, col))
            elif row > target_row:
                options.append((row - 1, col))
            row, col = rng.choice(options)
            path.append((row, col))
        active.update(path)
        for a, b in zip(path, path[1:]):
            edges.add((a, b) if a < b else (b, a))

    masks = {cell: 0 for cell in active}
    masks[start] |= WEST
    for target_row in outlet_rows:
        masks[(target_row, COLS - 1)] |= EAST
    for a, b in edges:
        ar, ac = a
        br, bc = b
        if br == ar - 1:
            direction = NORTH
        elif bc == ac + 1:
            direction = EAST
        elif br == ar + 1:
            direction = SOUTH
        else:
            direction = WEST
        masks[a] |= direction
        masks[b] |= OPPOSITE[direction]

    # Resolve each exact port mask to the current type + rotation vocabulary.
    encoded: dict[tuple[int, int], Pipe] = {}
    for cell, mask in masks.items():
        for tile_type in ("I", "L", "T", "X"):
            match = next((rotation for rotation in range(4)
                          if ports_for(tile_type, rotation) == mask), None)
            if match is not None:
                r, c = cell
                valve = valves_by_row.get(r, 1) if c == COLS - 1 and mask & EAST else 1
                encoded[cell] = Pipe(tile_type, match, valve)
                break
        else:
            raise ValueError(f"no I/L/T/X encoding for ports mask {mask:04b} at {cell}")
    cells = tuple(
        tuple(encoded.get((row, col)) for col in range(COLS)) for row in range(ROWS)
    )
    return Board(cells)
