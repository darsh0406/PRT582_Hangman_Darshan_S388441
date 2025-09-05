"""
PRT582 - Hangman Game using TDD (Assignment 2)
Student: Darshan Veerabhadrappa Meti
ID     : S388441

Notes:
- Single file with Tkinter GUI and CLI fallback.
- 15-second timer per guess (GUI shows countdown; CLI deducts a life).
- Two difficulties: basic (word) and intermediate (phrase).
- Only Python stdlib; no external dependencies.
"""

from __future__ import annotations

import queue
import random
import string
import threading
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional, Set


# ---------------- Engine (UI-agnostic) ----------------

MASK_CHAR = "_"


def _normalize_answer(text: str) -> str:
    """Uppercase and keep only A-Z and spaces (phrases readable)."""
    text = (text or "").upper()
    return "".join(
        ch for ch in text if ch in string.ascii_uppercase + " "
    ).strip()


@dataclass
class HangmanState:
    """Snapshot of state for any UI."""
    answer: str
    lives: int
    guessed: Set[str] = field(default_factory=set)

    @property
    def masked(self) -> str:
        """Underscore hidden letters; keep spaces."""
        return " ".join(
            ch if (ch == " " or ch in self.guessed) else MASK_CHAR
            for ch in self.answer
        )

    @property
    def is_won(self) -> bool:
        """True when all letters are guessed."""
        return all(ch == " " or ch in self.guessed for ch in self.answer)

    @property
    def is_lost(self) -> bool:
        """True when lives are 0 and not already won."""
        return self.lives <= 0 and not self.is_won


class HangmanEngine:
    """Main rules of Hangman with a small, testable API."""

    def __init__(
        self,
        words: Iterable[str],
        phrases: Iterable[str],
        lives: int = 6,
        rng: Optional[random.Random] = None,
    ):
        """Create an engine; deterministic RNG helps unit tests."""
        self._rng = rng or random.Random()
        self._words = [w.strip() for w in words if w and w.strip()]
        self._phrases = [p.strip() for p in phrases if p and p.strip()]
        if not self._words:
            raise ValueError("words must not be empty")
        if not self._phrases:
            raise ValueError("phrases must not be empty")
        self._default_lives = lives
        self._state: Optional[HangmanState] = None

    def start(self, difficulty: str = "basic") -> HangmanState:
        """Start a game for 'basic' (word) or 'intermediate' (phrase)."""
        if difficulty not in {"basic", "intermediate"}:
            raise ValueError(
                "difficulty must be 'basic' or 'intermediate'"
            )
        pool = self._words if difficulty == "basic" else self._phrases
        raw = self._rng.choice(pool)
        self._state = HangmanState(
            answer=_normalize_answer(raw),
            lives=self._default_lives,
            guessed=set(),
        )
        return self.state

    @property
    def state(self) -> HangmanState:
        """Current state snapshot (raises if not started)."""
        if self._state is None:
            raise RuntimeError("game not started")
        return self._state

    def guess(self, letter: str) -> HangmanState:
        """Apply a single-letter guess. Invalid/repeat guesses ignored."""
        if self._state is None:
            raise RuntimeError("game not started")
        if self._state.is_won or self._state.is_lost:
            return self._state

        letter = (letter or "").strip().upper()
        if len(letter) != 1 or letter not in string.ascii_uppercase:
            return self._state
        if letter in self._state.guessed:
            return self._state

        guessed = set(self._state.guessed)
        guessed.add(letter)
        new_lives = self._state.lives - (
            0 if letter in self._state.answer else 1
        )
        self._state = HangmanState(
            answer=self._state.answer,
            lives=new_lives,
            guessed=guessed,
        )
        return self._state

    def timeout(self) -> HangmanState:
        """Deduct one life when the UI reports a 15s timeout."""
        if self._state is None:
            raise RuntimeError("game not started")
        if self._state.is_won or self._state.is_lost:
            return self._state

        new_lives = max(self._state.lives - 1, 0)
        self._state = HangmanState(
            answer=self._state.answer,
            lives=new_lives,
            guessed=set(self._state.guessed),
        )
        return self._state


# ---------------- Word/Phrase data ----------------

WORDS = [
    "PYTHON",
    "VARIABLE",
    "FUNCTION",
    "ALGORITHM",
    "DEBUG",
    "COMPILE",
    "PACKAGE",
    "LIBRARY",
    "INTEGER",
    "BOOLEAN",
    "EXCEPTION",
    "ITERABLE",
    "DECORATOR",
    "GENERATOR",
    "ASYNC",
    "MODULE",
    "PYTEST",
    "LINTER",
    "SOFTWARE",
    "HARDWARE",
    "NETWORK",
    "SECURITY",
    "DATABASE",
    "MIGRATION",
    "TESTING",
    "QUALITY",
    "VERSION",
    "CONTROL",
    "BRANCH",
    "MERGE",
    "RELEASE",
    "SPRINT",
    "BACKLOG",
    "DOCUMENT",
    "REQUIREMENT",
    "DESIGN",
    "PATTERN",
    "FACTORY",
    "ADAPTER",
    "STRATEGY",
    "OBSERVER",
    "BUILDER",
    "FACADE",
    "SINGLETON",
    "INHERITANCE",
    "ENCAPSULATION",
    "POLYMORPHISM",
    "COMPOSITION",
    "ABSTRACTION",
]

PHRASES = [
    "UNIT TESTS",
    "SOFTWARE QUALITY",
    "HANGMAN GAME",
    "DATA MIGRATION",
    "CODE REVIEW",
    "CONTINUOUS INTEGRATION",
    "VERSION CONTROL",
    "CLEAN CODE",
    "TEST DRIVEN DEVELOPMENT",
    "GRAPHICAL USER INTERFACE",
    "PROJECT MANAGEMENT",
    "BUG TRIAGE",
    "ERROR HANDLING",
    "STATIC ANALYSIS",
    "TEAM COLLABORATION",
    "STATE MACHINE",
    "EVENT LOOP",
    "PUBLIC INTERFACE",
    "SEPARATION OF CONCERNS",
]


# ---------------- Tkinter GUI (with 15s timer) ----------------

def run_gui() -> None:
    """Run the Tkinter GUI with a 15s countdown."""
    # pylint: disable=import-outside-toplevel
    # pylint: disable=too-many-locals, too-many-statements
    try:
        import tkinter as tk  # type: ignore
        from tkinter import messagebox  # type: ignore
    except ImportError as exc:
        print("GUI unavailable (ImportError):", exc)
        raise

    engine = HangmanEngine(WORDS, PHRASES, lives=6)

    root = tk.Tk()
    root.title("Hangman TDD S388441 (PRT582)")
    root.geometry("720x420")
    root.resizable(False, False)

    timer_var = tk.StringVar(value="Time left: 15s")
    lives_var = tk.StringVar(value="Lives: 6")
    mask_var = tk.StringVar(value="")
    guessed_var = tk.StringVar(value="Guessed: ")
    answer_var = tk.StringVar(value="")
    difficulty = tk.StringVar(value="basic")

    timer_seconds = {"value": 15}
    timer_thread = {"value": None}  # type: ignore
    timer_stop = {"event": None}    # type: ignore

    def _entry_validator(text_after: str) -> bool:
        """Allow only 0-1 chars and only letters."""
        if len(text_after) > 1:
            return False
        if text_after == "":
            return True
        return text_after.isalpha()

    vcmd = (root.register(_entry_validator), "%P")

    def start_game() -> None:
        """Start or restart the game based on selected difficulty."""
        engine.start(difficulty.get())
        update_view()
        restart_timer()

    def update_view() -> None:
        """Refresh labels and handle win/lose dialogs."""
        st = engine.state
        mask_var.set(st.masked)
        lives_var.set(f"Lives: {st.lives}")
        guessed_sorted = " ".join(sorted(st.guessed)) if st.guessed else ""
        guessed_var.set(f"Guessed: {guessed_sorted}")
        if st.is_won:
            answer_var.set("Correct! You guessed it.")
            stop_timer()
            messagebox.showinfo(
                "You won!",
                "Great job! Start a new game?",
            )
        elif st.is_lost:
            answer_var.set(f"Out of lives. Answer: {st.answer}")
            stop_timer()
            messagebox.showinfo(
                "Game over",
                f"You ran out of lives.\nAnswer: {st.answer}",
            )
        else:
            answer_var.set("")

    def submit_guess(_event=None) -> None:
        """Enforce 1 char, send guess, update view and timer."""
        ch = (entry.get().strip()[:1]).upper()
        entry.delete(0, tk.END)
        engine.guess(ch)
        update_view()
        if not engine.state.is_won and not engine.state.is_lost:
            restart_timer()

    def stop_timer() -> None:
        """Signal the current timer thread to stop and join it."""
        ev = timer_stop["event"]
        thr = timer_thread["value"]
        if ev is not None:
            ev.set()
        if (
            thr is not None
            and thr.is_alive()
            and thr is not threading.current_thread()
        ):
            try:
                thr.join(timeout=1.0)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        timer_thread["value"] = None
        timer_stop["event"] = None

    def restart_timer() -> None:
        """Safely stop any old timer and start a fresh 15s timer."""
        stop_timer()
        timer_seconds["value"] = 15
        timer_var.set(f"Time left: {timer_seconds['value']}s")
        ev = threading.Event()
        timer_stop["event"] = ev
        t_thr = threading.Thread(
            target=timer_loop,
            args=(ev,),
            daemon=True,
        )
        timer_thread["value"] = t_thr
        t_thr.start()

    def timer_loop(stop_event: threading.Event) -> None:
        """Decrement timer each sec; trigger timeout at zero."""
        next_tick = time.monotonic() + 1.0
        while (not stop_event.is_set()) and timer_seconds["value"] > 0:
            now = time.monotonic()
            sleep_for = max(0.0, next_tick - now)
            if sleep_for > 0:
                time.sleep(sleep_for)
            next_tick += 1.0
            if stop_event.is_set():
                return
            timer_seconds["value"] -= 1
            timer_var.set(f"Time left: {timer_seconds['value']}s")
        if (not stop_event.is_set()) and timer_seconds["value"] <= 0:
            engine.timeout()
            update_view()
            if not engine.state.is_won and not engine.state.is_lost:
                restart_timer()

    # GUI layout

    top = tk.Frame(root, padx=16, pady=10)
    top.pack(fill=tk.X)

    tk.Label(top, text="Difficulty:").pack(side=tk.LEFT)

    tk.Radiobutton(
        top,
        text="Basic (Word)",
        value="basic",
        variable=difficulty,
    ).pack(side=tk.LEFT, padx=6)

    tk.Radiobutton(
        top,
        text="Intermediate (Phrase)",
        value="intermediate",
        variable=difficulty,
    ).pack(side=tk.LEFT, padx=6)

    tk.Button(
        top,
        text="New Game",
        command=start_game,
    ).pack(side=tk.RIGHT)

    status = tk.Frame(root, padx=16)
    status.pack(fill=tk.X, pady=(0, 8))

    tk.Label(
        status,
        textvariable=lives_var,
        font=("Arial", 12, "bold"),
    ).pack(side=tk.LEFT, padx=(0, 12))

    tk.Label(
        status,
        textvariable=timer_var,
        font=("Arial", 12, "bold"),
    ).pack(side=tk.LEFT)

    tk.Label(
        root,
        textvariable=mask_var,
        font=("Consolas", 24),
        pady=10,
    ).pack()

    panel = tk.Frame(root, pady=10)
    panel.pack()

    entry = tk.Entry(
        panel,
        width=2,
        font=("Arial", 16),
        justify="center",
        validate="key",
        validatecommand=vcmd,
    )
    entry.pack(side=tk.LEFT)
    entry.bind("<Return>", submit_guess)

    tk.Button(
        panel,
        text="Guess",
        command=submit_guess,
    ).pack(side=tk.LEFT, padx=6)

    tk.Button(
        panel,
        text="Quit",
        command=root.destroy,
    ).pack(side=tk.LEFT, padx=6)

    tk.Label(
        root,
        textvariable=guessed_var,
        font=("Arial", 12),
    ).pack()

    tk.Label(
        root,
        textvariable=answer_var,
        font=("Arial", 11, "italic"),
        fg="gray",
    ).pack(pady=(10, 0))

    start_game()
    root.mainloop()


# ---------------- CLI fallback (with real 15s timeout) ----------------

def timed_input(prompt: str, timeout: int) -> Optional[str]:
    """Blocking input with a deadline; None on timeout."""
    print(prompt, end="", flush=True)
    q: "queue.Queue[str]" = queue.Queue()

    def _reader() -> None:
        try:
            line = input()
        except Exception:  # pylint: disable=broad-exception-caught
            line = ""
        q.put(line)

    t_thr = threading.Thread(target=_reader, daemon=True)
    t_thr.start()

    remaining = timeout
    while remaining > 0 and t_thr.is_alive():
        print(f"\rTime left: {remaining:2d}s   ", end="", flush=True)
        time.sleep(1)
        remaining -= 1

    if t_thr.is_alive():
        print("\nTime's up!")
        return None
    return q.get().strip()


def run_cli() -> None:
    """Run the CLI version with a 15s countdown per guess."""
    print("Hangman Game (PRT582) [CLI]")
    engine = HangmanEngine(WORDS, PHRASES, lives=6)

    prompt = "Choose difficulty [basic/intermediate]: "
    diff_raw = input(prompt).strip().lower() or "basic"
    if diff_raw not in {"basic", "intermediate"}:
        diff_raw = "basic"

    engine.start(diff_raw)

    while True:
        st = engine.state
        guessed_str = " ".join(sorted(st.guessed))
        print(f"\n{st.masked}")
        print(f"Lives: {st.lives}  Guessed: {guessed_str}")

        if st.is_won:
            print("Correct! You guessed it right.")
            break
        if st.is_lost:
            print(f"Out of lives. Answer: {st.answer}")
            break

        guess_raw = timed_input("Enter a letter: ", 15)
        if guess_raw is None:
            engine.timeout()
            continue

        guess_raw = guess_raw.strip()
        if not guess_raw or not guess_raw[0].isalpha():
            print("Please enter a single A-Z letter.")
            continue

        engine.guess(guess_raw[0])


if __name__ == "__main__":
    # Try GUI first; fall back to CLI
    try:
        run_gui()
    except (ImportError, RuntimeError, OSError) as exc:
        print("GUI not available. Falling back to CLI.\nReason:", exc)
        run_cli()
