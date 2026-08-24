"""
core/llm_engine.py

Handles downloading the small local GGUF model and running inference
through llama-cpp-python. No external server (no Ollama) required.
"""

from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional

MODEL_DIR = Path.home() / ".smart_resume_screener" / "models"
MODEL_REPO = "HuggingFaceTB/SmolLM2-360M-Instruct-GGUF"
MODEL_FILENAME = "smollm2-360m-instruct-q4_k_m.gguf"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

ProgressCallback = Callable[[int, int], None]  # (downloaded_bytes, total_bytes)


def is_model_downloaded() -> bool:
    return MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 1_000_000


def download_model(progress_callback: Optional[ProgressCallback] = None) -> Path:
    """
    Downloads the quantized GGUF model from Hugging Face Hub.
    Calls progress_callback(downloaded_bytes, total_bytes) periodically if given.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if is_model_downloaded():
        if progress_callback:
            size = MODEL_PATH.stat().st_size
            progress_callback(size, size)
        return MODEL_PATH

    # huggingface_hub handles resumable, chunked downloads well; we wrap it
    # with a manual requests-based fallback that reports fine-grained progress.
    import requests

    url = (
        f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILENAME}"
    )
    tmp_path = MODEL_PATH.with_suffix(".part")

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total)

    if not tmp_path.exists() or tmp_path.stat().st_size < 1_000_000:
        raise RuntimeError("Model download failed or file is incomplete.")

    tmp_path.rename(MODEL_PATH)
    return MODEL_PATH


class LLMEngine:
    """Thin wrapper around llama-cpp-python for the two narrow prompts we use."""

    _instance: "LLMEngine | None" = None

    def __init__(self, model_path: Path = MODEL_PATH):
        from llama_cpp import Llama

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run download_model() first."
            )

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=4,
            verbose=False,
        )

    @classmethod
    def get_instance(cls) -> "LLMEngine":
        if cls._instance is None:
            cls._instance = LLMEngine()
        return cls._instance

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response["choices"][0]["message"]["content"].strip()
