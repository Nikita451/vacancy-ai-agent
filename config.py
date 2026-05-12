import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Ключи
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Настройки моделей
    # Позволяет легко переключаться между mini и полной версией
    DEFAULT_MODEL = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")
    BASE_URL = "https://openrouter.ai"
    
    # Настройки поиска
    TAVILY_SEARCH_DEPTH = "advanced"
    MAX_SEARCH_RESULTS = 10