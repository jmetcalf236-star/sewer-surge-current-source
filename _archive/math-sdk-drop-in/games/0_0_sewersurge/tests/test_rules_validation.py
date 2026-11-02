import pytest
from rules_validation import scatter_tier, validate_round_payload


def make_board(scatter_count=0):
    board = [[{"t": "I", "r": 0, "s": False} for _ in range(5)] for _ in range(5)]
    board[2][2] = {"t": "T", "r": 0, "s": False}  # W/E/S tee on the playable route
    board[3][2] = {"t": "I", "r": 1, "s": False}  # north/south pipe connects the tee's second branch
    for idx in range(scatter_count):
        row, col = divmod(idx + 6, 5)
        board[row][col] = {"t": "S", "r": 0, "s": True}
    return board


def make_payload(scatter_count=0, **updates):
    payload = {
        "schemaVersion": 1,
        "board": make_board(scatter_count),
        "inlet": 2,
        "scatterCount": scatter_count,
        "scatterTier": scatter_tier(scatter_count),
        "payoutMultiplier": 12.5,
        "waterEntry": "west",
        "waterExit": "east",
        "routeAuthority": "visual-only",
    }
    payload.update(updates)
    return payload


def test_scatter_tier_boundaries():
    assert [scatter_tier(n) for n in range(6)] == ["none", "none", "none", "bonus", "deep-run", "deep-run"]
    with pytest.raises(ValueError):
        scatter_tier(True)


def test_valid_round_accepts_5x5_server_payload():
    validate_round_payload(make_payload(3))


@pytest.mark.parametrize("updates", [
    {"board": []},
    {"inlet": 5},
    {"inlet": True},
    {"payoutMultiplier": 10000.1},
    {"payoutMultiplier": 0.15},
    {"payoutMultiplier": True},
    {"payoutMultiplier": float("nan")},
    {"waterEntry": "north"},
    {"routeAuthority": "player-selected"},
    {"schemaVersion": 2},
])
def test_malformed_rounds_are_rejected(updates):
    with pytest.raises(ValueError):
        validate_round_payload(make_payload(**updates))


def test_wrong_scatter_tier_is_rejected():
    with pytest.raises(ValueError, match="scatterTier"):
        validate_round_payload(make_payload(4, scatterTier="bonus"))


def test_scatter_count_mismatch_is_rejected():
    with pytest.raises(ValueError, match="scatterCount"):
        validate_round_payload(make_payload(3, scatterCount=2))


def test_wild_and_scatter_are_not_rotatable():
    board = make_board()
    board[0][0] = {"t": "W", "r": 1, "s": False}
    with pytest.raises(ValueError, match="not rotatable"):
        validate_round_payload(make_payload(board=board))


def test_inlet_cannot_be_scatter():
    board = make_board()
    board[2][0] = {"t": "S", "r": 0, "s": True}
    with pytest.raises(ValueError, match="inlet"):
        validate_round_payload(make_payload(board=board, scatterCount=1, scatterTier="none"))


def test_inlet_pipe_must_open_to_west():
    board = make_board()
    # An unrotated tee has N/E/W? In this game's definition tee opens E/W/S.
    # Use an elbow facing south/east to prove a closed west inlet is rejected.
    board[2][0] = {"t": "L", "r": 0, "s": False}
    with pytest.raises(ValueError, match="west-facing"):
        validate_round_payload(make_payload(board=board))


def test_inlet_pipe_can_be_rotated_to_open_west():
    board = make_board()
    board[2][0] = {"t": "L", "r": 2, "s": False}  # west+north
    board[1][0] = {"t": "L", "r": 0, "s": False}  # south+east turn into horizontal row
    board[1][2] = {"t": "T", "r": 0, "s": False}  # W/E/S tee on the route
    board[2][2] = {"t": "I", "r": 1, "s": False}  # vertical neighbour exposes its north port
    validate_round_payload(make_payload(board=board))


def test_inlet_pipe_must_expose_west_port():
    board = make_board()
    board[2][0] = {"t": "L", "r": 0, "s": False}
    with pytest.raises(ValueError, match="west-facing"):
        validate_round_payload(make_payload(board=board))


def test_inlet_pipe_can_rotate_to_expose_west_port():
    board = make_board()
    board[2][0] = {"t": "L", "r": 2, "s": False}  # west+north
    board[1][0] = {"t": "L", "r": 0, "s": False}  # south+east turn into horizontal row
    board[1][2] = {"t": "T", "r": 0, "s": False}  # W/E/S tee on the route
    board[2][2] = {"t": "I", "r": 1, "s": False}  # vertical neighbour exposes its north port
    validate_round_payload(make_payload(board=board))


def test_route_validation_rejects_route_that_must_double_back_west():
    board = make_board()
    # The only connected route from the inlet to the outlet is:
    # (2,0) -> (2,1) -> (1,1) -> (1,0) -> (0,0) -> (0,1...
    # It requires a westward move from (1,1) to (1,0), so it is not a legal
    # left-to-right water route. The rest of the grid is deliberately closed.
    board[2][0] = {"t": "T", "r": 0, "s": False}       # W/E/S
    board[2][1] = {"t": "L", "r": 2, "s": False}       # W/N
    board[1][1] = {"t": "L", "r": 1, "s": False}       # W/S
    board[1][0] = {"t": "L", "r": 3, "s": False}       # E/N
    board[0][0] = {"t": "L", "r": 0, "s": False}       # S/E
    board[0][1] = {"t": "I", "r": 0, "s": False}       # W/E
    with pytest.raises(ValueError, match="connected branchable junction"):
        validate_round_payload(make_payload(board=board))


def test_route_must_include_a_branchable_junction():
    board = make_board()
    board[2][2] = {"t": "I", "r": 0, "s": False}
    board[3][2] = {"t": "I", "r": 0, "s": False}
    board[0][4] = {"t": "T", "r": 0, "s": False}  # junction exists, but not on the route
    with pytest.raises(ValueError, match="connected branchable junction"):
        validate_round_payload(make_payload(board=board))
