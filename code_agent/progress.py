import sys
import time
import itertools
from typing import Optional

class Spinner:
    """A simple terminal spinner for showing progress."""
    unicode_spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    ascii_spinner = ["|", "/", "-", "\\"]

    def __init__(self, text: str):
        self.text = text
        self.start_time = time.time()
        self.last_update = 0
        self.visible = False
        self.is_tty = sys.stdout.isatty()
        self.tested = False
        self.spinner_chars = None

    def test_charset(self) -> None:
        """Test if unicode characters can be displayed, fallback to ASCII if not."""
        if self.tested:
            return
        self.tested = True
        try:
            print(self.unicode_spinner[0], end="", flush=True)
            print("\r", end="", flush=True)
            self.spinner_chars = itertools.cycle(self.unicode_spinner)
        except UnicodeEncodeError:
            self.spinner_chars = itertools.cycle(self.ascii_spinner)

    def step(self) -> None:
        """Update the spinner display."""
        if not self.is_tty:
            return

        current_time = time.time()
        if not self.visible and current_time - self.start_time >= 0.5:
            self.visible = True
            self._step()
        elif self.visible and current_time - self.last_update >= 0.1:
            self._step()
        self.last_update = current_time

    def _step(self) -> None:
        """Internal method to update the spinner display."""
        if not self.visible:
            return

        self.test_charset()
        print(f"\r{self.text} {next(self.spinner_chars)}\r{self.text} ", end="", flush=True)

    def end(self) -> None:
        """Clear the spinner from display."""
        if self.visible and self.is_tty:
            print("\r" + " " * (len(self.text) + 3))