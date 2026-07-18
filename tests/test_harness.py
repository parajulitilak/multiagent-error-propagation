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

    def test_expression_answers_take_the_result(self):
        # models (esp. the verifier) answer as "a + b = c"; take c, not a
        self.assertEqual(normalize("91 + 182 = 273"), "273")
        self.assertEqual(normalize("$50/day * 7 days/week = $350/week"), "350")
        self.assertEqual(normalize("600 - (198 + 209) = 600 - 407 = 193."), "193")
        self.assertTrue(is_correct("19 + 13 = 32", "32"))
        self.assertFalse(is_correct("19 + 13 = 32", "19"))

    def test_bare_number_answers_unchanged(self):
        # no '=' path stays first-number behavior
        self.assertEqual(normalize("273"), "273")
        self.assertEqual(normalize("the answer is 12 dollars"), "12")


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


class TestSeverity(unittest.TestCase):
    def test_mild_stays_under_15_percent(self):
        for seed in range(30):
            _, meta = number_swap("there are 100 apples and 40 pears",
                                  random.Random(seed), "mild")
            self.assertTrue(meta["applied"])
            self.assertEqual(meta["severity"], "mild")
            self.assertLess(meta["relative_change"], 0.15)

    def test_moderate_within_30_to_60_percent(self):
        for seed in range(30):
            _, meta = number_swap("there are 100 apples and 40 pears",
                                  random.Random(seed), "moderate")
            self.assertEqual(meta["severity"], "moderate")
            self.assertGreaterEqual(meta["relative_change"], 0.30)
            self.assertLessEqual(meta["relative_change"], 0.60)

    def test_severe_above_200_percent_or_sign_flip(self):
        for seed in range(30):
            _, meta = number_swap("there are 10 boxes", random.Random(seed), "severe")
            self.assertEqual(meta["severity"], "severe")
            self.assertTrue(meta["sign_flip"] or meta["relative_change"] > 2.0)

    def test_small_integer_escalates_from_mild(self):
        # 3 cannot change by under 15%, so mild must escalate and say so.
        _, meta = number_swap("use 3 eggs", random.Random(0), "mild")
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["severity_target"], "mild")
        self.assertNotEqual(meta["severity"], "mild")
        self.assertNotEqual(meta["old"], meta["new"])

    def test_zero_still_gets_changed(self):
        _, meta = number_swap("the score is 0 now", random.Random(0), "mild")
        self.assertTrue(meta["applied"])
        self.assertNotEqual(meta["new"], "0")
        self.assertEqual(meta["severity"], "severe")

    def test_targets_cycle_balanced(self):
        injector = make_injector(["number_swap"], seed=7)
        targets = []
        for _ in range(9):
            _, meta = injector("there are 120 marbles in 40 bags")
            self.assertTrue(meta["applied"])
            targets.append(meta["severity_target"])
        self.assertEqual(targets.count("mild"), 3)
        self.assertEqual(targets.count("moderate"), 3)
        self.assertEqual(targets.count("severe"), 3)

    def test_comma_grouping_preserved_under_severe(self):
        corrupted, meta = number_swap("She paid $1,234 for it.",
                                      random.Random(1), "severe")
        self.assertEqual(meta["severity"], "severe")
        self.assertNotIn("1,234", corrupted.replace(meta["new"], ""))
        if "," in corrupted and not meta["sign_flip"]:
            self.assertRegex(corrupted, r"\$\d{1,3}(?:,\d{3})+")

    def test_value_always_changes_across_levels(self):
        for level in ("mild", "moderate", "severe"):
            for seed in range(30):
                _, meta = number_swap("there are 10 boxes and 7 cats",
                                      random.Random(seed), level)
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
