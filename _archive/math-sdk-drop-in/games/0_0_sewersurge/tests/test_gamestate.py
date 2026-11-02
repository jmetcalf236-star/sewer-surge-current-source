"""Integration checks against the copied official Math SDK classes."""
from game_config import GameConfig
from gamestate import GameState
from rules_validation import has_west_to_east_route


def run_round(criteria, sim=17, seed=20261101):
    config = GameConfig()
    state = GameState(config)
    state.betmode = "base"
    state.criteria = criteria
    state.run_spin(sim, seed)
    return state.book.to_json()


def test_seeded_sdk_round_replays_identically():
    first = run_round("bonus")
    second = run_round("bonus")
    assert first == second


def test_official_sdk_books_contain_authoritative_sewer_payload():
    for criteria in ("0", "basegame", "bonus", "deep_run", "wincap"):
        book = run_round(criteria, sim=29, seed=8821)
        sewer_board = next(event for event in book["events"] if event["type"] == "sewerBoard")
        sewer_award = next(event for event in book["events"] if event["type"] == "sewerAward")
        assert len(sewer_board["board"]) == 5
        assert all(len(row) == 5 for row in sewer_board["board"])
        assert sewer_board["scatterTier"] in {"none", "bonus", "deep-run"}
        assert has_west_to_east_route(sewer_board["board"], sewer_board["inlet"])
        assert sewer_award["payoutMultiplier"] == book["payoutMultiplier"]
        assert 0 <= book["payoutMultiplier"] <= 1_000_000
        assert book["payoutMultiplier"] % 10 == 0


def test_scatter_count_matches_feature_tier_in_sdk_book():
    for criteria, expected in (("bonus", 3), ("deep_run", None), ("wincap", None)):
        book = run_round(criteria, sim=31, seed=10101)
        event = next(event for event in book["events"] if event["type"] == "sewerBoard")
        actual = sum(cell["s"] for row in event["board"] for cell in row)
        assert event["scatterCount"] == actual
        if expected is not None:
            assert actual == expected
        if criteria in {"deep_run", "wincap"}:
            assert actual >= 4


def test_max_win_uses_official_sdk_wincap_event():
    book = run_round("wincap", sim=41, seed=501)
    event_types = [event["type"] for event in book["events"]]
    assert "wincap" in event_types
    assert "setWin" not in event_types
    assert book["payoutMultiplier"] == 1_000_000
    cap_event = next(event for event in book["events"] if event["type"] == "wincap")
    assert cap_event["amount"] == 1_000_000


def test_payout_substream_is_independent_of_visual_board_random_draws():
    import random

    first_config = GameConfig()
    first = GameState(first_config)
    first.betmode = "base"
    first.criteria = "bonus"
    first.reset_seed(101, 987654321)
    first.reset_book()
    expected = first._select_authoritative_payout()

    second_config = GameConfig()
    second = GameState(second_config)
    second.betmode = "base"
    second.criteria = "bonus"
    second.reset_seed(101, 987654321)
    second.reset_book()
    # Simulate an arbitrarily large and variable amount of RNG use in the
    # board renderer/route solver before selecting the server-side payout.
    random.seed(123)
    for _ in range(10_000):
        random.random()
    actual = second._select_authoritative_payout()

    assert actual == expected


def test_feature_payout_is_booked_to_sdk_freegame_ledger():
    bonus_book = run_round("bonus", sim=121, seed=444)
    assert bonus_book["baseGameWins"] == 0.0
    assert round(bonus_book["freeGameWins"] * 100) == bonus_book["payoutMultiplier"]


def test_non_feature_payout_is_booked_to_sdk_basegame_ledger():
    base_book = run_round("basegame", sim=122, seed=445)
    assert round(base_book["baseGameWins"] * 100) == base_book["payoutMultiplier"]
    assert base_book["freeGameWins"] == 0.0


def test_rng_substreams_do_not_depend_on_newer_sdk_repeat_count_attribute():
    config = GameConfig()
    state = GameState(config)
    state.betmode = "base"
    state.criteria = "bonus"
    state.reset_seed(202, 303)
    assert hasattr(state, "_round_retry_index")
    # This SDK generation intentionally has no GeneralGameState.repeat_count.
    if hasattr(state, "repeat_count"):
        delattr(state, "repeat_count")
    with state._rng_substream("payout"):
        import random
        draw = random.random()
    assert isinstance(draw, float)
