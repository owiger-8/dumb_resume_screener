"""
main.py

Entry point for the Smart Resume Screener desktop app.
"""

import tkinter as tk

from gui import styles
from gui.model_download_dialog import ModelDownloadDialog
from gui.app_shell import AppShell
from core.llm_engine import is_model_downloaded
from core import db


def launch_main_app(root: tk.Tk):
    AppShell(root)


def main():
    db.init_db()

    root = tk.Tk()
    root.title("Smart Resume Screener")
    root.geometry(styles.WINDOW_SIZE)
    root.configure(bg=styles.BG)

    resolved_font = styles.resolve_font()
    if resolved_font != styles.FONT_FAMILY:
        styles.FONT_MONO = (resolved_font, 11)
        styles.FONT_MONO_BOLD = (resolved_font, 11, "bold")
        styles.FONT_TITLE = (resolved_font, 16, "bold")
        styles.FONT_SMALL = (resolved_font, 9)

    if is_model_downloaded():
        launch_main_app(root)
    else:
        # Hide the (empty) main window until the model is ready
        root.withdraw()

        def on_complete():
            root.deiconify()
            launch_main_app(root)

        ModelDownloadDialog(root, on_complete=on_complete)

    root.mainloop()


if __name__ == "__main__":
    main()
