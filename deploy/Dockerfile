FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN uv add --no-cache-dir fastapi "uvicorn[standard]" pydantic-settings

CMD ["uvicorn", "interview_pilot:main:app", "--host", "0.0.0.0", "--port", "8000"]
