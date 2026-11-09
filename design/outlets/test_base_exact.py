import unittest
from fractions import Fraction

from base_exact import (
    DENOMINATOR, HIT_PROBABILITY, MAX_WIN_TENTHS_X, PRIZES_TENTHS_X,
    TARGET_RTP, build_table, exact_metrics, sample_rows, weighted_quantile,
)


class ExactVisiblePaytableTests(unittest.TestCase):
    def setUp(self):
        self.table = build_table()
        self.metrics = exact_metrics(self.table)

    def test_positive_only_visible_variety_and_smooth_decreasing_weights(self):
        self.assertEqual(len(PRIZES_TENTHS_X), 14)
        self.assertEqual(len(set(PRIZES_TENTHS_X)), 14)
        self.assertTrue(all(prize >= 10 for prize in PRIZES_TENTHS_X))
        self.assertEqual(PRIZES_TENTHS_X[0], 10)
        self.assertEqual(PRIZES_TENTHS_X[-1], MAX_WIN_TENTHS_X)
        self.assertEqual(sum(self.table.weights), DENOMINATOR)
        self.assertTrue(all(self.table.weights[i] > self.table.weights[i + 1]
                            for i in range(len(self.table.weights) - 1)))

    def test_individual_and_largest_two_weight_limits(self):
        self.assertLess(Fraction(max(self.table.weights), DENOMINATOR), Fraction(3, 10))
        self.assertLess(Fraction(sum(self.table.weights[:2]), DENOMINATOR), Fraction(1, 2))

    def test_exact_hit_rate_rtp_and_conditional_mean(self):
        self.assertEqual(self.table.hit_probability, Fraction(3, 10))
        self.assertEqual(self.metrics["hit_rate"], HIT_PROBABILITY)
        self.assertEqual(self.metrics["rtp"], TARGET_RTP)
        self.assertEqual(self.metrics["mean_prize_x"], Fraction(193, 60))
        self.assertEqual(self.metrics["rtp"],
                         self.metrics["hit_rate"] * self.metrics["mean_prize_x"])

    def test_top_prize_display_and_paid_frequencies_exactly(self):
        self.assertEqual(self.table.weights[-1], 1)
        self.assertEqual(self.metrics["top_display_per_outlet"], Fraction(1, 1_500_000))
        self.assertEqual(self.metrics["top_paid_per_spin"], Fraction(1, 5_000_000))
        self.assertEqual(self.metrics["top_paid_per_outlet"], Fraction(1, 25_000_000))
        self.assertEqual(self.metrics["top_rtp_contribution_x"], Fraction(1, 100))
        self.assertEqual(self.metrics["top_display_any_row"],
                         1 - (1 - Fraction(1, 1_500_000)) ** 5)

    def test_median_and_tail_percentiles(self):
        self.assertEqual(weighted_quantile(self.table, Fraction(1, 2)), Fraction(2, 1))
        self.assertEqual(weighted_quantile(self.table, Fraction(9, 10)), Fraction(5, 1))
        self.assertEqual(weighted_quantile(self.table, Fraction(99, 100)), Fraction(20, 1))

    def test_ge100_and_1000_top_display_and_paid_probabilities(self):
        p_ge100 = Fraction(2403, 1_500_000)
        p_1000 = Fraction(3, 50_000)
        p_top = Fraction(1, 1_500_000)
        self.assertEqual(self.metrics["p_ge100_per_outlet"], p_ge100)
        self.assertEqual(self.metrics["p_ge100_any_row"], 1 - (1 - p_ge100) ** 5)
        self.assertEqual(self.metrics["p_ge100_paid_per_spin"], Fraction(2403, 5_000_000))
        self.assertEqual(self.metrics["p1000_per_outlet"], p_1000)
        self.assertEqual(self.metrics["p1000_or_top_any_row"],
                         1 - (1 - p_1000 - p_top) ** 5)
        self.assertEqual(self.metrics["p1000_paid_per_spin"], Fraction(9, 500_000))
        self.assertEqual(self.metrics["p1000_or_top_paid_per_spin"], Fraction(91, 5_000_000))

    def test_every_award_is_in_tenths_of_x(self):
        self.assertTrue(self.metrics["payouts_multiple_of_0_1x"])
        self.assertTrue(all(isinstance(prize, int) for prize in self.table.prizes_tenths_x))

    def test_sample_rows_are_repeatable_five_positive_prizes(self):
        sample = sample_rows(self.table, count=20, seed=20261102)
        self.assertEqual(len(sample), 20)
        self.assertEqual(sample, sample_rows(self.table, count=20, seed=20261102))
        for row in sample:
            self.assertEqual(len(row), 5)
            self.assertTrue(all(prize >= 10 for prize in row))


if __name__ == "__main__":
    unittest.main(verbosity=2)
