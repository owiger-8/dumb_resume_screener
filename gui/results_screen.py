"""
gui/results_screen.py

Screen 2: ranked shortlist of candidates. Clicking a row expands
the score breakdown and LLM-written justification.
"""

from __future__ import annotations
import tkinter as tk

from gui import styles


class ResultsScreen(tk.Frame):
    def __init__(self, master, on_back):
        super().__init__(master, bg=styles.BG)
        self.on_back = on_back
        self.results: list[dict] = []
        self.row_frames: dict[int, tk.Frame] = {}
        self.expanded_index: int | None = None

        header = tk.Frame(self, bg=styles.BG)
        header.pack(fill="x", padx=24, pady=(24, 8))
        tk.Label(header, text="SHORTLIST", **styles.TITLE_STYLE).pack(side="left")
        tk.Button(
            header, text="< BACK", command=self._go_back, **styles.SECONDARY_BUTTON_STYLE
        ).pack(side="right")

        self.job_label = tk.Label(self, text="", **styles.LABEL_STYLE, fg="#444444")
        self.job_label.pack(anchor="w", padx=24, pady=(0, 12))

        # Scrollable list container
        canvas_frame = tk.Frame(self, bg=styles.BG)
        canvas_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.canvas = tk.Canvas(canvas_frame, bg=styles.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.list_container = tk.Frame(self.canvas, bg=styles.BG)

        self.list_container.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.list_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_results(self, job_title: str, results: list[dict]):
        """
        results: list of dicts, each with keys:
            file_name, candidate (dict), score (ScoreBreakdown.as_dict()), justification
        Sorted descending by score before display.
        """
        self.results = sorted(results, key=lambda r: r["score"]["final_score"], reverse=True)
        self.job_label.config(text=f"Job: {job_title}   |   {len(self.results)} candidate(s) screened")

        for widget in self.list_container.winfo_children():
            widget.destroy()
        self.row_frames.clear()
        self.expanded_index = None

        for i, result in enumerate(self.results):
            self._build_row(i, result)

    def _build_row(self, index: int, result: dict):
        candidate = result["candidate"]
        score = result["score"]

        row = tk.Frame(self.list_container, bg=styles.BG, highlightbackground=styles.BLACK, highlightthickness=1)
        row.pack(fill="x", pady=(0, 8))

        summary = tk.Frame(row, bg=styles.BG, cursor="hand2")
        summary.pack(fill="x", padx=10, pady=8)

        rank_label = tk.Label(
            summary, text=f"#{index + 1}", **styles.LABEL_STYLE, font=styles.FONT_MONO_BOLD
        )
        rank_label.pack(side="left")

        name = candidate.get("name") or result["file_name"]
        name_label = tk.Label(summary, text=f"   {name}", **styles.LABEL_STYLE)
        name_label.pack(side="left")

        score_label = tk.Label(
            summary, text=f"{score['final_score']} / 10", **styles.LABEL_STYLE, font=styles.FONT_MONO_BOLD
        )
        score_label.pack(side="right")

        detail = tk.Frame(row, bg=styles.BG)
        # not packed initially -- shown on click

        def toggle(event=None, idx=index, detail_frame=detail):
            self._toggle_row(idx, detail_frame)

        for widget in (summary, rank_label, name_label, score_label, row):
            widget.bind("<Button-1>", toggle)

        self.row_frames[index] = detail
        self._populate_detail(detail, result)

    def _populate_detail(self, detail_frame: tk.Frame, result: dict):
        score = result["score"]
        candidate = result["candidate"]

        sep = tk.Frame(detail_frame, bg=styles.BLACK, height=1)
        sep.pack(fill="x", padx=10)

        body = tk.Frame(detail_frame, bg=styles.BG)
        body.pack(fill="x", padx=14, pady=10)

        tk.Label(
            body, text=result["justification"], **styles.LABEL_STYLE, wraplength=780, justify="left"
        ).pack(anchor="w", pady=(0, 8))

        breakdown_text = (
            f"Skill match: {score['skill_match']}   "
            f"Experience fit: {score['experience_fit']}   "
            f"Education fit: {score['education_fit']}   "
            f"Title relevance: {score['title_relevance']}"
        )
        tk.Label(body, text=breakdown_text, **styles.LABEL_STYLE, font=styles.FONT_SMALL, fg="#444444").pack(
            anchor="w", pady=(0, 6)
        )

        if score.get("matched_skills"):
            tk.Label(
                body,
                text=f"Matched skills: {', '.join(score['matched_skills'])}",
                **styles.LABEL_STYLE,
                font=styles.FONT_SMALL,
            ).pack(anchor="w")
        if score.get("missing_skills"):
            tk.Label(
                body,
                text=f"Missing skills: {', '.join(score['missing_skills'])}",
                **styles.LABEL_STYLE,
                font=styles.FONT_SMALL,
                fg="#444444",
            ).pack(anchor="w")

    def _toggle_row(self, index: int, detail_frame: tk.Frame):
        if self.expanded_index == index:
            detail_frame.pack_forget()
            self.expanded_index = None
            return

        if self.expanded_index is not None and self.expanded_index in self.row_frames:
            self.row_frames[self.expanded_index].pack_forget()

        detail_frame.pack(fill="x")
        self.expanded_index = index

    def _go_back(self):
        self.on_back()
