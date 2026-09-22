import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured")