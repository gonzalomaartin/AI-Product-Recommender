import os 
from dotenv import load_dotenv

load_dotenv() 

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

RELATIVE_PRICE_PROVIDER = "groq"
ALLERGENS_PROVIDER = "groq"
NUTRITIONAL_INFO_PROVIDER = "groq"

RELATIVE_PRICE_MODEL = "llama-3.3-70b-versatile"
ALLERGENS_MODEL = "moonshotai/kimi-k2-instruct-0905"
NUTRITIONAL_INFO_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


