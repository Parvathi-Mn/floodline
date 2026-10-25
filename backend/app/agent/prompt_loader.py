from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def build_system_prompt(version: str, emergency_numbers: str) -> str:
    """Load prompts/<version>.md and insert the client's emergency numbers."""
    template = (PROMPTS_DIR / f"{version}.md").read_text(encoding="utf-8")
    return template.replace("{{EMERGENCY_NUMBERS}}", emergency_numbers)