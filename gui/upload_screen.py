"""
gui/upload_screen.py

Screen 1: add resume files, enter job title + description, run screening.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox

from gui import styles


class UploadScreen(tk.Frame):
    def __init__(self, master, on_run):
        super().__init__(master, bg=styles.BG)
        self.on_run = on_run
        self.resume_paths: list[str] = []

        tk.Label(self, text="SMART RESUME SCREENER", **styles.TITLE_STYLE).pack(
            anchor="w", padx=24, pady=(24, 4)
        )
        tk.Label(
            self,
            text="Local, offline resume screening. No data leaves your machine.",
            **styles.LABEL_STYLE,
            fg="#444444",
        ).pack(anchor="w", padx=24, pady=(0, 20))

        # --- Resume upload section ---
        section1 = tk.Frame(self, bg=styles.BG)
        section1.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(section1, text="1. RESUMES (PDF / TXT)", **styles.LABEL_STYLE).pack(anchor="w")

        list_frame = tk.Frame(section1, bg=styles.BG, highlightbackground=styles.BLACK, highlightthickness=1)
        list_frame.pack(fill="x", pady=(6, 6))

        self.file_listbox = tk.Listbox(
            list_frame,
            bg=styles.WHITE,
            fg=styles.BLACK,
            font=styles.FONT_MONO,
            bd=0,
            highlightthickness=0,
            height=6,
            selectbackground=styles.BLACK,
            selectforeground=styles.WHITE,
        )
        self.file_listbox.pack(fill="x", padx=4, pady=4)

        btn_row = tk.Frame(section1, bg=styles.BG)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="+ ADD RESUMES", command=self._add_files, **styles.BUTTON_STYLE).pack(
            side="left"
        )
        tk.Button(
            btn_row, text="REMOVE SELECTED", command=self._remove_selected, **styles.SECONDARY_BUTTON_STYLE
        ).pack(side="left", padx=(10, 0))

        # --- Job description section ---
        section2 = tk.Frame(self, bg=styles.BG)
        section2.pack(fill="both", expand=True, padx=24, pady=(8, 8))

        tk.Label(section2, text="2. JOB TITLE", **styles.LABEL_STYLE).pack(anchor="w")
        self.job_title_entry = tk.Entry(section2, **styles.ENTRY_STYLE)
        self.job_title_entry.pack(fill="x", pady=(4, 12), ipady=4)

        tk.Label(section2, text="3. JOB DESCRIPTION (paste required skills + years of experience)", **styles.LABEL_STYLE).pack(
            anchor="w"
        )
        jd_frame = tk.Frame(section2, bg=styles.BG, highlightbackground=styles.BLACK, highlightthickness=1)
        jd_frame.pack(fill="both", expand=True, pady=(4, 0))
        self.jd_text = tk.Text(
            jd_frame, bg=styles.WHITE, fg=styles.BLACK, font=styles.FONT_MONO, bd=0, highlightthickness=0, wrap="word"
        )
        self.jd_text.pack(fill="both", expand=True, padx=4, pady=4)

        # --- Run button ---
        run_row = tk.Frame(self, bg=styles.BG)
        run_row.pack(fill="x", padx=24, pady=20)
        tk.Button(run_row, text="RUN SCREENING >", command=self._run, **styles.BUTTON_STYLE).pack(side="right")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select resumes",
            filetypes=[("Resumes", "*.pdf *.txt"), ("All files", "*.*")],
        )
        for p in paths:
            if p not in self.resume_paths:
                self.resume_paths.append(p)
                self.file_listbox.insert("end", p.split("/")[-1].split("\\")[-1])

    def _remove_selected(self):
        selection = list(self.file_listbox.curselection())
        for index in reversed(selection):
            self.file_listbox.delete(index)
            del self.resume_paths[index]

    def _run(self):
        if not self.resume_paths:
            messagebox.showwarning("No resumes", "Add at least one resume file first.")
            return
        job_title = self.job_title_entry.get().strip()
        jd_text = self.jd_text.get("1.0", "end").strip()
        if not job_title or not jd_text:
            messagebox.showwarning("Missing info", "Enter both a job title and a job description.")
            return

        self.on_run(self.resume_paths, job_title, jd_text)
