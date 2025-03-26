FROM python:3.11-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv && uv pip install --no-cache "langchain-chroma>=0.2.2" "langchain-community>=0.3.20" "langchain-ollama>=0.3.0" "langchain-openai>=0.3.9" "langchain-text-splitters>=0.3.7" "openai-agents>=0.0.6" "python-dotenv>=1.0.1" "requests>=2.32.3" "streamlit>=1.43.2" "unstructured>=0.17.2"

FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=base .venv /.venv
COPY . .
ENV PATH=/.venv/bin:$PATH

CMD ["streamlit","run","/app/main.py","--theme.base","light", "--server.headless","true"]