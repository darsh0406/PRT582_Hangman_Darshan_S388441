import unittest
from hangman_single import HangmanEngine, MASK_CHAR

class TestHangmanEngine(unittest.TestCase):
    def test_guess_correct_and_win(self):
        eng = HangmanEngine(words=["ABC"], phrases=["X Y"], lives=3)
        eng.start("basic")

        # starts hidden: ___
        self.assertEqual(eng.state.masked.replace(" ", ""), MASK_CHAR * 3)

        # guess all correctly
        eng.guess("A"); eng.guess("B"); st = eng.guess("C")
        self.assertTrue(st.is_won)
        self.assertFalse(st.is_lost)

    def test_timeout_deducts_one_life(self):
        eng = HangmanEngine(words=["ABC"], phrases=["X Y"], lives=2)
        eng.start("basic")
        st = eng.timeout()
        self.assertEqual(st.lives, 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
