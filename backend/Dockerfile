FROM python:3.13-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r app \
    && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

COPY . .

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "uv sync --frozen --no-dev && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]