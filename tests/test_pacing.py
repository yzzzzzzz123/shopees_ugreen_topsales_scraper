"""Shared pacing math; these checks do not claim live-site throughput."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/shopee-ugreen-topsales/scripts'))
from pacing import PACING_SPEED_MULTIPLIER, paced_wait_seconds


class PacingTests(unittest.TestCase):
    def test_every_wait_category_uses_the_same_multiplier(self):
        self.assertEqual(PACING_SPEED_MULTIPLIER, 2.5)
        for baseline, expected in (
            ((2, 3), (0.8, 1.2)), ((2, 4), (0.8, 1.6)),
            ((0.9, 2.4), (0.36, 0.96)), ((1, 2), (0.4, 0.8)),
            ((1.2, 2.5), (0.48, 1)), ((180, 300), (72, 120)),
            ((5, 10), (2, 4)),
        ):
            for old, new in zip(baseline, expected):
                self.assertAlmostEqual(paced_wait_seconds(old), new)

    def test_invalid_waits_are_rejected(self):
        for invalid in (True, None, '2', -1, float('nan'), float('inf')):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                paced_wait_seconds(invalid)
        self.assertEqual(paced_wait_seconds(0), 0)


if __name__ == '__main__':
    unittest.main()
