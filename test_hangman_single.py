"""
Unit tests for HangmanEngine.

Covers:
- Start in both difficulties with configured lives
- Masking and reveal of correct letters
- Lives deducted on wrong guesses and timeouts
- Invalid / repeat guesses do not change lives
- No state change after win; no negative lives after loss
"""

import unittest
import random
from hangman_single import HangmanEngine, MASK_CHAR

WORDS = ["PYTHON", "QUALITY", "DEBUG"]
PHRASES = ["UNIT TESTS", "CLEAN CODE"]


class TestHangmanSingle(unittest.TestCase):
    """Unit tests for the Hangman implementation."""

    def setUp(self):
        """Deterministic RNG for reproducible selections."""
        self.rng = random.Random(1234)

    def test_start_basic(self):
        """Basic mode starts with lives and clean answer."""
        eng = HangmanEngine(WORDS, PHRASES, lives=3, rng=self.rng)
        st = eng.start("basic")
        self.assertEqual(st.lives, 3)
        self.assertTrue(all(ch.isalpha() or ch == " " for ch in st.answer))

    def test_start_intermediate(self):
        """Intermediate mode returns a phrase (contains a space)."""
        eng = HangmanEngine(WORDS, PHRASES, lives=5, rng=self.rng)
        st = eng.start("intermediate")
        self.assertEqual(st.lives, 5)
        self.assertIn(" ", st.answer)

    def test_correct_flow_win(self):
        """Guessing all letters wins the game."""
        eng = HangmanEngine(["ABC"], ["X Y"], lives=6, rng=self.rng)
        eng.start("basic")
        eng.guess("A")
        eng.guess("B")
        st = eng.guess("C")
        self.assertTrue(st.is_won)
        self.assertFalse(st.is_lost)

    def test_wrong_guesses_lose(self):
        """Two wrong guesses with 2 lives causes loss."""
        eng = HangmanEngine(["A"], ["B C"], lives=2, rng=self.rng)
        eng.start("basic")
        eng.guess("Z")
        st = eng.guess("Y")
        self.assertTrue(st.is_lost)

    def test_repeat_no_penalty(self):
        """Repeating a guess does not deduct lives."""
        eng = HangmanEngine(["ABC"], ["X Y"], lives=3, rng=self.rng)
        eng.start("basic")
        eng.guess("Z")
        st = eng.guess("Z")
        self.assertEqual(st.lives, 2)

    def test_timeout_deducts_life(self):
        """Timeout call deducts one life."""
        eng = HangmanEngine(["ABC"], ["X Y"], lives=2, rng=self.rng)
        eng.start("basic")
        st = eng.timeout()
        self.assertEqual(st.lives, 1)

    def test_masking_and_reveal(self):
        """Masking uses underscores; correct guess reveals all positions."""
        eng = HangmanEngine(["ABA"], ["X Y"], lives=3, rng=self.rng)
        eng.start("basic")
        self.assertEqual(eng.state.masked.replace(" ", ""), MASK_CHAR * 3)
        eng.guess("A")
        self.assertIn("A", eng.state.masked)
        self.assertNotIn("B", eng.state.masked.replace(" ", ""))

    def test_invalid_guess_ignored(self):
        """Non-letters and multi-char inputs are ignored."""
        eng = HangmanEngine(["ABC"], ["X Y"], lives=3, rng=self.rng)
        eng.start("basic")
        before = eng.state.lives
        eng.guess("1")
        self.assertEqual(before, eng.state.lives)

    def test_no_state_change_after_win(self):
        """After win, further guesses do not alter state."""
        eng = HangmanEngine(["ABA"], ["X Y"], lives=3, rng=self.rng)
        eng.start("basic")
        eng.guess("A")
        eng.guess("B")
        self.assertTrue(eng.state.is_won)

        before_lives = eng.state.lives
        before_masked = eng.state.masked
        before_guessed = set(eng.state.guessed)

        eng.guess("Z")  # ignored post-win

        self.assertTrue(eng.state.is_won)
        self.assertEqual(eng.state.lives, before_lives)
        self.assertEqual(eng.state.masked, before_masked)
        self.assertEqual(set(eng.state.guessed), before_guessed)

    def test_no_negative_lives_after_loss(self):
        """Lives never go below zero after loss and extra timeouts."""
        eng = HangmanEngine(["A"], ["B C"], lives=1, rng=self.rng)
        eng.start("basic")
        eng.guess("Z")
        self.assertTrue(eng.state.is_lost)
        self.assertEqual(eng.state.lives, 0)
        eng.timeout()  # ignored post-loss
        self.assertEqual(eng.state.lives, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
