import random
import unittest

from flow import (
    Board, Pipe, NORTH, EAST, SOUTH, WEST, board_from_outlet_rows,
    compute_payout, ports_for, trace_flow,
)


def blank_board():
    return Board(tuple(tuple(None for _ in range(5)) for _ in range(5)))


class FlowTests(unittest.TestCase):
    def test_rotation_has_four_quarter_turns_and_returns(self):
        self.assertEqual(ports_for("I", 0), EAST | WEST)
        self.assertEqual(ports_for("I", 1), NORTH | SOUTH)
        self.assertEqual(ports_for("L", 0), SOUTH | EAST)
        self.assertEqual(ports_for("T", 0), EAST | WEST | SOUTH)
        self.assertEqual(ports_for("T", 1), NORTH | SOUTH | WEST)
        self.assertEqual(ports_for("X", 3), NORTH | EAST | SOUTH | WEST)
        for kind in "ILTX":
            self.assertEqual(ports_for(kind, 4), ports_for(kind, 0))

    def test_dead_end_pays_zero(self):
        payout, trace = compute_payout(blank_board(), [100] * 5, split=False)
        self.assertEqual(payout, 0)
        self.assertTrue(trace.dead_end)
        self.assertEqual(trace.reached_outlets, ())

    def test_single_stream_reaches_only_one_of_multiple_outlets(self):
        board = board_from_outlet_rows((0, 1, 3, 4), rng=random.Random(4))
        trace = trace_flow(board, split=False, rng=random.Random(9))
        self.assertEqual(len(trace.reached_outlets), 1)

    def test_bonus_splits_and_pays_every_reached_outlet(self):
        rows = (0, 1, 3, 4)
        board = board_from_outlet_rows(rows, rng=random.Random(10))
        payout, trace = compute_payout(board, [10, 20, 30, 40, 50], split=True)
        self.assertEqual(trace.reached_outlets, rows)
        self.assertEqual(payout, 10 + 20 + 40 + 50)

    def test_super_valve_products_apply_per_outlet_path(self):
        rows = (0, 4)
        board = board_from_outlet_rows(rows, rng=random.Random(3), valves_by_row={0: 2, 4: 5})
        payout, trace = compute_payout(board, [10, 0, 0, 0, 20], split=True)
        self.assertEqual(trace.reached_outlets, rows)
        self.assertEqual(payout, 10 * 2 + 20 * 5)

    def test_total_round_cap_applies_after_summing_all_outlets(self):
        rows = (0, 1, 2, 3, 4)
        board = board_from_outlet_rows(rows, rng=random.Random(17), valves_by_row={r: 10 for r in rows})
        payout, _ = compute_payout(board, [50_000] * 5, split=True, cap=100_000)
        self.assertEqual(payout, 100_000)

    def test_all_payouts_are_in_tenths_of_x(self):
        board = board_from_outlet_rows((2,), rng=random.Random(22))
        payout, _ = compute_payout(board, [123, 0, 0, 0, 0], split=False)
        self.assertIsInstance(payout, int)


if __name__ == "__main__":
    unittest.main(verbosity=2)
