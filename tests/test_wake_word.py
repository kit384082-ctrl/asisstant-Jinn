from __future__ import annotations

import unittest

from config import Config
from core.wake_word import WakeWordDetector


class WakeWordTests(unittest.TestCase):
    def test_normalization_is_unicode_case_and_spacing_tolerant(self):
        self.assertEqual(WakeWordDetector._normalize("  ЭЙ   ДЖИНН  "), "эй джинн")
        self.assertEqual(WakeWordDetector._normalize("GÉNIE"), "génie")
        self.assertEqual(WakeWordDetector._normalize("ДЖИНН\u00a0"), "джинн")

    def test_matching_tolerates_punctuation_but_respects_word_boundaries(self):
        self.assertTrue(
            WakeWordDetector._contains_wake_phrase(
                "Okay, HEY... GENIE!", ("hey genie",)
            )
        )
        self.assertTrue(
            WakeWordDetector._contains_wake_phrase("Salut, génie !", ("salut génie",))
        )
        self.assertFalse(
            WakeWordDetector._contains_wake_phrase("un ingenioso plan", ("genio",))
        )

    def test_default_wake_phrases_are_normalizable_in_all_languages(self):
        expected = {
            "ru": "джинн",
            "en": "genie",
            "de": "dschinni",
            "es": "genio",
            "fr": "génie",
        }
        for language, phrase in expected.items():
            with self.subTest(language=language):
                normalized = {
                    WakeWordDetector._normalize(value)
                    for value in Config.wake_words(language)
                }
                self.assertIn(phrase, normalized)


if __name__ == "__main__":
    unittest.main()
