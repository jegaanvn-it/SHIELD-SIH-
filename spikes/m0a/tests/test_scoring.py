import unittest

from spikes.m0a.scoring import (
    character_error_rate,
    label_matches,
    normalize_for_cer,
    script_range_check,
)


class ScoringTests(unittest.TestCase):
    def test_normalization_removes_punctuation_and_collapses_spaces(self):
        self.assertEqual(normalize_for_cer(' Hello,   WORLD! '), "hello world")

    def test_character_error_rate(self):
        self.assertEqual(character_error_rate("cat", "cat"), 0.0)
        self.assertAlmostEqual(character_error_rate("cat", "cut"), 1 / 3)
        self.assertEqual(character_error_rate("", ""), 0.0)
        self.assertEqual(character_error_rate("", "x"), 1.0)

    def test_tanglish_labels_accept_only_documented_aliases(self):
        self.assertTrue(label_matches("Tamil in Latin script", "ta-Latn"))
        self.assertTrue(label_matches("Tanglish", "ta-Latn"))
        self.assertFalse(label_matches("en", "ta-Latn"))

    def test_script_prefilter_for_all_modes(self):
        self.assertTrue(script_range_check("நான் Python கற்கிறேன்", "ta"))
        self.assertTrue(script_range_check("ഞാൻ Python പഠിക്കുന്നു", "ml"))
        self.assertTrue(script_range_check("मैं Python सीख रहा हूँ", "hi"))
        self.assertTrue(script_range_check("Python-la pesu", "ta-Latn"))
        self.assertTrue(script_range_check("Guten Tag", "de"))
        self.assertFalse(script_range_check("English only", "ta"))
        self.assertFalse(script_range_check("नमस्ते", "ta"))


if __name__ == "__main__":
    unittest.main()
