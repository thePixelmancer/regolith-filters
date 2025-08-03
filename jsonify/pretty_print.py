import textwrap


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


LINE_WIDTH = 120


def print_section(title="", symbol="-", color=Colors.WHITE, width=LINE_WIDTH):
    """Print a horizontal line with an optional centered title."""
    if title:
        title_str = f" {title} "
        side_len = (width - len(title_str)) // 2
        line = (
            symbol * side_len + title_str + symbol * (width - side_len - len(title_str))
        )
    else:
        line = symbol * width
    print(Colors.BOLD + color + line + Colors.RESET)


def print_success(text):
    print_section(f"[Success]", color=Colors.GREEN)
    wrapped_lines = textwrap.wrap(text, width=LINE_WIDTH)
    for line in wrapped_lines:
        print(Colors.GREEN + line + Colors.RESET)
    print_section(color=Colors.GREEN)


def print_error(text):
    print_section(f"[Error]", color=Colors.RED)
    wrapped_lines = textwrap.wrap(text, width=LINE_WIDTH)
    for line in wrapped_lines:
        print(Colors.RED + line + Colors.RESET)
    print_section(color=Colors.RED)


def print_warning(text):
    print_section(f"[Warning]", color=Colors.YELLOW)
    wrapped_lines = textwrap.wrap(text, width=LINE_WIDTH)
    for line in wrapped_lines:
        print(Colors.YELLOW + line + Colors.RESET)
    print_section(color=Colors.YELLOW)


def print_info(text):
    print_section(f"[Info]", color=Colors.BLUE)
    wrapped_lines = textwrap.wrap(text, width=LINE_WIDTH)
    for line in wrapped_lines:
        print(Colors.BLUE + line + Colors.RESET)
    print_section(color=Colors.BLUE)
