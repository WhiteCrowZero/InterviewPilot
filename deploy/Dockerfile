FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY src ./src
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

CMD ["uvicorn", "interview_pilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
