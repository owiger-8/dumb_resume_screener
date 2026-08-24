"""
gui/app_shell.py

Main application window. Wires the upload screen -> screening pipeline
-> results screen together, and runs screening on a background thread
so the GUI never freezes.
"""

from __future__ import annotations
import re
import threading
import tkinter as tk
from tkinter import messagebox

from gui import styles
from gui.upload_screen import UploadScreen
from gui.results_screen import ResultsScreen
from core.pdf_parser import extract_text
from core.extraction import extract_resume_data
from core.scoring import compute_score
from core.justification import generate_justification
from core.llm_engine import LLMEngine
from core import db


def _guess_required_years(jd_text: str) -> float:
    """Best-effort extraction of a 'N years' requirement from the JD text."""
    match = re.search(r"(\d+)\s*\+?\s*years?", jd_text, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0


def _guess_required_skills(jd_text: str) -> list[str]:
    """
    Naive skill extraction from the JD: look for a comma/bullet separated
    list near common keywords. Falls back to notable capitalized tokens.
    """
    lines = jd_text.splitlines()
    skills: list[str] = []
    for line in lines:
        if re.search(r"(skills|requirements|must have|tech stack)", line, re.IGNORECASE):
            continue
        if re.match(r"^\s*[-*•]\s*", line):
            cleaned = re.sub(r"^\s*[-*•]\s*", "", line).strip()
            if cleaned:
                skills.append(cleaned)
    if not skills:
        # fallback: comma-separated tokens that look like skill names
        candidates = re.findall(r"\b[A-Z][a-zA-Z0-9+.#]{1,20}\b", jd_text)
        skills = list(dict.fromkeys(candidates))[:10]
    return skills


class AppShell(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=styles.BG)
        self.pack(fill="both", expand=True)

        self.upload_screen = UploadScreen(self, on_run=self._start_screening)
        self.results_screen = ResultsScreen(self, on_back=self._show_upload)

        self._show_upload()

    def _show_upload(self):
        self.results_screen.pack_forget()
        self.upload_screen.pack(fill="both", expand=True)

    def _show_results(self):
        self.upload_screen.pack_forget()
        self.results_screen.pack(fill="both", expand=True)

    def _start_screening(self, resume_paths: list[str], job_title: str, jd_text: str):
        progress_win = self._show_progress_dialog()
        thread = threading.Thread(
            target=self._run_screening_pipeline,
            args=(resume_paths, job_title, jd_text, progress_win),
            daemon=True,
        )
        thread.start()

    def _show_progress_dialog(self) -> tk.Toplevel:
        win = tk.Toplevel(self)
        win.title("Screening in progress")
        win.geometry("400x120")
        win.configure(bg=styles.BG)
        win.resizable(False, False)
        label = tk.Label(win, text="Screening resumes...", **styles.LABEL_STYLE)
        label.pack(pady=30)
        win.status_label = label  # type: ignore[attr-defined]
        win.grab_set()
        return win

    def _run_screening_pipeline(self, resume_paths, job_title, jd_text, progress_win):
        try:
            engine = LLMEngine.get_instance()
            required_years = _guess_required_years(jd_text)
            required_skills = _guess_required_skills(jd_text)

            results = []
            for i, path in enumerate(resume_paths):
                self._update_progress(progress_win, f"Parsing {i + 1}/{len(resume_paths)}...")
                raw_text = extract_text(path)

                self._update_progress(progress_win, f"Extracting data {i + 1}/{len(resume_paths)}...")
                extracted = extract_resume_data(raw_text, engine=engine)
                candidate_id = db.save_candidate(path.split("/")[-1].split("\\")[-1], raw_text, extracted)

                self._update_progress(progress_win, f"Scoring {i + 1}/{len(resume_paths)}...")
                breakdown = compute_score(extracted, required_skills, required_years, job_title)

                self._update_progress(progress_win, f"Writing justification {i + 1}/{len(resume_paths)}...")
                justification = generate_justification(extracted.get("name", ""), job_title, breakdown, engine=engine)

                db.save_screening(candidate_id, job_title, jd_text, breakdown.as_dict(), justification)

                results.append(
                    {
                        "file_name": path.split("/")[-1].split("\\")[-1],
                        "candidate": extracted,
                        "score": breakdown.as_dict(),
                        "justification": justification,
                    }
                )

            self.after(0, self._on_screening_complete, progress_win, job_title, results)
        except Exception as e:
            self.after(0, self._on_screening_error, progress_win, str(e))

    def _update_progress(self, progress_win: tk.Toplevel, text: str):
        self.after(0, lambda: progress_win.status_label.config(text=text))  # type: ignore[attr-defined]

    def _on_screening_complete(self, progress_win: tk.Toplevel, job_title: str, results: list[dict]):
        progress_win.grab_release()
        progress_win.destroy()
        self.results_screen.load_results(job_title, results)
        self._show_results()

    def _on_screening_error(self, progress_win: tk.Toplevel, error_msg: str):
        progress_win.grab_release()
        progress_win.destroy()
        messagebox.showerror("Screening failed", error_msg)
