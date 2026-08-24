# Smart Resume Screener

A fully offline, self-contained Python desktop app that parses resumes,
matches them against a job description, and produces a ranked, explainable
shortlist — no cloud API calls, no internet needed after first launch.

## Architecture

```
Tkinter GUI (black/white, monospace, flat)
        |
        v
Resume Parser (pdfplumber)  ->  raw text
        |
        v
Local LLM: extraction only  ->  structured JSON
   { name, skills[], years_of_experience, education_level, past_job_titles[] }
        |
        v
Deterministic Scoring Formula (pure Python, no LLM)
   final_score = skill_match*0.50 + experience_fit*0.25
                + education_fit*0.15 + title_relevance*0.10  (x10)
        |
        v
Local LLM: justification only  ->  1-2 sentence explanation of the score
        |
        v
SQLite storage + Tkinter results screen (ranked, expandable rows)
```

**Design principle:** the LLM never invents the score. It only (1) extracts
structured facts from unstructured resume text, and (2) explains a score
that was already computed by deterministic Python code. This keeps scoring
consistent across candidates and fully auditable.

## Local Model

- Model: `SmolLM2-360M-Instruct` (GGUF, Q4_K_M quantization, ~230-250MB)
- Runs via `llama-cpp-python`, CPU-only, no external server (no Ollama)
- Downloaded automatically on first launch into `~/.smart_resume_screener/models/`
- All later launches load the model directly from disk — fully offline

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

First run will show a download progress dialog for the local model.
After that, just `python main.py` to launch.

## Building a Standalone Executable

```bash
pyinstaller build.spec
```

Produces `dist/SmartResumeScreener` (or `.exe` on Windows). The model itself
is not bundled into the installer — it downloads on first run, keeping the
installer small (~30-50MB instead of ~300MB).

## Prompts

Both LLM prompts are stored as plain text templates in `/prompts/` rather
than hardcoded in Python, so they're easy to review and tune:

- `prompts/extraction_prompt.txt` — turns raw resume text into strict JSON
- `prompts/justification_prompt.txt` — turns a score breakdown into a
  short, evidence-based explanation

## Scoring Formula

| Component         | Weight | How it's computed                                              |
|--------------------|--------|------------------------------------------------------------------|
| Skill match        | 50%    | matched required skills / total required skills (fuzzy matching) |
| Experience fit     | 25%    | candidate years / required years, capped at 1.0                  |
| Education fit      | 15%    | lookup table (PhD=1.0, Masters=0.85, Bachelors=0.7, ...)          |
| Title relevance    | 10%    | token overlap + string similarity vs. job title                  |

Job requirements (required skills, required years) are parsed from the
pasted job description using lightweight heuristics in `gui/app_shell.py`
(`_guess_required_skills`, `_guess_required_years`) — for best results,
paste a JD with a bulleted skills list and an explicit "X years" phrase.

## Known Limitations

- PDF text extraction fails on scanned/image-only resumes (no OCR yet).
- Required-skills detection from the job description is heuristic, not
  LLM-driven — it looks for bullet points or capitalized tokens. A messy
  or unstructured JD may under-extract requirements.
- SmolLM2-360M is small and fast, but occasionally needs the built-in
  retry to produce valid JSON on unusually formatted resumes.
- Single-machine, single-user local SQLite storage — not built for
  multi-user or networked use.

## Project Structure

```
smart_resume_screener/
├── main.py                       # Entry point
├── gui/                           # Tkinter screens + shared styles
├── core/                          # Parsing, LLM engine, scoring, DB
├── prompts/                       # LLM prompt templates
├── requirements.txt
├── build.spec                     # PyInstaller config
└── README.md
```
