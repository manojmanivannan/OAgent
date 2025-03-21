import os
from dotenv import load_dotenv

class ConfigManager:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_env()
        return cls._instance

    def _load_env(self):
        """Load environment variables from .env file and system."""
        load_dotenv()  # Load variables from a .env file (if available)
        self.env_vars = {key: value for key, value in os.environ.items()}

    def get(self, key, default=None):
        """Retrieve an environment variable, with an optional default."""
        return self.env_vars.get(key, default)

# Usage
config = ConfigManager()


