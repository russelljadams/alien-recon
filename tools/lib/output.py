"""Ghost Girl — structured output helpers.

All tools use these functions so Ghost Girl can grep for [DATA] lines
to extract machine-readable results alongside human-readable output.
"""

import sys

# ANSI colors
_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def _c(color, text):
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def banner(tool_name):
    """Print tool banner."""
    print(f"\n{_c('magenta', '  ╔' + '═' * 40 + '╗')}")
    print(f"{_c('magenta', '  ║')} {_c('bold', tool_name):^48s} {_c('magenta', '║')}")
    print(f"{_c('magenta', '  ╚' + '═' * 40 + '╝')}\n")


def status(msg):
    """Informational status message."""
    print(f"{_c('blue', '[*]')} {msg}")


def success(msg):
    """Success message."""
    print(f"{_c('green', '[+]')} {msg}")


def error(msg):
    """Error message."""
    print(f"{_c('red', '[-]')} {msg}", file=sys.stderr)


def warning(msg):
    """Warning message."""
    print(f"{_c('yellow', '[!]')} {msg}")


def data(key, value):
    """Machine-parseable data line. Ghost Girl greps for [DATA] key=value."""
    print(f"[DATA] {key}={value}")


def section(title):
    """Section header."""
    print(f"\n{_c('cyan', '─── ' + title + ' ' + '─' * max(1, 50 - len(title)))}")


def table(headers, rows):
    """Print a simple aligned table."""
    if not rows:
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(f"  {_c('bold', fmt.format(*headers))}")
    print(f"  {'  '.join('─' * w for w in col_widths)}")
    for row in rows:
        print(f"  {fmt.format(*[str(c) for c in row])}")
