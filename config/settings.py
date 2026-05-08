import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class Settings:
    # Fetch variables, providing safe defaults where applicable
    BOT_TOKEN: str = os.getenv("RUBIKA_BOT_TOKEN")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Constants for API configuration
    API_BASE_URL: str = "https://botapi.rubika.ir/v3"

    @classmethod
    def validate(cls):
        """Fails fast on application startup if critical secrets are missing."""
        if not cls.BOT_TOKEN:
            raise ValueError("CRITICAL FAILURE: RUBIKA_BOT_TOKEN is missing from .env file!")

# Instantiate a global settings object
settings = Settings()