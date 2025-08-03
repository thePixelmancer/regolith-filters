import textwrap

# -------------------------------------------------------------------------------------- #
# Color and Formatting Utilities
# -------------------------------------------------------------------------------------- #
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

LINE_WIDTH = 100

def print_colored(text, color=Colors.WHITE, symbol=None):
  """Print text with specified color, wrapping lines at 100 chars."""
  wrapped_lines = textwrap.wrap(text, width=LINE_WIDTH)
  
  # Create top line with symbol at the beginning if provided
  if symbol:
    symbol_text = f"[ {symbol} ]"
    remaining_width = LINE_WIDTH - len(symbol_text)
    top_line = symbol_text + "─" * remaining_width
  else:
    top_line = "─" * LINE_WIDTH
  
  print(f"{color}{top_line}{Colors.RESET}")
  for line in wrapped_lines:
    print(f"{color}{line}{Colors.RESET}")
  print(f"{color}{'─' * LINE_WIDTH}{Colors.RESET}")


def print_success(text):
    """Print success message in green."""
    print_colored(text, Colors.GREEN, "✓")


def print_error(text):
    """Print error message in red."""
    print_colored(text, Colors.RED, "✗")


def print_warning(text):
    """Print warning message in yellow."""
    print_colored(text, Colors.YELLOW, "⚠")


def print_info(text):
    """Print info message in blue."""
    print_colored(text, Colors.BLUE, "ℹ")
