"""Prompt loading helper — loads LLM prompt templates from the prompts/ directory."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def get_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
