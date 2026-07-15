# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv (fast Python package manager) via the official static binary.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifest first for better layer caching.
COPY pyproject.toml ./

# Create the venv and install deps. --no-install-project skips installing
# the local package itself until the source is copied in below.
RUN uv sync --no-install-project

COPY app ./app

# Install the local project into the venv now that source is present.
RUN uv sync

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    REDIS_HOST=redis \
    REDIS_PORT=6379

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
