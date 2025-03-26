from openai import AsyncOpenAI
from agents import set_default_openai_client
from agents import OpenAIChatCompletionsModel
from pydantic import BaseModel
from config import config


class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None
    from_city: str | None = None
    to_city: str | None = None
    mcp_config_path: str = "mcp_agent.config.yaml"
    mcp_config: str = None


set_default_openai_client(config.llm_client)


model = OpenAIChatCompletionsModel(
    model=config.model_name,
    openai_client=config.llm_client,
)