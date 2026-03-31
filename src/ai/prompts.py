from pathlib import Path

# Define the base directory for prompts
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
HUMAN_MESSAGE_DIR = BASE_DIR / "HumanMessages"

def load_file(DIR, file_name: str) -> str:
    """Load a prompt from a local file (synchronous)."""
    prompt_path = DIR / file_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")

def load_relative_price_prompt() -> str:
    """Load the relative price prompt."""
    return load_file(PROMPTS_DIR, "relative_price_prompt.txt")

def load_allergens_prompt() -> str:
    """Load the allergens prompt."""
    return load_file(PROMPTS_DIR, "allergens_prompt.txt")

def load_reflection_allergens_prompt() -> str: 
    return load_file(PROMPTS_DIR, "allergens_audit_prompt.txt")

def load_nutritional_info_prompt() -> str:
    """Load the nutritional info prompt."""
    return load_file(PROMPTS_DIR, "nutritional_info_prompt.txt")

def load_all_prompts() -> tuple[str, str, str, str]:
    """Load all prompts syncronously"""
    return (
        load_relative_price_prompt(),
        load_nutritional_info_prompt(),
        load_allergens_prompt(), 
        load_reflection_allergens_prompt()
    )

def load_relative_price_human_message() -> str: 
    return load_file(HUMAN_MESSAGE_DIR, "RELATIVE_PRICE.txt")

def load_allergens_human_message() -> str: 
    return load_file(HUMAN_MESSAGE_DIR, "ALLERGENS.txt")

def load_reflection_allergens_human_message() -> str: 
    return load_file(HUMAN_MESSAGE_DIR, "REFLECTION_ALLERGENS.txt")

def load_nutritional_info_message() -> str: 
    return load_file(HUMAN_MESSAGE_DIR, "NUTRITIONAL_INFO.txt")

def load_all_human_messages() -> tuple[str, str]: 
    "Load all human messages syncronously"
    return ( 
        load_allergens_human_message(), 
        load_reflection_allergens_human_message(), 
    )
    