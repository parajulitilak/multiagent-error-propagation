import random
import unittest

from src.injection import make_injector, number_swap, operation_flip
from src.pipeline import extract_final_answer, extract_marked_answer
from src.runner import is_correct, normalize


class TestNormalize(unittest.TestCase):
    def test_integers_keep_trailing_zeros(self):
        self.assertEqual(normalize("100"), "100")
        self.assertEqual(normalize("1000"), "1000")
        self.assertEqual(normalize("70"), "70")
        self.assertEqual(normalize("0"), "0")

    def test_decimals_drop_trailing_zeros(self):
        self.assertEqual(normalize("1.50"), "1.5")
        self.assertEqual(normalize("2.0"), "2")

    def test_currency_and_commas(self):
        self.assertEqual(normalize("$1,234"), "1234")

    def test_round_numbers_do_not_collide(self):
        self.assertFalse(is_correct("1", "100"))
        self.assertFalse(is_correct("10", "1000"))
        self.assertFalse(is_correct("", "0"))
        self.assertTrue(is_correct("100", "100"))
        self.assertTrue(is_correct("$1,234", "1234"))


class TestExtraction(unittest.TestCase):
    def test_last_marker_wins(self):
        text = "FINAL ANSWER: 10\nno wait\nFINAL ANSWER: 12"
        self.assertEqual(extract_final_answer(text), "12")

    def test_two_markers_on_one_line(self):
        text = "the solver said 'FINAL ANSWER: 10' but that is wrong. FINAL ANSWER: 12"
        self.assertEqual(extract_final_answer(text), "12")

    def test_no_marker_returns_none(self):
        self.assertIsNone(extract_marked_answer("VERDICT: REJECT, step 3 is off."))

    def test_fallback_takes_last_number(self):
        self.assertEqual(extract_final_answer("costs 5 then 7"), "7")

    def test_marker_only_reads_its_own_line(self):
        text = "FINAL ANSWER: 12\nby step 3 of the plan"
        self.assertEqual(extract_final_answer(text), "12")


class TestNumberSwap(unittest.TestCase):
    def test_step_labels_excluded(self):
        text = "Step 1: take the 6 apples\nStep 2: add 4 more"
        for seed in range(30):
            _, meta = number_swap(text, random.Random(seed))
            self.assertTrue(meta["applied"])
            self.assertIn(meta["old"], ("6", "4"))

    def test_line_start_label_excluded(self):
        text = "2. mix them together\nuse 3 eggs"
        for seed in range(30):
            _, meta = number_swap(text, random.Random(seed))
            self.assertTrue(meta["applied"])
            self.assertEqual(meta["old"], "3")

    def test_sentence_final_quantity_is_eligible(self):
        _, meta = number_swap("The total is 6.", random.Random(0))
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["old"], "6")

    def test_comma_grouped_number_swapped_whole(self):
        corrupted, meta = number_swap("She paid $1,234 for it.", random.Random(0))
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["old"], "1234")
        self.assertNotIn("1,234", corrupted)

    def test_swap_always_changes_value(self):
        for seed in range(50):
            _, meta = number_swap("there are 10 boxes", random.Random(seed))
            self.assertNotEqual(meta["old"], meta["new"])


class TestOperationFlip(unittest.TestCase):
    def test_flips_to_opposite(self):
        corrupted, meta = operation_flip("add the totals", random.Random(0))
        self.assertTrue(meta["applied"])
        self.assertIn("subtract", corrupted)

    def test_no_candidates(self):
        _, meta = operation_flip("nothing to see here", random.Random(0))
        self.assertFalse(meta["applied"])


class TestInjector(unittest.TestCase):
    def test_falls_back_between_types(self):
        injector = make_injector(["number_swap", "operation_flip"], seed=7)
        # no numbers, so number_swap cannot apply; the flip still must
        _, meta = injector("add everything together", random.Random(1))
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["type"], "operation_flip")

    def test_none_applicable(self):
        injector = make_injector(["number_swap", "operation_flip"], seed=7)
        _, meta = injector("nothing here", random.Random(1))
        self.assertFalse(meta["applied"])


if __name__ == "__main__":
    unittest.main()
