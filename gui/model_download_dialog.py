"""
gui/model_download_dialog.py

Blocking modal shown on first launch while the ~250MB local model downloads.
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk

from gui import styles
from core.llm_engine import download_model


class ModelDownloadDialog(tk.Toplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.on_complete = on_complete
        self.title("Setting up Smart Resume Screener")
        self.geometry("480x220")
        self.configure(bg=styles.BG)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # block close during download

        tk.Label(
            self,
            text="DOWNLOADING LOCAL MODEL",
            **styles.TITLE_STYLE,
        ).pack(pady=(24, 4))

        tk.Label(
            self,
            text="First-time setup. This model runs entirely on your machine.\nNo internet needed after this.",
            **styles.LABEL_STYLE,
            justify="center",
        ).pack(pady=(0, 16))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "BW.Horizontal.TProgressbar",
            troughcolor=styles.WHITE,
            background=styles.BLACK,
            bordercolor=styles.BLACK,
            lightcolor=styles.BLACK,
            darkcolor=styles.BLACK,
        )

        self.progress = ttk.Progressbar(
            self,
            style="BW.Horizontal.TProgressbar",
            length=380,
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(pady=8)

        self.status_label = tk.Label(self, text="Starting download...", **styles.LABEL_STYLE)
        self.status_label.pack(pady=(4, 0))

        self.grab_set()
        threading.Thread(target=self._run_download, daemon=True).start()

    def _run_download(self):
        def callback(downloaded: int, total: int):
            if total > 0:
                pct = int((downloaded / total) * 100)
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                self.after(0, self._update_progress, pct, mb_down, mb_total)

        try:
            download_model(progress_callback=callback)
            self.after(0, self._finish)
        except Exception as e:
            self.after(0, self._fail, str(e))

    def _update_progress(self, pct: int, mb_down: float, mb_total: float):
        self.progress["value"] = pct
        self.status_label.config(text=f"{pct}%  ({mb_down:.1f} MB / {mb_total:.1f} MB)")

    def _finish(self):
        self.status_label.config(text="Done. Launching app...")
        self.after(400, self._close_and_continue)

    def _fail(self, error_msg: str):
        self.status_label.config(text=f"Download failed: {error_msg}")

    def _close_and_continue(self):
        self.grab_release()
        self.destroy()
        self.on_complete()
