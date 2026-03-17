import os 
from dotenv import load_dotenv

load_dotenv() 

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

RELATIVE_PRICE_PROVIDER = "groq"
ALLERGENS_PROVIDER = "groq"
NUTRITIONAL_INFO_PROVIDER = "google_genai"

RELATIVE_PRICE_MODEL = "llama-3.3-70b-versatile"
ALLERGENS_MODEL = "moonshotai/kimi-k2-instruct-0905"
NUTRITIONAL_INFO_MODEL = "gemini-3.1-flash-lite-preview"


