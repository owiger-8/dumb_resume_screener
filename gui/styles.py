"""
gui/styles.py

Single source of truth for the app's minimal black/white,
monospace, flat visual style. Every screen imports from here.
"""

BLACK = "#000000"
WHITE = "#FFFFFF"

BG = WHITE
FG = BLACK
BORDER = BLACK

FONT_FAMILY = "Consolas"  # falls back to Courier New on non-Windows via _resolve_font()
FONT_MONO = (FONT_FAMILY, 11)
FONT_MONO_BOLD = (FONT_FAMILY, 11, "bold")
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_SMALL = (FONT_FAMILY, 9)

WINDOW_SIZE = "900x650"

BUTTON_STYLE = {
    "bg": BLACK,
    "fg": WHITE,
    "activebackground": WHITE,
    "activeforeground": BLACK,
    "font": FONT_MONO_BOLD,
    "bd": 0,
    "relief": "flat",
    "highlightthickness": 1,
    "highlightbackground": BLACK,
    "padx": 14,
    "pady": 8,
    "cursor": "hand2",
}

SECONDARY_BUTTON_STYLE = {
    "bg": WHITE,
    "fg": BLACK,
    "activebackground": BLACK,
    "activeforeground": WHITE,
    "font": FONT_MONO,
    "bd": 1,
    "relief": "solid",
    "highlightthickness": 0,
    "padx": 12,
    "pady": 6,
    "cursor": "hand2",
}

LABEL_STYLE = {
    "bg": BG,
    "fg": FG,
    "font": FONT_MONO,
}

TITLE_STYLE = {
    "bg": BG,
    "fg": FG,
    "font": FONT_TITLE,
}

FRAME_STYLE = {
    "bg": BG,
    "highlightbackground": BORDER,
    "highlightthickness": 0,
}

ENTRY_STYLE = {
    "bg": WHITE,
    "fg": BLACK,
    "insertbackground": BLACK,
    "font": FONT_MONO,
    "bd": 1,
    "relief": "solid",
    "highlightthickness": 0,
}


def resolve_font() -> str:
    """Pick a monospace font available on the current platform."""
    import tkinter.font as tkfont

    candidates = ["Consolas", "Courier New", "Courier", "Menlo", "DejaVu Sans Mono"]
    available = set(tkfont.families())
    for name in candidates:
        if name in available:
            return name
    return "TkFixedFont"
