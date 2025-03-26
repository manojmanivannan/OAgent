FROM python:3.11-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv && uv pip install fastapi[standard]>=0.115.11 sqlalchemy>=2.0.39

FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=base .venv /.venv
COPY . .
ENV PATH=/.venv/bin:$PATH

CMD ["fastapi","run","/app/main.py"]
