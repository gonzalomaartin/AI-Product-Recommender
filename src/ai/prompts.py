from pathlib import Path

# Define the base directory for prompts
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

def load_prompt(file_name: str) -> str:
    """Load a prompt from a local file (synchronous)."""
    prompt_path = PROMPTS_DIR / file_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")

def load_relative_price_prompt() -> str:
    """Load the relative price prompt."""
    return load_prompt("relative_price_prompt.txt")

def load_allergens_prompt() -> str:
    """Load the allergens prompt."""
    return load_prompt("allergens_prompt.txt")

def load_nutritional_info_prompt() -> str:
    """Load the nutritional info prompt."""
    return load_prompt("nutritional_info_prompt.txt")

def load_all_prompts() -> tuple[str, str, str]:
    """Load all prompts syncronously"""
    return (
        load_relative_price_prompt(),
        load_nutritional_info_prompt(),
        load_allergens_prompt(),
    )
    