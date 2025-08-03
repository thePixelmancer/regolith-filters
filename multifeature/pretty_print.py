import textwrap
import io
import sys
from typing import Union, Dict, Any
from dataclasses import dataclass
from enum import Enum

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# -------------------------------------------------------------------------------------- #
# Color and Formatting Utilities
# -------------------------------------------------------------------------------------- #
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


class BorderStyle(Enum):
    """Enumeration of available border styles."""

    ROUNDED = "rounded"
    SQUARE = "square"
    DOUBLE = "double"
    THICK = "thick"
    DOUBLE_SINGLE = "double_single"
    SINGLE_DOUBLE = "single_double"
    ASCII = "ascii"
    STARS = "stars"
    DOTS = "dots"
    HASH = "hash"
    MINIMAL = "minimal"
    SHADOW = "shadow"
    DASHED = "dashed"
    BOLD_DASHED = "bold_dashed"


class TitleAnchor(Enum):
    """Enumeration of title anchor positions."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class BorderChars:
    """Container for border characters."""

    top_left: str
    top_right: str
    bottom_left: str
    bottom_right: str
    horizontal: str
    vertical: str


class Panel:
    """A flexible panel class for creating bordered text boxes with customizable styling."""

    # Border style definitions
    BORDER_STYLES: Dict[str, BorderChars] = {
        BorderStyle.ROUNDED.value: BorderChars("╭", "╮", "╰", "╯", "─", "│"),
        BorderStyle.SQUARE.value: BorderChars("┌", "┐", "└", "┘", "─", "│"),
        BorderStyle.DOUBLE.value: BorderChars("╔", "╗", "╚", "╝", "═", "║"),
        BorderStyle.THICK.value: BorderChars("┏", "┓", "┗", "┛", "━", "┃"),
        BorderStyle.DOUBLE_SINGLE.value: BorderChars("╓", "╖", "╙", "╜", "─", "║"),
        BorderStyle.SINGLE_DOUBLE.value: BorderChars("╒", "╕", "╘", "╛", "═", "│"),
        BorderStyle.ASCII.value: BorderChars("+", "+", "+", "+", "-", "|"),
        BorderStyle.STARS.value: BorderChars("*", "*", "*", "*", "*", "*"),
        BorderStyle.DOTS.value: BorderChars("·", "·", "·", "·", "·", "·"),
        BorderStyle.HASH.value: BorderChars("#", "#", "#", "#", "#", "#"),
        BorderStyle.MINIMAL.value: BorderChars(" ", " ", " ", " ", "─", "│"),
        BorderStyle.SHADOW.value: BorderChars("▄", "▄", "▀", "▀", "▄", "█"),
        BorderStyle.DASHED.value: BorderChars("┌", "┐", "└", "┘", "┄", "┊"),
        BorderStyle.BOLD_DASHED.value: BorderChars("┏", "┓", "┗", "┛", "┅", "┋"),
    }

    def __init__(
        self,
        body: str,
        title: Union[str, None] = None,
        width: int = 120,
        color: str = Colors.WHITE,
        border_style: Union[str, BorderStyle] = BorderStyle.ROUNDED,
        padding: int = 1,
        title_anchor: Union[str, TitleAnchor] = TitleAnchor.CENTER,
    ) -> None:
        """
        Initialize a Panel.

        Args:
            body: The main text content
            title: Title text to display in the top border
            width: Maximum width of the panel
            color: ANSI color code for the panel
            border_style: Border style enum or string
            padding: Internal padding (spaces on each side of text)
            title_anchor: Title position enum or string
        """
        self.body = body
        self.title = title
        self.width = width
        self.color = color
        self.padding = padding

        # Handle enum or string input
        if isinstance(border_style, BorderStyle):
            border_style = border_style.value
        if isinstance(title_anchor, TitleAnchor):
            title_anchor = title_anchor.value

        self.border_style = border_style.lower()
        self.title_anchor = title_anchor.lower()

        # Get border characters
        self.border_chars = self.BORDER_STYLES.get(
            self.border_style, self.BORDER_STYLES[BorderStyle.ROUNDED.value]
        )

    def _wrap_text(self) -> list[str]:
        """Wrap the body text to fit within the panel."""
        available_width = self.width - (2 * self.padding) - 2
        return textwrap.wrap(self.body, width=available_width)

    def _create_top_border(self) -> str:
        """Create the top border with optional title positioned according to anchor."""
        if not self.title:
            return (
                self.border_chars.top_left
                + self.border_chars.horizontal * (self.width - 2)
                + self.border_chars.top_right
            )

        title_text = f" {self.title} "
        remaining_width = self.width - len(title_text) - 2

        if self.title_anchor == TitleAnchor.LEFT.value:
            return (
                self.border_chars.top_left
                + title_text
                + self.border_chars.horizontal * remaining_width
                + self.border_chars.top_right
            )
        elif self.title_anchor == TitleAnchor.RIGHT.value:
            return (
                self.border_chars.top_left
                + self.border_chars.horizontal * remaining_width
                + title_text
                + self.border_chars.top_right
            )
        else:  # center (default)
            left_width = remaining_width // 2
            right_width = remaining_width - left_width
            return (
                self.border_chars.top_left
                + self.border_chars.horizontal * left_width
                + title_text
                + self.border_chars.horizontal * right_width
                + self.border_chars.top_right
            )

    def _create_bottom_border(self) -> str:
        """Create the bottom border."""
        return (
            self.border_chars.bottom_left
            + self.border_chars.horizontal * (self.width - 2)
            + self.border_chars.bottom_right
        )

    def _create_content_line(self, text: str) -> str:
        """Create a content line with proper padding and borders."""
        padding_spaces = " " * self.padding
        content_width = self.width - (2 * self.padding) - 2
        text_padding = content_width - len(text)

        return (
            self.border_chars.vertical
            + padding_spaces
            + text
            + " " * text_padding
            + padding_spaces
            + self.border_chars.vertical
        )

    def print(self):
        """Print the panel to the console."""
        wrapped_lines = self._wrap_text()

        # Print top border
        print(f"{self.color}{self._create_top_border()}{Colors.RESET}")

        # Print content lines
        for line in wrapped_lines:
            print(f"{self.color}{self._create_content_line(line)}{Colors.RESET}")

        # Print bottom border
        print(f"{self.color}{self._create_bottom_border()}{Colors.RESET}")

    def __str__(self):
        """Return the panel as a string."""
        wrapped_lines = self._wrap_text()
        lines = []

        lines.append(f"{self.color}{self._create_top_border()}{Colors.RESET}")
        for line in wrapped_lines:
            lines.append(f"{self.color}{self._create_content_line(line)}{Colors.RESET}")
        lines.append(f"{self.color}{self._create_bottom_border()}{Colors.RESET}")

        return "\n".join(lines)


def print_colored(text, color=Colors.WHITE, symbol=None, title_anchor="center"):
    """Print text with specified color, wrapping lines at 100 chars in a box."""
    panel = Panel(
        text,
        title=symbol,
        color=color,
        border_style="rounded",
        title_anchor=title_anchor,
    )
    panel.print()


def print_success(text, title_anchor="center"):
    """Print success message in green."""
    panel = Panel(
        text,
        title="✓ Success",
        color=Colors.GREEN,
        border_style="rounded",
        title_anchor=title_anchor,
    )
    panel.print()


def print_error(text, title_anchor="center"):
    """Print error message in red."""
    panel = Panel(
        text,
        title="✗ Error",
        color=Colors.RED,
        border_style="rounded",
        title_anchor=title_anchor,
    )
    panel.print()


def print_warning(text, title_anchor="center"):
    """Print warning message in yellow."""
    panel = Panel(
        text,
        title="⚠ Warning",
        color=Colors.YELLOW,
        border_style="rounded",
        title_anchor=title_anchor,
    )
    panel.print()


def print_info(text, title_anchor="center"):
    """Print info message in blue."""
    panel = Panel(
        text,
        title="ℹ Info",
        color=Colors.BLUE,
        border_style="rounded",
        title_anchor=title_anchor,
    )
    panel.print()
