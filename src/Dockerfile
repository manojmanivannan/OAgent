FROM python:3.11-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY requirements.txt .
RUN uv venv && uv pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=base .venv /.venv
COPY . .
ENV PATH=/.venv/bin:$PATH

CMD ["streamlit","run","/app/main.py","--theme.base","light", "--server.headless","true"]