from openai import AsyncOpenAI
from agents import set_default_openai_client
from agents import OpenAIChatCompletionsModel
from pydantic import BaseModel
from src.config import config


class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None
    from_city: str | None = None
    to_city: str | None = None
    mcp_config_path: str ="mcp_agent.config.yaml"
    mcp_config: str = None


# Determine whether to use external client
use_external_client = config.get("USE_EXTERNAL_CLIENT", "False").lower() == "true"

if use_external_client:
    external_client = AsyncOpenAI(
        base_url=config.get("EXTERNAL_BASE_URL"),
        api_key=config.get("EXTERNAL_API_KEY"),
    )
    model_name = config.get("EXTERNAL_MODEL")

else:
    external_client = AsyncOpenAI()  # Default OpenAI client
    model_name = config.get("OPENAI_MODEL")
    
# or external_client should default AsyncOpenAI() based on variable from .env
set_default_openai_client(external_client)


model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=external_client,
    )