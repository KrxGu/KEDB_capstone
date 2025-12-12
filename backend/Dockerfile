FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

COPY backend/pyproject.toml ./pyproject.toml
RUN poetry install --no-root --no-interaction

COPY backend /app
