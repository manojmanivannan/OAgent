import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings  # new import
from langchain_ollama import OllamaEmbeddings      # new import
from openai import AsyncOpenAI                      # new import

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
        # Instantiate shared objects for embeddings and LLM:
        use_external_client = self.env_vars.get("USE_EXTERNAL_CLIENT", "False").lower() == "true"
        if use_external_client:
            self.embeddings = OllamaEmbeddings(
                model=self.env_vars.get("EXTERNAL_EMB_MODEL"),
                base_url=self.env_vars.get("EXTERNAL_BASE_URL")
            )
            self.llm_client = AsyncOpenAI(
                base_url=self.env_vars.get("EXTERNAL_BASE_URL"),
                api_key=self.env_vars.get("EXTERNAL_API_KEY")
            )
            self.model_name = self.env_vars.get("EXTERNAL_LLM_MODEL")
        else:
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            self.llm_client = AsyncOpenAI() 
            self.model_name = self.env_vars.get("OPENAI_MODEL")
        
    def get(self, key, default=None):
        """Retrieve an environment variable, with an optional default."""
        return self.env_vars.get(key, default)

# Usage
config = ConfigManager()


